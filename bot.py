#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""English Starter — Telegram-бот для изучения английского с нуля.

Запуск:
    python bot.py                 # берёт токен из token.txt или переменной BOT_TOKEN
    python bot.py --token 123:ABC # токен в командной строке
    python bot.py --check         # проверить контент курса и выйти

Режимы работы:
    long polling (по умолчанию) — для домашнего компьютера, интернет только исходящий;
    webhook (--webhook-url https://... ) — для облака 24/7.
"""

import argparse
import atexit
import hashlib
import json
import os
import random
import shutil
import sys
import threading
import time
import traceback
from datetime import datetime, timedelta

import course
import texts
from content import (
    DIALOGUE_BY_ID,
    GRAMMAR,
    GRAMMAR_BY_ID,
    STATS,
    TOPIC_BY_ID,
    TOTAL_DAYS,
    WORD_BY_KEY,
    validate,
)
from instance_lock import InstanceLock
from remote_store import (
    RemoteSnapshot,
    SnapshotUploader,
    TelegramSnapshot,
    build_snapshot_provider,
    restore_if_needed,
)
from store import Store, iso, local_date_str, local_now, utcnow
from tgbot import Telegram, TgError, btn, inline, reply_keyboard, url_btn

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_DIR = os.path.join(BASE_DIR, "logs")
DATA_DIR = os.path.join(BASE_DIR, "data")
DB_DEFAULT = os.path.join(DATA_DIR, "bot.db")
LOCK_PATH = os.path.join(DATA_DIR, "bot.lock")
PID_PATH = os.path.join(DATA_DIR, "bot.pid")
HEARTBEAT_PATH = os.path.join(DATA_DIR, "heartbeat")
CONFLICT_FLAG = os.path.join(DATA_DIR, "conflict.flag")
TOKEN_FILE = os.path.join(BASE_DIR, "token.txt")
ENV_FILE = os.path.join(BASE_DIR, ".env")

TZ_CHOICES = [
    ("Калининград (UTC+2)", 120),
    ("Москва (UTC+3)", 180),
    ("Самара (UTC+4)", 240),
    ("Екатеринбург (UTC+5)", 300),
    ("Омск (UTC+6)", 360),
    ("Красноярск (UTC+7)", 420),
    ("Иркутск (UTC+8)", 480),
    ("Владивосток (UTC+10)", 600),
]

TIME_CHOICES = ["07:00", "09:00", "12:00", "18:00", "20:00", "22:00"]

MODE_BY_BUTTON = {
    # режим -> (название, сколько карточек повторения и упражнений в уроке)
    "light": ("light", 5),
    "standard": ("standard", 10),
    "intensive": ("intensive", 15),
}

COMMANDS = [
    {"command": "today", "description": "▶️ Урок дня"},
    {"command": "newwords", "description": "🆕 Практика новых слов"},
    {"command": "constructions", "description": "🧩 Тренажёр конструкций"},
    {"command": "practice", "description": "✍️ Смешанная практика"},
    {"command": "dictionary", "description": "📖 Словарь выученных слов"},
    {"command": "review", "description": "🔁 Повторение слов"},
    {"command": "quiz", "description": "🎲 Быстрый тест"},
    {"command": "progress", "description": "📊 Мой прогресс"},
    {"command": "backup", "description": "🗄 Резервная копия прогресса"},
    {"command": "program", "description": "📚 Программа курса"},
    {"command": "words", "description": "📚 Слова по темам"},
    {"command": "word", "description": "🔍 Карточка слова: /word hello"},
    {"command": "grammar", "description": "📘 Грамматика"},
    {"command": "settings", "description": "⚙️ Настройки"},
    {"command": "help", "description": "❓ Помощь"},
    {"command": "stop", "description": "🔕 Выключить напоминания"},
]


def log(message):
    line = "[%s] %s" % (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), message)
    try:
        print(line)
    except Exception:
        pass
    try:
        os.makedirs(LOG_DIR, exist_ok=True)
        # utf-8-sig: файл лога читается в Блокноте и PowerShell без «кракозябр»
        with open(os.path.join(LOG_DIR, "bot.log"), "a", encoding="utf-8-sig") as handle:
            handle.write(line + "\n")
    except Exception:
        pass


def read_env_file(path):
    values = {}
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as handle:
            for raw in handle:
                line = raw.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, value = line.split("=", 1)
                values[key.strip()] = value.strip().strip('"').strip("'")
    return values


def resolve_token(cli_token=None):
    if cli_token:
        return cli_token.strip()
    env = os.environ.get("BOT_TOKEN") or os.environ.get("TELEGRAM_BOT_TOKEN")
    if env:
        return env.strip()
    values = read_env_file(ENV_FILE)
    if values.get("BOT_TOKEN"):
        return values["BOT_TOKEN"]
    if os.path.exists(TOKEN_FILE):
        with open(TOKEN_FILE, "r", encoding="utf-8") as handle:
            for raw in handle:
                line = raw.strip()
                if line and not line.startswith("#"):
                    return line
    return None


class Bot:
    def __init__(self, token, db_path=DB_DEFAULT, api_base=None, remote=None):
        self.tg = Telegram(token, api_base=api_base) if api_base else Telegram(token)
        self.store = Store(db_path)
        self.rng = random.Random()
        self.offset = None
        self.me = None
        self.reminder_thread = None
        self.stopping = False
        self.started_at = utcnow()
        self.pinned_checked = set()      # какие чаты уже проверяли на закреплённую копию
        # Хранилище снимков базы: внешний key-value либо закреплённый файл в Telegram.
        self.remote = remote if remote is not None else build_snapshot_provider(self.tg, log=log)
        if isinstance(self.remote, TelegramSnapshot) and not self.remote.chat_id:
            self.remote.chat_id_provider = self.admin_chat_id
        interval = os.environ.get("SNAPSHOT_INTERVAL")
        if not interval:
            interval = "1800" if isinstance(self.remote, TelegramSnapshot) else "600"
        self.uploader = SnapshotUploader(self.store, self.remote, interval=int(interval), log=log)

    # ------------------------------------------------------------------
    # низкий уровень
    # ------------------------------------------------------------------

    def send(self, chat_id, text, keyboard=None):
        try:
            return self.tg.send_message(chat_id, text, reply_markup=keyboard)
        except TgError as err:
            log("sendMessage failed for %s: %s" % (chat_id, err))
            return None

    def edit(self, chat_id, message_id, text, keyboard=None):
        try:
            return self.tg.edit_message(chat_id, message_id, text, reply_markup=keyboard)
        except TgError as err:
            if "not modified" in str(err).lower():
                return None
            log("editMessage failed for %s: %s" % (chat_id, err))
            return None

    def typing(self, chat_id):
        try:
            self.tg.send_chat_action(chat_id, "typing")
        except Exception:
            pass

    # ------------------------------------------------------------------
    # состояние пользователя
    # ------------------------------------------------------------------

    def state(self, chat_id):
        return self.store.get_state(chat_id) or {}

    def save_state(self, chat_id, state):
        self.store.set_state(chat_id, state if state else None)

    def session(self, chat_id):
        return self.state(chat_id).get("session")

    # ------------------------------------------------------------------
    # маршрутизация
    # ------------------------------------------------------------------

    def handle_update(self, update):
        if "message" in update:
            message = update["message"]
            log("message %s: %s" % (
                message.get("chat", {}).get("id"),
                (message.get("text") or "<не текст>").replace("\n", " ")[:70],
            ))
            self.handle_message(message)
        elif "callback_query" in update:
            query = update["callback_query"]
            log("button %s: %s" % (
                query.get("message", {}).get("chat", {}).get("id"),
                (query.get("data") or "")[:40],
            ))
            self.handle_callback(query)

    def handle_message(self, message):
        chat = message.get("chat", {})
        chat_id = chat.get("id")
        if chat_id is None:
            return
        if chat.get("type") != "private":
            self.send(chat_id, "Я работаю только в личных сообщениях. Напишите мне в личку 🙂")
            return
        self.store.ensure_user(
            chat_id,
            message.get("from", {}).get("username"),
            message.get("from", {}).get("first_name"),
        )
        if self.maybe_restore_from_pinned(chat_id):
            self.send(chat_id, "\n".join([
                "♻️ <b>Прогресс восстановлен</b>",
                "",
                "Бот перезапустился на бесплатном хостинге и поднял вашу базу "
                "из закреплённой копии в этом чате.",
                "Продолжаем с того же дня — посмотрите /progress.",
            ]), texts.MAIN_MENU)
        if message.get("document"):
            self.restore_from_document(chat_id, message["document"])
            return
        text = (message.get("text") or "").strip()
        if not text:
            self.send(chat_id, "Я понимаю текст и кнопки. Нажмите /today, чтобы продолжить 🙂",
                      texts.MAIN_MENU)
            return

        if text.startswith("/"):
            command = text.split()[0].lstrip("/").split("@")[0].lower()
            argument = text[len(text.split()[0]):].strip()
            self.handle_command(chat_id, command, argument)
            return

        state = self.state(chat_id)
        pending = state.get("pending")

        if pending == "set_time":
            parsed = self.parse_time(text)
            if parsed:
                state["pending"] = None
                if (state.get("tmp") or {}).get("mode"):
                    # это шаг онбординга: продолжаем настройку
                    state["tmp"]["time"] = parsed
                    state["pending"] = "onb_tz"
                    self.store.update_user(chat_id, remind_time=parsed, reminders_on=1)
                    self.save_state(chat_id, state)
                    self.send(chat_id, "⏰ Время напоминания: <b>%s</b>" % parsed)
                    self.send_start_step(chat_id)
                    return
                self.store.update_user(chat_id, remind_time=parsed, reminders_on=1)
                self.save_state(chat_id, state)
                user = self.store.get_user(chat_id)
                self.send(chat_id, "⏰ Готово! Напоминание в <b>%s</b>." % user["remind_time"],
                          texts.settings_keyboard(user))
            else:
                self.send(chat_id, "Не понял время. Напишите в формате <b>09:00</b>.")
            return

        if pending == "set_day":
            if text.isdigit() and 1 <= int(text) <= TOTAL_DAYS:
                day = int(text)
                self.store.update_user(chat_id, day=day, state=None)
                user = self.store.get_user(chat_id)
                plan = course.plan_for_day(day, user["per_day"])
                self.send(chat_id, "📅 Переключил на день <b>%d</b>: «%s»." % (
                    day, plan["week_title"]), texts.lesson_keyboard())
            else:
                self.send(chat_id, "Введите число от 1 до %d." % TOTAL_DAYS)
            return

        session = state.get("session")
        if session and session.get("await"):
            self.grade_typed(chat_id, text)
            return

        # кнопки главного меню
        menu_map = {
            "▶️ урок дня": "today",
            "🆕 новые слова": "newwords",
            "🧩 конструкции": "constructions",
            "✍️ практика": "practice",
            "📖 словарь": "dictionary",
            "📊 прогресс": "progress",
            "📚 программа": "program",
            "⚙️ настройки": "settings",
            "🔁 повторение": "review",
            "❓ помощь": "help",
        }
        if text.lower() in menu_map:
            self.handle_command(chat_id, menu_map[text.lower()], "")
            return

        self.send(
            chat_id,
            "Не понял сообщение. Нажмите <b>▶️ Урок дня</b> или посмотрите /help.",
            texts.MAIN_MENU,
        )

    def parse_time(self, text):
        try:
            hours, minutes = text.strip().split(":")
            hours, minutes = int(hours), int(minutes)
            if 0 <= hours <= 23 and 0 <= minutes <= 59:
                return "%02d:%02d" % (hours, minutes)
        except Exception:
            return None
        return None

    # ------------------------------------------------------------------
    # команды
    # ------------------------------------------------------------------

    def handle_command(self, chat_id, command, argument=""):
        user = self.store.get_user(chat_id)
        handlers = {
            "start": self.cmd_start,
            "today": self.cmd_today,
            "lesson": self.cmd_today,
            "review": self.cmd_review,
            "newwords": self.cmd_newwords,
            "constructions": self.cmd_constructions,
            "drills": self.cmd_constructions,
            "practice": self.cmd_practice,
            "dictionary": self.cmd_dictionary,
            "dict": self.cmd_dictionary,
            "quiz": self.cmd_quiz,
            "progress": self.cmd_progress,
            "program": self.cmd_program,
            "words": self.cmd_words,
            "word": self.cmd_word,
            "grammar": self.cmd_grammar,
            "settings": self.cmd_settings,
            "help": self.cmd_help,
            "stop": self.cmd_stop,
            "nextday": self.cmd_next_day,
            "backup": self.cmd_backup,
            "restore": self.cmd_backup,
        }
        handler = handlers.get(command)
        if not handler:
            self.send(chat_id, "Не знаю такой команды. /help — список.", texts.MAIN_MENU)
            return
        if command == "word":
            handler(chat_id, user, argument)
        else:
            handler(chat_id, user)

    def cmd_start(self, chat_id, user):
        if user and user["onboarded"]:
            session = self.session(chat_id)
            if session:
                self.send(chat_id, "Продолжаем занятие 👇")
                self.send_step(chat_id)
                return
            self.send(
                chat_id,
                "С возвращением! 👋\n\nВы на дне <b>%d</b> из %d. Начнём урок?" % (
                    user["day"], TOTAL_DAYS),
                texts.lesson_keyboard(),
            )
            return

        current = self.state(chat_id)
        if (current.get("pending") or "").startswith("onb"):
            self.send_start_step(chat_id)
            return

        self.store.update_user(chat_id, state=json.dumps({"pending": "onb_mode"}))
        self.send(
            chat_id,
            "\n".join([
                "🇬🇧 <b>English Starter</b>",
                "",
                "Привет! Я бот, который научит вас английскому с нуля:",
                "• %d слов и %d грамматических тем" % (STATS["words"], STATS["grammar"]),
                "• 12 недель, 84 занятия по 10 минут",
                "• умное повторение: слова возвращаются ровно тогда, когда вы готовы их забыть",
                "• днём курса можно управлять, курс не сгорает при пропусках",
                "",
                "Сначала два вопроса. Какой режим занятий вам подходит?",
            ]),
            inline([
                [btn("🌱 10 минут в день (рекомендую)", "onb|mode|light")],
                [btn("🌿 20 минут в день", "onb|mode|standard")],
                [btn("🌳 40 минут в день", "onb|mode|intensive")],
            ]),
        )

    def cmd_today(self, chat_id, user):
        session = self.session(chat_id)
        if session:
            self.send(chat_id, "Занятие уже идёт — продолжаем 👇")
            self.send_step(chat_id)
            return
        if self.store.lesson_done_today(chat_id):
            self.send(
                chat_id,
                "Сегодняшний урок уже пройден ✅\n\nМожно повторить слова или перейти к следующему дню.",
                inline([
                    [btn("🔁 Повторить слова", "go|review")],
                    [btn("➡️ Следующий день (%d)" % min(user["day"] + 1, TOTAL_DAYS), "go|next_day")],
                    [btn("📊 Прогресс", "go|progress")],
                ]),
            )
            return
        self.start_session(chat_id, "lesson")

    def cmd_review(self, chat_id, user):
        self.start_session(chat_id, "review")

    def cmd_quiz(self, chat_id, user):
        if self.session(chat_id):
            self.send(chat_id, "Сначала завершим текущее занятие 🙂", texts.MAIN_MENU)
            self.send_step(chat_id)
            return
        questions = course.build_quiz_questions(self.store, chat_id, self.rng, count=10)
        if not questions:
            self.send(chat_id, "Пока нечего тестировать — сначала пройдите первый урок!",
                      texts.lesson_keyboard())
            return
        state = self.state(chat_id)
        state["session"] = {
            "kind": "quiz",
            "steps": ["ex", "done"],
            "si": 0,
            "questions": questions,
            "qi": 0,
            "phase": "question",
            "await": False,
            "correct": 0,
            "total": 0,
        }
        self.save_state(chat_id, state)
        self.send(chat_id, "🎲 <b>Быстрый тест: 10 вопросов</b> по пройденным словам. Поехали!")
        self.send_step(chat_id)

    def cmd_progress(self, chat_id, user):
        self.send(chat_id, texts.progress_text(self.store, user), texts.MAIN_MENU)

    # ---------- тренажёры и словарь ----------

    def start_training(self, chat_id, kind, questions, header, day=None):
        """Общий запуск тренажёра: практика новых слов, конструкции, микс."""
        if self.session(chat_id):
            self.send(chat_id, "Сначала завершим текущее занятие 🙂")
            self.send_step(chat_id)
            return
        if not questions:
            self.send(chat_id,
                      "Материала пока нет — сначала пройдите урок дня, и тренажёр наполнится.",
                      texts.lesson_keyboard())
            return
        user = self.store.get_user(chat_id)
        state = self.state(chat_id)
        state["pending"] = None
        state["session"] = {
            "kind": kind,
            "day": day or course.clamp_day(user["day"]),
            "si": 0,
            "cards": [],
            "new": [],
            "ci": 0,
            "shown": False,
            "correct": 0,
            "total": 0,
            "await": False,
            "qi": 0,
            "phase": "question",
            "questions": questions,
            "grammar": None,
            "dialogue": None,
            "is_review_day": False,
            "plan": None,
            "steps": ["ex", "done"],
            "drill_cards": sorted({q["grammar_id"] for q in questions if q.get("grammar_id")}),
        }
        self.save_state(chat_id, state)
        self.send(chat_id, header, texts.MAIN_MENU)
        self.send_step(chat_id)

    def cmd_newwords(self, chat_id, user):
        _, volume = course.practice_settings(user)
        day = course.clamp_day(user["day"])
        words = course.recent_new_words(day, limit=max(volume * 2, 10))
        if not words:
            self.send(chat_id,
                      "Пока закреплять нечего: новых слов ещё не было.\n"
                      "Пройдите урок дня — и сюда добавятся слова последних уроков.",
                      texts.lesson_keyboard())
            return
        if self.session(chat_id):
            self.send(chat_id, "Сначала завершим текущее занятие 🙂")
            self.send_step(chat_id)
            return
        questions = course.build_new_words_questions(self.store, chat_id, day, self.rng, count=volume)
        self.start_training(chat_id, "new_words", questions,
                            texts.new_words_intro(len(words), len(questions)), day=day)

    def cmd_constructions(self, chat_id, user):
        text, keyboard = texts.constructions_home(self.store, user)
        self.send(chat_id, text, keyboard)

    def cmd_practice(self, chat_id, user):
        _, volume = course.practice_settings(user)
        day = course.clamp_day(user["day"])
        if self.session(chat_id):
            self.send(chat_id, "Сначала завершим текущее занятие 🙂")
            self.send_step(chat_id)
            return
        questions = course.build_mixed_questions(self.store, user, self.rng, count=volume)
        header = texts.trainer_intro(
            "mixed", "СМЕШАННАЯ ПРАКТИКА", len(questions),
            "Слова последних уроков + конструкции + диалог недели",
            "<i>Если что-то забыли — это нормально: ошибка вернёт слово в повторение.</i>",
        )
        self.start_training(chat_id, "mixed", questions, header, day=day)

    def cmd_dictionary(self, chat_id, user):
        text, keyboard = texts.dictionary_home(self.store, user)
        self.send(chat_id, text, keyboard)

    # ---------- резервные копии и восстановление ----------

    def admin_chat_id(self):
        """Владелец бота: ADMIN_CHAT_ID, иначе - самый первый ученик."""
        from_env = (os.environ.get("ADMIN_CHAT_ID") or "").strip()
        if from_env.lstrip("-").isdigit():
            return int(from_env)
        saved = self.store.get_meta("admin_chat_id")
        if saved and str(saved).lstrip("-").isdigit():
            return int(saved)
        users = self.store.all_users()
        if not users:
            return None
        first = min(users, key=lambda item: item.get("created_at") or "")
        self.store.set_meta("admin_chat_id", first["chat_id"])
        return first["chat_id"]

    def cmd_backup(self, chat_id, user):
        if chat_id != self.admin_chat_id():
            self.send(chat_id, "Резервную копию может запросить только владелец бота.")
            return
        self.send_backup(chat_id, reason="Копия по запросу (команда /backup)")

    def send_backup(self, chat_id, reason="", silent=False):
        """Отправляет согласованную копию базы в чат владельца."""
        temp_path = os.path.join(DATA_DIR, "backup-snapshot.db")
        try:
            os.makedirs(DATA_DIR, exist_ok=True)
            self.store.snapshot(temp_path)
            size_kb = round(os.path.getsize(temp_path) / 1024.0, 1)
            self.tg.send_document(
                chat_id,
                temp_path,
                caption=("\n".join([
                    "🗄 <b>Резервная копия прогресса</b>",
                    reason,
                    "Размер: %s КБ" % size_kb,
                    "",
                    "<i>Чтобы восстановить прогресс, отправьте этот файл боту "
                    "(или перешлите его из «Избранного»).</i>",
                ])),
                filename="english-starter-backup.db",
            )
            self.store.set_meta("last_backup_at", iso(utcnow()))
            if not silent:
                self.send(chat_id, "✅ Копия выше. Совет: перешлите её себе в «Избранное».")
            log("резервная копия отправлена в %s (%s КБ)" % (chat_id, size_kb))
            return True
        except Exception as err:
            log("не удалось отправить резервную копию: %s" % err)
            if not silent:
                self.send(chat_id, "Не удалось отправить копию: %s" % err)
            return False
        finally:
            if os.path.exists(temp_path):
                try:
                    os.remove(temp_path)
                except OSError:
                    pass

    def maybe_auto_backup(self):
        """Раз в 2 дня отправляет владельцу свежую копию базы."""
        if (os.environ.get("AUTO_BACKUP") or "1").strip() == "0":
            return
        admin = self.admin_chat_id()
        if not admin:
            return
        last = self.store.get_meta("last_backup_at")
        due = True
        if last:
            try:
                from datetime import datetime as dt
                due = (utcnow() - dt.fromisoformat(last)) > timedelta(days=2)
            except Exception:
                due = True
        if due:
            self.send_backup(admin, reason="Автоматическая копия (раз в 2 дня)", silent=True)

    def restore_from_document(self, chat_id, document):
        """Восстанавливает базу из файла, присланного владельцем."""
        if chat_id != self.admin_chat_id():
            self.send(chat_id, "Восстановить базу может только владелец бота.")
            return
        name = (document.get("file_name") or "").lower()
        if not name.endswith(".db"):
            self.send(chat_id, "Пришлите файл резервной копии (имя заканчивается на .db).")
            return
        temp_path = os.path.join(DATA_DIR, "restore-upload.db")
        try:
            os.makedirs(DATA_DIR, exist_ok=True)
            _, size = self.tg.download_file(document["file_id"], temp_path)
            with open(temp_path, "rb") as handle:
                header = handle.read(16)
            if not header.startswith(b"SQLite format 3"):
                self.send(chat_id, "Это не похоже на базу бота — файл отменён.")
                return

            db_path = self.store.path
            safety = db_path + ".before-restore"
            self.store.close()
            if os.path.exists(db_path):
                shutil.copy2(db_path, safety)
            shutil.copy2(temp_path, db_path)
            self.store = Store(db_path)
            users = len(self.store.all_users())
            learned = self.store.srs_counts(self.admin_chat_id() or 0)["total"]
            self.send(chat_id, "\n".join([
                "✅ <b>Прогресс восстановлен</b>",
                "Файл: %s (%s КБ)" % (texts.esc(name), round(size / 1024.0, 1)),
                "Учеников в базе: <b>%d</b>, слов в повторении у вас: <b>%d</b>" % (users, learned),
                "",
                "Прежняя база сохранена рядом как <code>bot.db.before-restore</code>.",
                "Нажмите /progress, чтобы проверить.",
            ]))
            log("база восстановлена из файла %s (%d байт)" % (name, size))
        except Exception as err:
            log("ошибка восстановления: %s" % traceback.format_exc())
            self.send(chat_id, "Не получилось восстановить базу: %s" % err)
        finally:
            if os.path.exists(temp_path):
                try:
                    os.remove(temp_path)
                except OSError:
                    pass

    def cmd_program(self, chat_id, user):
        self.send(chat_id, texts.program_text(user["day"]), texts.MAIN_MENU)

    def cmd_words(self, chat_id, user):
        text, keyboard = texts.words_text(self.store, user)
        self.send(chat_id, text, keyboard)

    def cmd_word(self, chat_id, user, argument):
        if not argument:
            self.send(chat_id, "Напишите слово: <code>/word hello</code>")
            return
        text = texts.word_card_text(self.store, user, argument)
        if not text:
            self.send(chat_id, "В курсе нет слова «%s». Посмотрите /words." % argument)
            return
        key = argument.strip().lower()
        word = WORD_BY_KEY.get(key)
        keyboard = inline([[url_btn("🔊 Произношение", texts.pronunciation_url(word))]]) if word else None
        self.send(chat_id, text, keyboard)

    def cmd_grammar(self, chat_id, user):
        text, keyboard = texts.grammar_index_text()
        self.send(chat_id, text, keyboard)

    def cmd_settings(self, chat_id, user):
        self.send(chat_id, texts.settings_text(user), texts.settings_keyboard(user))

    def cmd_help(self, chat_id, user):
        self.send(chat_id, texts.help_text(user), texts.MAIN_MENU)

    def cmd_stop(self, chat_id, user):
        self.store.update_user(chat_id, reminders_on=0)
        user = self.store.get_user(chat_id)
        self.send(chat_id, "🔕 Напоминания выключены. Включить снова — /settings.",
                  texts.MAIN_MENU)

    def cmd_next_day(self, chat_id, user):
        new_day = min(user["day"] + 1, TOTAL_DAYS)
        self.store.update_user(chat_id, day=new_day, state=None)
        user = self.store.get_user(chat_id)
        plan = course.plan_for_day(new_day, user["per_day"])
        self.send(chat_id, "➡️ День <b>%d</b>: неделя %d «%s».\n🎯 %s" % (
            new_day, plan["week"], plan["week_title"], plan["focus"]),
            texts.lesson_keyboard())

    # ------------------------------------------------------------------
    # онбординг
    # ------------------------------------------------------------------

    def send_start_step(self, chat_id):
        state = self.state(chat_id)
        pending = state.get("pending")
        tmp = state.setdefault("tmp", {})
        if pending == "onb_time":
            rows = [[btn("⏰ %s" % t, "onb|time|%s" % t) for t in TIME_CHOICES[:3]],
                    [btn("⏰ %s" % t, "onb|time|%s" % t) for t in TIME_CHOICES[3:]],
                    [btn("✏️ Другое время", "onb|time|custom")]]
            self.send(chat_id, "Во сколько напоминать о занятии?", inline(rows))
        elif pending == "onb_tz":
            rows = [[btn(name, "onb|tz|%d" % offset)] for name, offset in TZ_CHOICES[:4]]
            rows += [[btn(name, "onb|tz|%d" % offset)] for name, offset in TZ_CHOICES[4:]]
            self.send(chat_id, "Ваш часовой пояс? (по нему считаются дни и напоминания)",
                      inline(rows))
        elif pending == "onb_finish":
            self.send(
                chat_id,
                "\n".join([
                    "Готово! 🎉",
                    "",
                    "Режим: <b>%s</b>" % texts.MODE_TITLES.get(tmp.get("mode", "light")),
                    "Напоминание: <b>%s</b>, часовой пояс UTC%+d" % (
                        tmp.get("time", "09:00"), int(tmp.get("tz", 180)) // 60),
                    "",
                    "Первое занятие: день 1 — «%s»." % course.plan_for_day(1)["week_title"],
                    "Это 10 минут. Удачи!",
                ]),
                inline([[btn("▶️ Начать первый урок", "go|lesson")]]),
            )

    def onb_advance(self, chat_id, state):
        tmp = state.setdefault("tmp", {})
        pending = state.get("pending")
        if pending == "onb_mode":
            state["pending"] = "onb_time"
        elif pending == "onb_time":
            state["pending"] = "onb_tz"
        elif pending == "onb_tz":
            state["pending"] = "onb_finish"
        self.save_state(chat_id, state)
        self.send_start_step(chat_id)

    # ------------------------------------------------------------------
    # занятия
    # ------------------------------------------------------------------

    def start_session(self, chat_id, kind):
        user = self.store.get_user(chat_id)
        day = course.clamp_day(user["day"])
        plan = course.plan_for_day(day)
        review_target, _ = course.practice_settings(user)
        heavy = kind == "review" or plan["is_review"]
        cards = course.build_review_queue(
            self.store, chat_id, max(review_target, 12) if heavy else review_target)

        if kind == "review" and not cards:
            self.send(chat_id, "Повторять пока нечего — сначала пройдите урок дня!",
                      texts.lesson_keyboard())
            return

        state = self.state(chat_id)
        session = {
            "kind": kind,
            "day": day,
            "si": 0,
            "cards": cards,
            "ci": 0,
            "shown": False,
            "correct": 0,
            "total": 0,
            "await": False,
            "qi": 0,
            "phase": "question",
            "questions": None,
            "grammar": None,
            "dialogue": None,
            "is_review_day": False,
            "plan": None,
        }

        if kind == "lesson":
            session["is_review_day"] = plan["is_review"]
            session["new"] = [w["key"] for w in plan["new_words"]]
            session["grammar"] = plan["grammar"]["id"] if plan.get("grammar") else None
            session["dialogue"] = plan["dialogue"]["id"] if plan.get("dialogue") else None
            session["plan"] = {
                "day": plan["day"],
                "week": plan["week"],
                "week_title": plan["week_title"],
                "focus": plan["focus"],
                "is_review": plan["is_review"],
                "grammar_title": plan["grammar"]["title"] if plan.get("grammar") else None,
                "dialogue_title": plan["dialogue"]["title"] if plan.get("dialogue") else None,
            }
            if plan["is_review"]:
                steps = ["review"]
                if plan.get("grammar"):
                    steps.append("grammar")
                steps += ["test"]
                if plan.get("dialogue"):
                    steps.append("dialogue")
                steps.append("done")
                session["steps"] = steps
            else:
                steps = ["review", "new", "grammar", "ex"]
                if plan.get("dialogue"):
                    steps.append("dialogue")
                steps.append("done")
                session["steps"] = steps
        else:
            session["new"] = []
            session["steps"] = ["review", "done"]

        state["session"] = session
        state["pending"] = None
        self.save_state(chat_id, state)

        header = None
        if kind == "lesson":
            header = texts.lesson_intro(
                plan, day, user, len(cards), len(session["new"])
            )
        elif kind == "review":
            header = "🔁 <b>Повторение</b>\n\nСлов в очереди: <b>%d</b>. Это 5–10 минут." % len(cards)
        if header:
            self.send(chat_id, header, texts.MAIN_MENU)
        self.send_step(chat_id)

    def send_step(self, chat_id):
        state = self.state(chat_id)
        session = state.get("session")
        if not session:
            self.send(chat_id, "Занятие не найдено. Начнём заново?", texts.lesson_keyboard())
            return
        steps = session["steps"]
        si = session.get("si", 0)
        if si >= len(steps):
            self.finish_session(chat_id)
            return
        step = steps[si]
        user = self.store.get_user(chat_id)

        if step in ("review", "new"):
            keys = session["cards"] if step == "review" else session.get("new", [])
            session["current"] = keys
            session["ci"] = session.get("ci", 0)
            self.save_state(chat_id, state)
            self.send_card(chat_id, step)
            return

        if step == "grammar":
            card = GRAMMAR_BY_ID.get(session.get("grammar"))
            if not card:
                self.advance_step(chat_id)
                return
            self.send(chat_id, texts.grammar_card(card),
                      inline([[btn("✅ Понятно, дальше", "s|next|%d" % si)]]))
            return

        if step == "dialogue":
            dialogue = DIALOGUE_BY_ID.get(session.get("dialogue"))
            if not dialogue:
                self.advance_step(chat_id)
                return
            self.send(chat_id, texts.dialogue_card(dialogue),
                      inline([[btn("✅ Прочитал вслух, дальше", "s|next|%d" % si)]]))
            return

        if step == "test":
            questions = session.get("questions")
            if not questions:
                questions = course.build_test_questions(
                    self.store, chat_id, session["day"], self.rng, count=10)
                session["questions"] = questions
                session["qi"] = 0
                session["phase"] = "question"
                self.save_state(chat_id, state)
                self.send(chat_id, "🏁 <b>Тест недели</b>: 10 вопросов по всей неделе. Поехали!")
            self.send_question(chat_id)
            return

        if step == "ex":
            questions = session.get("questions")
            if questions is None:
                plan = course.plan_for_day(session["day"])
                _, exercise_count = course.practice_settings(user)
                questions = course.build_lesson_exercises(
                    plan, self.rng, session["cards"], count=exercise_count)
                session["questions"] = questions
                session["qi"] = 0
                session["phase"] = "question"
                self.save_state(chat_id, state)
            if not questions:
                self.advance_step(chat_id)
                return
            self.send_question(chat_id)
            return

        if step == "done":
            self.finish_session(chat_id)
            return

        self.advance_step(chat_id)

    def send_card(self, chat_id, step):
        state = self.state(chat_id)
        session = state["session"]
        keys = session.get("current") or []
        index = session.get("ci", 0)
        if index >= len(keys):
            session["ci"] = 0
            session["shown"] = False
            self.save_state(chat_id, state)
            self.advance_step(chat_id)
            return
        word = WORD_BY_KEY.get(keys[index])
        if not word:
            session["ci"] = index + 1
            self.save_state(chat_id, state)
            self.send_card(chat_id, step)
            return
        session["shown"] = False
        self.save_state(chat_id, state)
        review = step == "review"
        text = texts.word_front(word, index + 1, len(keys), review=review)
        keyboard = inline([
            [btn("👀 Показать перевод", "c|show|%d" % index)],
            [url_btn("🔊 Произношение", texts.pronunciation_url(word))],
        ])
        self.send(chat_id, text, keyboard)

    def show_card_back(self, chat_id, callback_id, message_id, index):
        state = self.state(chat_id)
        session = state.get("session")
        if not session or session.get("ci") != index:
            self.tg.answer_callback(callback_id, "Кнопка устарела")
            return
        keys = session.get("current") or []
        if index >= len(keys):
            return
        word = WORD_BY_KEY[keys[index]]
        step = session["steps"][session["si"]]
        first_time = not session.get("shown")
        session["shown"] = True

        if step == "review":
            keyboard = inline([
                [btn("😕 Не помню", "c|g|%d|0" % index), btn("🙂 Помню", "c|g|%d|1" % index),
                 btn("😎 Легко", "c|g|%d|2" % index)],
            ])
        else:
            if first_time:
                course.register_new_word(self.store, chat_id, word["key"])
            keyboard = inline([[btn("Дальше 👉", "c|next|%d" % index)]])

        self.save_state(chat_id, state)
        self.edit(chat_id, message_id, texts.word_back(word, first_time=first_time), keyboard)

    def grade_card(self, chat_id, callback_id, index, grade):
        state = self.state(chat_id)
        session = state.get("session")
        if not session or session.get("ci") != index:
            self.tg.answer_callback(callback_id, "Кнопка устарела")
            return
        keys = session.get("current") or []
        word = WORD_BY_KEY[keys[index]]
        result = course.grade_srs(self.store, chat_id, word["key"], grade)
        session["ci"] = index + 1
        session["shown"] = False
        if grade > 0:
            session["correct"] += 1
        session["total"] += 1
        self.save_state(chat_id, state)
        self.tg.answer_callback(callback_id, "Повторю %s" % course.interval_label(result["box"]))
        self.send_card(chat_id, session["steps"][session["si"]])

    def next_card(self, chat_id, callback_id, index):
        state = self.state(chat_id)
        session = state.get("session")
        if not session or session.get("ci") != index:
            self.tg.answer_callback(callback_id, "Кнопка устарела")
            return
        session["ci"] = index + 1
        session["shown"] = False
        self.save_state(chat_id, state)
        self.tg.answer_callback(callback_id)
        self.send_card(chat_id, session["steps"][session["si"]])

    def send_question(self, chat_id):
        state = self.state(chat_id)
        session = state.get("session")
        questions = session.get("questions") or []
        qi = session.get("qi", 0)
        if qi >= len(questions):
            self.advance_step(chat_id)
            return
        question = questions[qi]
        session["phase"] = "question"
        session["await"] = question["kind"] == "type"
        self.save_state(chat_id, state)

        text = texts.question_text(question, qi + 1, len(questions))
        if question["kind"] == "mc":
            rows = [[btn(option, "a|%d|%d" % (qi, idx))] for idx, option in enumerate(question["options"])]
            self.send(chat_id, text, inline(rows))
        else:
            hint = "✏️ <i>Напишите ответ сообщением. Регистр и знаки не важны.</i>"
            self.send(chat_id, text + "\n\n" + hint)

    def answer_question(self, chat_id, callback_id, message_id, qi, option):
        state = self.state(chat_id)
        session = state.get("session")
        if not session or session.get("qi") != qi or session.get("phase") != "question":
            self.tg.answer_callback(callback_id, "Кнопка устарела")
            return
        questions = session.get("questions") or []
        if qi >= len(questions):
            return
        question = questions[qi]
        if option >= len(question["options"]):
            return
        correct = option == question["correct"]
        session["phase"] = "result"
        session["await"] = False
        session["qi"] = qi + 1
        session["total"] = session.get("total", 0) + 1
        if correct:
            session["correct"] = session.get("correct", 0) + 1
        self.save_state(chat_id, state)
        self.record_answer(chat_id, question, correct)
        keyboard = inline([[btn("Дальше 👉", "n|%d|%d" % (session["si"], session["qi"]))]])
        self.tg.answer_callback(
            callback_id,
            "Верно ✅" if correct else "Правильно: %s" % question["options"][question["correct"]],
        )
        self.edit(chat_id, message_id, texts.answer_result(question, correct), keyboard)

    def next_question(self, chat_id, callback_id, si, qi):
        """Переход к следующему упражнению внутри текущего шага."""
        state = self.state(chat_id)
        session = state.get("session")
        if not session or session.get("si") != si or session.get("qi") != qi:
            self.tg.answer_callback(callback_id, "Кнопка устарела")
            return
        self.tg.answer_callback(callback_id)
        self.send_question(chat_id)

    def grade_typed(self, chat_id, text):
        state = self.state(chat_id)
        session = state.get("session")
        if not session:
            return
        questions = session.get("questions") or []
        qi = session.get("qi", 0)
        if qi >= len(questions) or session.get("phase") != "question":
            return
        question = questions[qi]
        ok, note = course.check_typed(text, question.get("answer", ""), question.get("accept", []))
        session["phase"] = "result"
        session["await"] = False
        session["qi"] = qi + 1
        session["total"] = session.get("total", 0) + 1
        if ok:
            session["correct"] = session.get("correct", 0) + 1
        self.save_state(chat_id, state)
        self.record_answer(chat_id, question, ok)
        keyboard = inline([[btn("Дальше 👉", "n|%d|%d" % (session["si"], session["qi"]))]])
        body = texts.answer_result(question, ok, note)
        if not ok:
            body += "\n\nВаш ответ: <i>%s</i>" % texts.esc(text[:80])
        self.send(chat_id, body, keyboard)

    def record_answer(self, chat_id, question, correct):
        """Записывает ответ в статистику; ошибка возвращает слово в очередь повторения."""
        word_key = question.get("word_key")
        if not word_key and question.get("grammar_id"):
            word_key = "g:" + question["grammar_id"]      # статистика тренажёра конструкций
        kind = "type" if question["kind"] == "type" else "mc"
        self.store.log_answer(chat_id, word_key, kind, correct)
        if word_key and not word_key.startswith("g:") and not correct:
            row = self.store.srs_row(chat_id, word_key)
            if row and row.get("learned"):
                course.grade_srs(self.store, chat_id, word_key, 0)

    def advance_step(self, chat_id):
        state = self.state(chat_id)
        session = state.get("session")
        if not session:
            return
        session["si"] = session.get("si", 0) + 1
        session["phase"] = "question"
        session["await"] = False
        session["qi"] = 0
        session["questions"] = None
        session["ci"] = 0
        session["shown"] = False
        self.save_state(chat_id, state)
        self.send_step(chat_id)

    def finish_session(self, chat_id):
        state = self.state(chat_id)
        session = state.get("session") or {}
        user = self.store.get_user(chat_id)
        kind = session.get("kind", "lesson")
        correct = session.get("correct", 0)
        total = session.get("total", 0)
        streak = user["streak"]

        if kind == "lesson" and not self.store.lesson_done_today(chat_id):
            info = self.store.finish_lesson(chat_id)
            streak = info.get("streak", streak)

        extra = ""
        new_day = user["day"]
        if kind == "lesson":
            day = session.get("day", user["day"])
            if session.get("is_review_day"):
                extra = "🏁 Неделя %d завершена! Тест недели пройден." % course.week_of_day(day)
            if day >= TOTAL_DAYS:
                extra = ("🎓 <b>Поздравляю, курс A1 пройден!</b>\n"
                         "Дальше: блок A2 — Present Perfect, условия, фразовые глаголы, аудирование. "
                         "Напишите /program, чтобы посмотреть план.")
            else:
                new_day = day + 1
                next_plan = course.plan_for_day(new_day, user["per_day"] or 5)
                extra = "➡️ Завтра: день %d, «%s»." % (new_day, next_plan["week_title"])
            self.store.update_user(chat_id, day=new_day, state=None)
        else:
            self.store.update_user(chat_id, state=None)
            if kind in ("constructions", "mixed") and session.get("drill_cards"):
                note = texts.drill_result_note(self.store, user, session["drill_cards"])
                if note:
                    extra = note
            elif kind == "new_words":
                extra = "🆕 Слова последних уроков закреплены. Они вернутся в повторение по расписанию."

        user = self.store.get_user(chat_id)
        self.send(chat_id, texts.session_finish(self.store, user, correct, total, streak, extra),
                  texts.MAIN_MENU)
        # прогресс изменился - сразу отправляем свежий снимок во внешнее хранилище
        self.uploader.upload_in_background()
        self.send(chat_id, "Что дальше?",
                  inline([
                      [btn("🧩 Конструкции", "go|constructions"), btn("✍️ Практика", "go|practice")],
                      [btn("🔁 Слабые слова", "go|review"), btn("📊 Прогресс", "go|progress")],
                      [btn("🆕 Новые слова", "go|newwords"), btn("📖 Словарь", "go|dictionary")],
                  ]))

    def maybe_restore_from_pinned(self, chat_id):
        """Спасательный круг после холодного старта бесплатного хостинга.

        Если база пустая (никто ещё не занимался), а в чате этого человека лежит
        закреплённая копия — восстанавливаем прогресс целиком. Так бот поднимается
        сам, без переменных окружения и ручных действий. Каждый чат проверяется
        один раз за запуск, поэтому восстановиться может любой владелец копии.
        """
        if not isinstance(self.remote, TelegramSnapshot) or chat_id in self.pinned_checked:
            return False
        self.pinned_checked.add(chat_id)
        try:
            with self.store.lock:
                answers = self.store.conn.execute("SELECT COUNT(*) AS c FROM answers").fetchone()["c"]
                learned = self.store.conn.execute(
                    "SELECT COUNT(*) AS c FROM srs WHERE learned = 1").fetchone()["c"]
            if answers or learned:
                return False                        # в базе есть настоящая работа - не трогаем

            remote = TelegramSnapshot(self.tg, chat_id=chat_id, log=log)
            if not remote.has_snapshot():
                return False

            temp = os.path.join(DATA_DIR, "pinned-restore.db")
            if not remote.download(temp):
                return False

            old_uploader = self.uploader
            old_uploader.stopping = True            # старый поток больше не нужен

            db_path = self.store.path
            safety = db_path + ".before-restore"
            self.store.close()
            if os.path.exists(db_path):
                shutil.copy2(db_path, safety)
            shutil.copy2(temp, db_path)
            os.remove(temp)
            self.store = Store(db_path)

            self.remote.chat_id = chat_id
            interval = int(os.environ.get("SNAPSHOT_INTERVAL") or 1800)
            self.uploader = SnapshotUploader(self.store, self.remote, interval=interval, log=log)
            self.uploader.start()
            atexit.register(self.uploader.upload_now)
            log("прогресс восстановлен из закреплённой копии в чате %s" % chat_id)
            return True
        except Exception:
            log("не удалось восстановить прогресс из копии:\n%s" % traceback.format_exc())
            return False

    # ------------------------------------------------------------------
    # callback-кнопки
    # ------------------------------------------------------------------

    def handle_callback(self, query):
        chat_id = query.get("message", {}).get("chat", {}).get("id")
        message_id = query.get("message", {}).get("message_id")
        callback_id = query.get("id")
        data = query.get("data") or ""
        if chat_id is None:
            return
        self.store.ensure_user(
            chat_id,
            query.get("from", {}).get("username"),
            query.get("from", {}).get("first_name"),
        )
        user = self.store.get_user(chat_id)
        parts = data.split("|")
        head = parts[0]

        if head == "onb":
            self.on_callback_onb(chat_id, callback_id, parts)
        elif head == "go":
            self.on_callback_go(chat_id, callback_id, parts)
        elif head == "c":
            if parts[1] == "show":
                self.show_card_back(chat_id, callback_id, message_id, int(parts[2]))
            elif parts[1] == "g":
                self.grade_card(chat_id, callback_id, int(parts[2]), int(parts[3]))
            elif parts[1] == "next":
                self.next_card(chat_id, callback_id, int(parts[2]))
        elif head == "a":
            self.answer_question(chat_id, callback_id, message_id, int(parts[1]), int(parts[2]))
        elif head == "n":
            self.next_question(chat_id, callback_id, int(parts[1]), int(parts[2]))
        elif head == "s":
            state = self.state(chat_id)
            session = state.get("session")
            if session and session.get("si") == int(parts[2]):
                self.tg.answer_callback(callback_id)
                self.advance_step(chat_id)
            else:
                self.tg.answer_callback(callback_id, "Кнопка устарела")
        elif head == "set":
            self.on_callback_settings(chat_id, callback_id, user, parts)
        elif head == "dic":
            self.on_callback_dictionary(chat_id, callback_id, message_id, user, parts)
        elif head == "drl":
            self.on_callback_drill(chat_id, callback_id, user, parts)
        elif head == "topic":
            text, keyboard = texts.topic_text(self.store, user, parts[1])
            self.edit(chat_id, message_id, text, keyboard)
            self.tg.answer_callback(callback_id)
        elif head == "words":
            text, keyboard = texts.words_text(self.store, user)
            self.edit(chat_id, message_id, text, keyboard)
            self.tg.answer_callback(callback_id)
        elif head == "gr":
            card = GRAMMAR_BY_ID.get(parts[1])
            if card:
                self.edit(chat_id, message_id, texts.grammar_card(card),
                          inline([[btn("⬅️ К списку", "gr|list")]]))
            else:
                text, keyboard = texts.grammar_index_text()
                self.edit(chat_id, message_id, text, keyboard)
            self.tg.answer_callback(callback_id)
        else:
            self.tg.answer_callback(callback_id, "Не понял кнопку")

    def on_callback_onb(self, chat_id, callback_id, parts):
        state = self.state(chat_id)
        tmp = state.setdefault("tmp", {})
        if parts[1] == "mode":
            mode, per_day = MODE_BY_BUTTON.get(parts[2], ("light", 5))
            tmp["mode"] = mode
            self.store.update_user(chat_id, mode=mode, per_day=per_day)
            state["pending"] = "onb_time"
            self.save_state(chat_id, state)
            self.tg.answer_callback(callback_id, "Режим: %s" % texts.MODE_TITLES[mode])
            self.send_start_step(chat_id)
        elif parts[1] == "time":
            if parts[2] == "custom":
                state["pending"] = "set_time"
                self.save_state(chat_id, state)
                self.tg.answer_callback(callback_id)
                self.send(chat_id, "Напишите время в формате <b>09:00</b>.")
                return
            tmp["time"] = parts[2]
            state["pending"] = "onb_tz"
            self.save_state(chat_id, state)
            self.tg.answer_callback(callback_id)
            self.send_start_step(chat_id)
        elif parts[1] == "tz":
            tmp["tz"] = int(parts[2])
            self.store.update_user(
                chat_id,
                tz_offset=int(parts[2]),
                remind_time=tmp.get("time", "09:00"),
                reminders_on=1,
                onboarded=1,
            )
            state["pending"] = "onb_finish"
            self.save_state(chat_id, state)
            self.tg.answer_callback(callback_id)
            self.send_start_step(chat_id)

    def on_callback_dictionary(self, chat_id, callback_id, message_id, user, parts):
        mode = parts[1]
        if mode == "noop":
            self.tg.answer_callback(callback_id, "Страница %d. Листайте ◀️ ▶️" % (int(parts[2]) + 1))
            return
        if mode == "home":
            text, keyboard = texts.dictionary_home(self.store, user)
        else:
            text, keyboard, _ = texts.dictionary_list(self.store, user, mode, int(parts[2]))
        self.edit(chat_id, message_id, text, keyboard)
        self.tg.answer_callback(callback_id)

    def on_callback_drill(self, chat_id, callback_id, user, parts):
        action = parts[1]
        if action == "mix":
            cards = course.drill_cards_available(course.clamp_day(user["day"]))
            questions = course.build_mixed_drill_questions(cards, self.rng, count=8)
            header = texts.trainer_intro(
                "constructions", "СМЕШАННЫЕ КОНСТРУКЦИИ", len(questions),
                "Все доступные конструкции вперемешку", "<i>Так проверяется, что правила не перепутаются.</i>")
        else:
            card_id = parts[2]
            card = GRAMMAR_BY_ID.get(card_id) or {}
            questions = course.build_drill_questions(card_id, self.rng, count=6)
            header = texts.trainer_intro(
                "constructions", texts.esc(card.get("title", "Конструкция")), len(questions),
                card.get("tip") or "")
        self.tg.answer_callback(callback_id)
        self.start_training(chat_id, "constructions", questions, header)

    def on_callback_go(self, chat_id, callback_id, parts):
        action = parts[1]
        user = self.store.get_user(chat_id)
        if action == "lesson":
            self.tg.answer_callback(callback_id)
            self.cmd_today(chat_id, user)
        elif action == "review":
            self.tg.answer_callback(callback_id)
            self.cmd_review(chat_id, user)
        elif action == "progress":
            self.tg.answer_callback(callback_id)
            self.cmd_progress(chat_id, user)
        elif action == "program":
            self.tg.answer_callback(callback_id)
            self.cmd_program(chat_id, user)
        elif action == "next_day":
            self.tg.answer_callback(callback_id)
            self.cmd_next_day(chat_id, user)
        elif action == "constructions":
            self.tg.answer_callback(callback_id)
            self.cmd_constructions(chat_id, user)
        elif action == "practice":
            self.tg.answer_callback(callback_id)
            self.cmd_practice(chat_id, user)
        elif action == "newwords":
            self.tg.answer_callback(callback_id)
            self.cmd_newwords(chat_id, user)
        elif action == "dictionary":
            self.tg.answer_callback(callback_id)
            self.cmd_dictionary(chat_id, user)
        elif action == "later":
            self.tg.answer_callback(callback_id, "Хорошо, напомню в следующий раз")

    def on_callback_settings(self, chat_id, callback_id, user, parts):
        action = parts[1]
        if action == "time":
            self.tg.answer_callback(callback_id)
            rows = [[btn(t, "onb|time|%s" % t) for t in TIME_CHOICES[:3]],
                    [btn(t, "onb|time|%s" % t) for t in TIME_CHOICES[3:]],
                    [btn("✏️ Другое время", "onb|time|custom")]]
            self.send(chat_id, "Во сколько напоминать?", inline(rows))
        elif action == "tz":
            self.tg.answer_callback(callback_id)
            rows = [[btn(name, "onb|tz|%d" % offset)] for name, offset in TZ_CHOICES]
            self.send(chat_id, "Выберите часовой пояс:", inline(rows))
        elif action == "mode":
            self.tg.answer_callback(callback_id)
            self.send(chat_id, "Сколько времени в день вы готовы заниматься?", inline([
                [btn("🌱 10 минут — короткий урок", "onb|mode|light")],
                [btn("🌿 20 минут — обычный урок", "onb|mode|standard")],
                [btn("🌳 40 минут — интенсивный урок", "onb|mode|intensive")],
            ]))
        elif action == "toggle_remind":
            new_value = 0 if user["reminders_on"] else 1
            self.store.update_user(chat_id, reminders_on=new_value)
            self.tg.answer_callback(
                callback_id, "Напоминания включены" if new_value else "Напоминания выключены")
            user = self.store.get_user(chat_id)
            self.send(chat_id, texts.settings_text(user), texts.settings_keyboard(user))
        elif action == "day":
            state = self.state(chat_id)
            state["pending"] = "set_day"
            self.save_state(chat_id, state)
            self.tg.answer_callback(callback_id)
            self.send(chat_id, "Введите номер дня курса (1–%d). Сейчас вы на дне %d." % (
                TOTAL_DAYS, user["day"]))
        elif action == "reset":
            self.tg.answer_callback(callback_id, "Прогресс сброшен")
            self.store.update_user(
                chat_id, day=1, streak=0, best_streak=0, total_lessons=0, total_answers=0,
                correct_answers=0, last_lesson_date=None, state=None,
            )
            with self.store.lock:
                self.store.conn.execute("DELETE FROM srs WHERE chat_id = ?", (chat_id,))
                self.store.conn.execute("DELETE FROM answers WHERE chat_id = ?", (chat_id,))
                self.store.conn.commit()
            self.send(chat_id, "Прогресс сброшен. Начинаем с дня 1!", texts.lesson_keyboard())

    # ------------------------------------------------------------------
    # напоминания
    # ------------------------------------------------------------------

    def check_reminders(self):
        sent = 0
        for user in self.store.all_users():
            if not user["onboarded"] or not user["reminders_on"]:
                continue
            tz = user["tz_offset"] or 0
            now_local = local_now(tz)
            today = local_date_str(tz)
            if user["last_lesson_date"] == today or user["last_remind_date"] == today:
                continue
            try:
                hh, mm = (user["remind_time"] or "09:00").split(":")
                target = int(hh) * 60 + int(mm)
            except Exception:
                target = 9 * 60
            current = now_local.hour * 60 + now_local.minute
            # Учитываем и «догоняющие» напоминания: если сервер спал и проснулся позже,
            # ученик всё равно получит урок - с пометкой о задержке.
            if target <= current <= min(target + 600, 22 * 60):
                late = current - target
                self.send(user["chat_id"], texts.reminder_text(user, late_minutes=late),
                          texts.reminder_keyboard())
                self.store.update_user(user["chat_id"], last_remind_date=today)
                sent += 1
        return sent

    def reminder_loop(self):
        while not self.stopping:
            try:
                self.touch_heartbeat()
                self.check_reminders()
            except Exception:
                log("reminder loop error:\n%s" % traceback.format_exc())
            time.sleep(30)

    def touch_heartbeat(self):
        """Отметка «бот жив». По ней сторож понимает, что процесс не завис."""
        try:
            os.makedirs(DATA_DIR, exist_ok=True)
            with open(HEARTBEAT_PATH, "w", encoding="ascii") as handle:
                handle.write(iso(utcnow()))
        except OSError:
            pass

    def start_reminders(self):
        if self.reminder_thread:
            return
        self.reminder_thread = threading.Thread(target=self.reminder_loop, daemon=True)
        self.reminder_thread.start()

    # ------------------------------------------------------------------
    # запуск
    # ------------------------------------------------------------------

    def setup(self):
        # Важно: pending-обновления не выбрасываем - иначе можно потерять /start,
        # который человек нажал ровно в момент перезапуска. Обработанные апдейты
        # отсекаются по last_update_id, сохранённому в базе.
        self.tg.delete_webhook(drop_pending_updates=False)
        self.me = self.tg.get_me()
        try:
            self.tg.set_my_commands(COMMANDS)
        except TgError as err:
            log("setMyCommands failed: %s" % err)
        saved = self.store.get_meta("last_update_id")
        if saved:
            self.offset = int(saved) + 1
        log("Бот запущен: @%s (%s)" % (self.me.get("username"), self.me.get("first_name")))
        if self.remote.enabled:
            kind = "чат Telegram (закреплённая копия)" if isinstance(self.remote, TelegramSnapshot) \
                else "внешнее хранилище %s" % getattr(self.remote, "url", "")
            log("хранилище снимков базы: %s" % kind)
            self.uploader.start()
            atexit.register(self.uploader.upload_now)
        self.start_reminders()
        threading.Thread(target=self._safe_auto_backup, daemon=True).start()

    def _safe_auto_backup(self):
        try:
            self.maybe_auto_backup()
        except Exception:
            log("auto backup error:\n%s" % traceback.format_exc())

    def remember_offset(self):
        if self.offset is not None:
            self.store.set_meta("last_update_id", self.offset - 1)

    def run_polling(self):
        self.setup()
        conflicts = 0
        while not self.stopping:
            try:
                updates = self.tg.get_updates(offset=self.offset, timeout=25,
                                              allowed_updates=["message", "callback_query"])
                conflicts = 0
                if os.path.exists(CONFLICT_FLAG):
                    try:
                        os.remove(CONFLICT_FLAG)
                    except OSError:
                        pass
            except TgError as err:
                if err.code == 409:
                    conflicts += 1
                    log("конфликт экземпляров (%d/5): другой бот уже читает обновления. "
                        "Остановите лишний экземпляр (на ПК: remove_autostart.bat, "
                        "в облаке: suspend сервиса)." % conflicts)
                    if conflicts >= 5:
                        try:
                            os.makedirs(DATA_DIR, exist_ok=True)
                            with open(CONFLICT_FLAG, "w", encoding="utf-8") as handle:
                                handle.write(iso(utcnow()))
                        except OSError:
                            pass
                        log("останавливаюсь, чтобы не мешать второму экземпляру")
                        return 2
                else:
                    log("getUpdates error: %s" % err)
                time.sleep(5)
                continue
            except Exception as err:
                log("getUpdates error: %s" % err)
                time.sleep(3)
                continue
            if updates:
                self.remember_offset()
            for update in updates:
                self.offset = update["update_id"] + 1
                try:
                    self.handle_update(update)
                except Exception:
                    log("handler error:\n%s" % traceback.format_exc())
                self.remember_offset()

    def landing_page(self):
        """Публичная страница со статистикой проекта (без личных данных) - для портфолио и health-check."""
        try:
            counts = self.store.stats()
            srs = 0
            with self.store.lock:
                row = self.store.conn.execute("SELECT COUNT(*) AS c FROM srs").fetchone()
                srs = row["c"] if row else 0
        except Exception:
            counts, srs = {"users": 0}, 0
        uptime = utcnow() - self.started_at
        hours, remainder = divmod(int(uptime.total_seconds()), 3600)
        username = (self.me or {}).get("username", "")
        bot_link = "https://t.me/%s" % username if username else "#"
        return ("<!DOCTYPE html><html lang='ru'><head><meta charset='utf-8'>"
                "<meta name='viewport' content='width=device-width, initial-scale=1'>"
                "<title>English Starter — Telegram-бот для изучения английского</title>"
                "<style>body{font-family:system-ui,Segoe UI,Roboto,sans-serif;background:#0f172a;"
                "color:#e2e8f0;margin:0;padding:40px 20px}.card{max-width:760px;margin:0 auto;"
                "background:#1e293b;border-radius:16px;padding:32px}h1{margin:0 0 8px;font-size:28px}"
                ".sub{color:#94a3b8;margin-bottom:24px}.grid{display:grid;grid-template-columns:"
                "repeat(auto-fit,minmax(150px,1fr));gap:12px;margin:24px 0}.stat{background:#0f172a;"
                "border-radius:12px;padding:16px}.num{font-size:24px;font-weight:700;color:#38bdf8}"
                ".lbl{color:#94a3b8;font-size:13px}a.btn{display:inline-block;background:#2563eb;color:#fff;"
                "text-decoration:none;padding:12px 20px;border-radius:10px;font-weight:600}"
                "footer{color:#64748b;font-size:13px;margin-top:24px}</style></head><body>"
                "<div class='card'><h1>🇬🇧 English Starter</h1>"
                "<div class='sub'>Telegram-бот: английский с нуля до A1 — 12 недель по 10 минут в день</div>"
                "<div class='grid'>"
                "<div class='stat'><div class='num'>%d</div><div class='lbl'>слов в курсе</div></div>"
                "<div class='stat'><div class='num'>%d</div><div class='lbl'>грамматических карточек</div></div>"
                "<div class='stat'><div class='num'>%d</div><div class='lbl'>заданий тренажёра</div></div>"
                "<div class='stat'><div class='num'>%d</div><div class='lbl'>диалогов</div></div>"
                "<div class='stat'><div class='num'>%d</div><div class='lbl'>дней курса</div></div>"
                "<div class='stat'><div class='num'>%d</div><div class='lbl'>учеников</div></div>"
                "<div class='stat'><div class='num'>%d</div><div class='lbl'>слов в повторении</div></div>"
                "<div class='stat'><div class='num'>%d ч</div><div class='lbl'>бот работает без сбоев</div></div>"
                "</div><a class='btn' href='%s'>Открыть бота в Telegram</a>"
                "<footer>Интервальное повторение (1→2→4→8→16→32 дня), 7 типов упражнений, "
                "ежедневные напоминания. Работает круглосуточно.</footer></div></body></html>") % (
            STATS["words"], STATS["grammar"], STATS["drill_items"], STATS["dialogues"],
            STATS["days"], counts["users"], srs, hours, bot_link,
        )

    def run_webhook(self, url, port=8080, secret=None):
        from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

        bot = self

        class Handler(BaseHTTPRequestHandler):
            protocol_version = "HTTP/1.1"

            def _reply(self, code, body=b"ok", content_type="text/plain; charset=utf-8"):
                self.send_response(code)
                self.send_header("Content-Type", content_type)
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

            def do_GET(self):
                path = self.path.split("?")[0]
                if path in ("/health", "/healthz"):
                    self._reply(200, b"ok")
                    return
                if path == "/":
                    try:
                        body = bot.landing_page().encode("utf-8")
                    except Exception:
                        body = b"English Starter bot is alive"
                    self._reply(200, body, content_type="text/html; charset=utf-8")
                    return
                self._reply(404, b"not found")

            def do_POST(self):
                if secret and self.path != "/tg/%s" % secret:
                    self._reply(403, b"forbidden")
                    return
                length = int(self.headers.get("Content-Length") or 0)
                raw = self.rfile.read(length) if length else b"{}"
                self._reply(200, b"ok")
                try:
                    update = json.loads(raw.decode("utf-8"))
                except ValueError:
                    return
                try:
                    bot.handle_update(update)
                except Exception:
                    log("webhook handler error:\n%s" % traceback.format_exc())

            def log_message(self, fmt, *args):
                return

        self.setup()
        webhook_url = url.rstrip("/")
        if secret:
            webhook_url += "/tg/%s" % secret
        self.tg.set_webhook(webhook_url, secret_token=None, drop_pending_updates=False)
        log("Webhook установлен: %s" % webhook_url)
        server = ThreadingHTTPServer(("0.0.0.0", port), Handler)
        log("HTTP-сервер слушает порт %s" % port)
        server.serve_forever()


def main(argv=None):
    parser = argparse.ArgumentParser(description="English Starter — Telegram-бот для изучения английского")
    parser.add_argument("--token", help="токен бота от @BotFather")
    parser.add_argument("--db", default=os.environ.get("DB_PATH", DB_DEFAULT), help="путь к файлу базы")
    parser.add_argument("--api-base", default=os.environ.get("TG_API_BASE"), help="свой адрес Bot API")
    parser.add_argument("--webhook-url", default=os.environ.get("WEBHOOK_URL"),
                        help="публичный адрес для режима webhook (облако)")
    parser.add_argument("--port", type=int, default=int(os.environ.get("PORT", "8080")))
    parser.add_argument("--secret", default=os.environ.get("WEBHOOK_SECRET"))
    parser.add_argument("--check", action="store_true", help="проверить контент курса и выйти")
    parser.add_argument("--remind-once", action="store_true", help="разослать напоминания и выйти")
    parser.add_argument("--backup-now", action="store_true",
                        help="отправить владельцу резервную копию базы и выйти")
    parser.add_argument("--lock", default=os.environ.get("LOCK_PATH"),
                        help="файл блокировки единственного экземпляра")
    args = parser.parse_args(argv)

    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

    if args.check:
        problems = validate()
        print("Контент: %d тем, %d слов, %d карточек грамматики, %d диалогов, "
              "%d заданий тренажёра (%d конструкций), %d недель" % (
                  STATS["topics"], STATS["words"], STATS["grammar"], STATS["dialogues"],
                  STATS["drill_items"], STATS["drill_cards"], STATS["weeks"]))
        if problems:
            print("Проблемы:")
            for problem in problems:
                print("  - %s" % problem)
            return 1
        print("Проверка пройдена: ошибок нет.")
        return 0

    token = resolve_token(args.token)
    if not token:
        print("Нет токена бота.\n"
              "1) Получите токен у @BotFather в Telegram (/newbot).\n"
              "2) Положите его в файл token.txt рядом с bot.py или задайте переменную BOT_TOKEN.\n"
              "3) Запустите снова: python bot.py")
        return 2

    # Режим работы: если есть публичный адрес - webhook (облако), иначе long polling.
    # Render сам подставляет RENDER_EXTERNAL_URL, поэтому в облаке ничего настраивать не нужно.
    webhook_url = (args.webhook_url or os.environ.get("WEBHOOK_URL")
                   or os.environ.get("RENDER_EXTERNAL_URL"))
    secret = args.secret or os.environ.get("WEBHOOK_SECRET")
    if webhook_url and not secret:
        # стабильный секрет: путь webhook не меняется между перезапусками
        secret = hashlib.sha256(("english-starter:" + token).encode("utf-8")).hexdigest()[:16]

    # Бесплатные хостинги стирают диск при перезапуске: снимок базы может лежать
    # во внешнем key-value хранилище или в закреплённом файле чата Telegram.
    # Клиент Telegram нужен уже здесь, поэтому создаём его до старта бота.
    early_tg = Telegram(token, api_base=args.api_base) if args.api_base else Telegram(token)
    remote = build_snapshot_provider(early_tg, log=log)
    if remote.enabled and restore_if_needed(os.path.dirname(os.path.abspath(args.db)),
                                            remote, log=log):
        log("прогресс поднят из резервной копии")

    # Один экземпляр на базу: второй процесс не должен драться за getUpdates
    lock = InstanceLock(args.lock or LOCK_PATH, os.environ.get("PID_PATH") or PID_PATH)
    if not lock.acquire():
        message = ("Бот уже запущен (блокировка %s занята другим процессом).\n"
                   "Если это ошибка - остановите лишний процесс или удалите файл." % lock.path)
        print(message)
        log(message)
        return 3

    bot = Bot(token, db_path=args.db, api_base=args.api_base, remote=remote)
    try:
        if args.remind_once:
            bot.me = bot.tg.get_me()
            print("Разослано напоминаний: %d" % bot.check_reminders())
            return 0
        if args.backup_now:
            bot.me = bot.tg.get_me()
            admin = bot.admin_chat_id()
            if not admin:
                print("В базе ещё нет учеников - копию отправить некому.")
                return 0
            ok = bot.send_backup(admin, reason="Копия по запросу (--backup-now)")
            print("Копия отправлена: %s" % ("да" if ok else "нет, смотрите logs/bot.log"))
            return 0

        if webhook_url:
            log("режим webhook, адрес: %s" % webhook_url)
            bot.run_webhook(webhook_url, port=args.port, secret=secret)
            return 0
        log("режим long polling")
        return bot.run_polling() or 0
    finally:
        lock.release()


if __name__ == "__main__":
    sys.exit(main())
