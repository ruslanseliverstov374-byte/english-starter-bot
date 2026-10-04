# -*- coding: utf-8 -*-
"""Хранилище на SQLite: пользователи, прогресс, интервальное повторение (SRS), ответы."""

import json
import os
import sqlite3
import threading
from datetime import datetime, timedelta, timezone

DEFAULT_TZ_OFFSET = 180          # Москва, UTC+3
DEFAULT_REMIND_TIME = "09:00"
DEFAULT_PER_DAY = 5              # режим «10 минут в день»

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    chat_id          INTEGER PRIMARY KEY,
    username         TEXT,
    first_name       TEXT,
    created_at       TEXT,
    onboarded        INTEGER DEFAULT 0,
    mode             TEXT DEFAULT 'light',
    day              INTEGER DEFAULT 1,
    per_day          INTEGER DEFAULT 5,
    tz_offset        INTEGER DEFAULT 180,
    remind_time      TEXT DEFAULT '09:00',
    reminders_on     INTEGER DEFAULT 1,
    streak           INTEGER DEFAULT 0,
    best_streak      INTEGER DEFAULT 0,
    last_lesson_date TEXT,
    last_remind_date TEXT,
    total_lessons    INTEGER DEFAULT 0,
    total_answers    INTEGER DEFAULT 0,
    correct_answers  INTEGER DEFAULT 0,
    state            TEXT
);
CREATE TABLE IF NOT EXISTS srs (
    chat_id   INTEGER NOT NULL,
    word_key  TEXT NOT NULL,
    box       INTEGER DEFAULT 0,
    reps      INTEGER DEFAULT 0,
    lapses    INTEGER DEFAULT 0,
    due_at    TEXT,
    last_seen TEXT,
    learned   INTEGER DEFAULT 0,
    PRIMARY KEY (chat_id, word_key)
);
CREATE TABLE IF NOT EXISTS answers (
    id       INTEGER PRIMARY KEY AUTOINCREMENT,
    chat_id  INTEGER NOT NULL,
    ts       TEXT,
    word_key TEXT,
    kind     TEXT,
    correct  INTEGER
);
CREATE INDEX IF NOT EXISTS idx_answers_chat ON answers(chat_id);
CREATE INDEX IF NOT EXISTS idx_srs_due ON srs(chat_id, due_at);
CREATE TABLE IF NOT EXISTS meta (
    key   TEXT PRIMARY KEY,
    value TEXT
);
"""


def utcnow():
    return datetime.now(timezone.utc).replace(tzinfo=None)


def iso(dt):
    return dt.replace(microsecond=0).isoformat()


def parse_iso(value):
    if not value:
        return None
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        return None


def local_now(tz_offset_minutes):
    return utcnow() + timedelta(minutes=int(tz_offset_minutes or 0))


def local_date_str(tz_offset_minutes):
    return local_now(tz_offset_minutes).strftime("%Y-%m-%d")


class Store:
    def __init__(self, path):
        self.path = path
        directory = os.path.dirname(os.path.abspath(path))
        if directory:
            os.makedirs(directory, exist_ok=True)
        self.lock = threading.RLock()
        self.conn = sqlite3.connect(path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        with self.lock:
            # WAL + synchronous=NORMAL: запись без fsync на каждый коммит.
            # Для 30+ активных учеников это разница в десятки раз по скорости.
            try:
                self.conn.execute("PRAGMA journal_mode=WAL")
                self.conn.execute("PRAGMA synchronous=NORMAL")
                self.conn.execute("PRAGMA busy_timeout=5000")
                self.conn.execute("PRAGMA temp_store=MEMORY")
                self.conn.execute("PRAGMA cache_size=-8000")     # ~8 МБ кэша страниц
            except sqlite3.Error:
                pass
            self.conn.executescript(SCHEMA)
            self.conn.commit()

    # ---------- пользователи ----------

    def get_user(self, chat_id):
        with self.lock:
            row = self.conn.execute(
                "SELECT * FROM users WHERE chat_id = ?", (chat_id,)
            ).fetchone()
        return dict(row) if row else None

    def ensure_user(self, chat_id, username=None, first_name=None):
        user = self.get_user(chat_id)
        if user:
            with self.lock:
                self.conn.execute(
                    "UPDATE users SET username = COALESCE(?, username), "
                    "first_name = COALESCE(?, first_name) WHERE chat_id = ?",
                    (username, first_name, chat_id),
                )
                self.conn.commit()
            return self.get_user(chat_id)
        with self.lock:
            self.conn.execute(
                "INSERT INTO users (chat_id, username, first_name, created_at, tz_offset,"
                " remind_time, per_day) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (
                    chat_id,
                    username,
                    first_name,
                    iso(utcnow()),
                    DEFAULT_TZ_OFFSET,
                    DEFAULT_REMIND_TIME,
                    DEFAULT_PER_DAY,
                ),
            )
            self.conn.commit()
        return self.get_user(chat_id)

    def update_user(self, chat_id, **fields):
        if not fields:
            return
        keys = ", ".join("%s = ?" % k for k in fields)
        values = list(fields.values()) + [chat_id]
        with self.lock:
            self.conn.execute("UPDATE users SET %s WHERE chat_id = ?" % keys, values)
            self.conn.commit()

    def set_state(self, chat_id, state):
        self.update_user(chat_id, state=json.dumps(state, ensure_ascii=False) if state else None)

    def get_state(self, chat_id):
        user = self.get_user(chat_id)
        if not user or not user.get("state"):
            return None
        try:
            return json.loads(user["state"])
        except ValueError:
            return None

    def all_users(self):
        with self.lock:
            rows = self.conn.execute("SELECT * FROM users").fetchall()
        return [dict(r) for r in rows]

    def stats(self):
        with self.lock:
            row = self.conn.execute("SELECT COUNT(*) AS c FROM users").fetchone()
        return {"users": row["c"] if row else 0}

    # ---------- служебные значения ----------

    def get_meta(self, key, default=None):
        with self.lock:
            row = self.conn.execute("SELECT value FROM meta WHERE key = ?", (key,)).fetchone()
        return row["value"] if row else default

    def set_meta(self, key, value):
        with self.lock:
            self.conn.execute(
                "INSERT INTO meta (key, value) VALUES (?, ?)"
                " ON CONFLICT(key) DO UPDATE SET value = excluded.value",
                (key, str(value)),
            )
            self.conn.commit()

    def snapshot(self, destination):
        """Согласованная копия базы (безопасно делать на работающем боте)."""
        with self.lock:
            target = sqlite3.connect(destination)
            try:
                with target:
                    self.conn.backup(target)
            finally:
                target.close()
        return destination

    def close(self):
        with self.lock:
            try:
                self.conn.close()
            except Exception:
                pass

    # ---------- SRS ----------

    def srs_row(self, chat_id, word_key):
        with self.lock:
            row = self.conn.execute(
                "SELECT * FROM srs WHERE chat_id = ? AND word_key = ?", (chat_id, word_key)
            ).fetchone()
        return dict(row) if row else None

    def upsert_srs(self, chat_id, word_key, **fields):
        row = self.srs_row(chat_id, word_key)
        if row is None:
            with self.lock:
                self.conn.execute(
                    "INSERT INTO srs (chat_id, word_key, box, reps, lapses, due_at, last_seen, learned)"
                    " VALUES (?, ?, 0, 0, 0, ?, ?, 0)",
                    (chat_id, word_key, iso(utcnow()), iso(utcnow())),
                )
                self.conn.commit()
            row = self.srs_row(chat_id, word_key)
        if fields:
            keys = ", ".join("%s = ?" % k for k in fields)
            values = list(fields.values()) + [chat_id, word_key]
            with self.lock:
                self.conn.execute(
                    "UPDATE srs SET %s WHERE chat_id = ? AND word_key = ?" % keys, values
                )
                self.conn.commit()
        return self.srs_row(chat_id, word_key)

    def due_words(self, chat_id, limit=10):
        now = iso(utcnow())
        with self.lock:
            rows = self.conn.execute(
                "SELECT word_key FROM srs WHERE chat_id = ? AND learned = 1 AND due_at <= ?"
                " ORDER BY due_at LIMIT ?",
                (chat_id, now, limit),
            ).fetchall()
        return [r["word_key"] for r in rows]

    def weakest_words(self, chat_id, limit=10, exclude=()):
        placeholders = ",".join("?" for _ in exclude) if exclude else None
        sql = "SELECT word_key FROM srs WHERE chat_id = ? AND learned = 1"
        params = [chat_id]
        if placeholders:
            sql += " AND word_key NOT IN (%s)" % placeholders
            params.extend(exclude)
        sql += " ORDER BY box ASC, lapses DESC, RANDOM() LIMIT ?"
        params.append(limit)
        with self.lock:
            rows = self.conn.execute(sql, params).fetchall()
        return [r["word_key"] for r in rows]

    def srs_map(self, chat_id):
        """Все записи повторения пользователя: word_key -> строка."""
        with self.lock:
            rows = self.conn.execute("SELECT * FROM srs WHERE chat_id = ?", (chat_id,)).fetchall()
        return {r["word_key"]: dict(r) for r in rows}

    def drill_stats(self, chat_id):
        """Статистика тренажёра конструкций: card_id -> {total, correct}."""
        with self.lock:
            rows = self.conn.execute(
                "SELECT word_key, COUNT(*) AS total, SUM(correct) AS correct FROM answers"
                " WHERE chat_id = ? AND word_key LIKE 'g:%' GROUP BY word_key",
                (chat_id,),
            ).fetchall()
        return {
            r["word_key"][2:]: {"total": r["total"] or 0, "correct": r["correct"] or 0}
            for r in rows
        }

    def srs_counts(self, chat_id):
        with self.lock:
            rows = self.conn.execute(
                "SELECT box, COUNT(*) AS c FROM srs WHERE chat_id = ? AND learned = 1 GROUP BY box",
                (chat_id,),
            ).fetchall()
            due = self.conn.execute(
                "SELECT COUNT(*) AS c FROM srs WHERE chat_id = ? AND learned = 1 AND due_at <= ?",
                (chat_id, iso(utcnow())),
            ).fetchone()
        by_box = {r["box"]: r["c"] for r in rows}
        total = sum(by_box.values())
        strong = sum(c for b, c in by_box.items() if b >= 4)
        return {"total": total, "due": due["c"] if due else 0, "strong": strong, "by_box": by_box}

    # ---------- ответы и стрики ----------

    def log_answer(self, chat_id, word_key, kind, correct):
        with self.lock:
            self.conn.execute(
                "INSERT INTO answers (chat_id, ts, word_key, kind, correct) VALUES (?, ?, ?, ?, ?)",
                (chat_id, iso(utcnow()), word_key, kind, 1 if correct else 0),
            )
            self.conn.execute(
                "UPDATE users SET total_answers = total_answers + 1,"
                " correct_answers = correct_answers + ? WHERE chat_id = ?",
                (1 if correct else 0, chat_id),
            )
            self.conn.commit()

    def finish_lesson(self, chat_id):
        user = self.get_user(chat_id)
        if not user:
            return {}
        tz = user["tz_offset"]
        today = local_date_str(tz)
        yesterday = (local_now(tz) - timedelta(days=1)).strftime("%Y-%m-%d")
        if user["last_lesson_date"] == today:
            streak = user["streak"]
        elif user["last_lesson_date"] == yesterday:
            streak = user["streak"] + 1
        else:
            streak = 1
        best = max(streak, user["best_streak"] or 0)
        self.update_user(
            chat_id,
            streak=streak,
            best_streak=best,
            last_lesson_date=today,
            total_lessons=(user["total_lessons"] or 0) + 1,
        )
        return {"streak": streak, "best": best, "date": today}

    def lesson_done_today(self, chat_id):
        user = self.get_user(chat_id)
        if not user:
            return False
        return user["last_lesson_date"] == local_date_str(user["tz_offset"])

    def week_accuracy(self, chat_id, days=7):
        since = iso(utcnow() - timedelta(days=days))
        with self.lock:
            row = self.conn.execute(
                "SELECT COUNT(*) AS total, SUM(correct) AS correct FROM answers"
                " WHERE chat_id = ? AND ts >= ?",
                (chat_id, since),
            ).fetchone()
        total = row["total"] or 0
        correct = row["correct"] or 0
        return {"total": total, "correct": correct,
                "percent": round(100.0 * correct / total) if total else 0}

    def difficulty(self, chat_id, word_keys):
        """Сколько раз слово было отвечено неверно (для подсказок в уроке)."""
        if not word_keys:
            return {}
        placeholders = ",".join("?" for _ in word_keys)
        with self.lock:
            rows = self.conn.execute(
                "SELECT word_key, SUM(1 - correct) AS wrongs FROM answers"
                " WHERE chat_id = ? AND word_key IN (%s) GROUP BY word_key" % placeholders,
                [chat_id] + list(word_keys),
            ).fetchall()
        return {r["word_key"]: r["wrongs"] or 0 for r in rows}
