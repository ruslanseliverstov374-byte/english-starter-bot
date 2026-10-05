# -*- coding: utf-8 -*-
"""Живой тест хранилища копий в чате Telegram (на реальном боте и реальном чате).

Что делает:
  1) снимает копию локальной базы с прогрессом;
  2) отправляет её в чат владельца и закрепляет (тихо, без уведомления);
  3) читает закреплённое сообщение через getChat и скачивает файл обратно;
  4) сверяет, что скачанная база совпадает с исходной (ученики, слова, ответы).

Запуск:  python tests/deploy_telegram_backup.py
"""

import os
import sqlite3
import sys

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE)

from remote_store import TelegramSnapshot          # noqa: E402
from store import Store                            # noqa: E402
from tgbot import Telegram                         # noqa: E402

DB_PATH = os.path.join(BASE, "data", "bot.db")
CHAT_ID = int(os.environ.get("ADMIN_CHAT_ID", "1368878379"))
TOKEN_FILE = os.path.join(BASE, "token.txt")
WORK = os.path.join(BASE, "tests", "_run")


def counts(path):
    conn = sqlite3.connect(path)
    try:
        return {table: conn.execute("SELECT COUNT(*) FROM %s" % table).fetchone()[0]
                for table in ("users", "srs", "answers")}
    finally:
        conn.close()


def main():
    token = open(TOKEN_FILE, encoding="utf-8").read().strip()
    tg = Telegram(token)

    os.makedirs(WORK, exist_ok=True)
    source = os.path.join(WORK, "live-snapshot.db")
    downloaded = os.path.join(WORK, "live-restored.db")
    for path in (source, downloaded):
        if os.path.exists(path):
            os.remove(path)

    store = Store(DB_PATH)
    store.snapshot(source)
    store.close()
    before = counts(source)
    print("копия снята: %.1f КБ, учеников %d, слов %d, ответов %d"
          % (os.path.getsize(source) / 1024.0, before["users"], before["srs"], before["answers"]))

    remote = TelegramSnapshot(tg, chat_id=CHAT_ID, log=lambda m: print("   [хранилище] %s" % m))
    print()
    print("отправляю и закрепляю копию в чате %d..." % CHAT_ID)
    if not remote.upload(source):
        print("❌ не удалось закрепить копию")
        return 1

    print("читаю закреплённое сообщение через getChat...")
    if not remote.has_snapshot():
        print("❌ закреплённая копия не найдена")
        return 1

    print("скачиваю копию обратно (как это сделает бот после перезапуска)...")
    if not remote.download(downloaded):
        print("❌ не удалось скачать копию")
        return 1

    after = counts(downloaded)
    print()
    print("сверка: до %s / после %s" % (before, after))
    if before == after:
        print("✅ ХРАНИЛИЩЕ РАБОТАЕТ: копия закреплена в чате и читается обратно полностью")
        return 0
    print("❌ данные не совпали")
    return 1


if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    sys.exit(main())
