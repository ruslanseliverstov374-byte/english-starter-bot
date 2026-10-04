# -*- coding: utf-8 -*-
"""Отладочный прогон одного урока с распечаткой всех сообщений бота."""

import os
import random
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE)
sys.path.insert(0, os.path.join(BASE, "tests"))

import bot as botmod          # noqa: E402
import simulate as S          # noqa: E402

rng = random.Random(1)
workdir = os.path.join(BASE, "tests", "_run")
os.makedirs(workdir, exist_ok=True)
db = os.path.join(workdir, "debug.db")
if os.path.exists(db):
    os.remove(db)

bot = botmod.Bot("111:TEST", db_path=db)
fake = S.FakeTg()
bot.tg = fake
bot.me = fake.get_me()
bot.handle_update(S.text_update("/start"))
bot.handle_update(S.callback_update("onb|mode|light"))
bot.handle_update(S.callback_update("onb|time|09:00"))
bot.handle_update(S.callback_update("onb|tz|180"))
ok = S.run_lesson(bot, fake, rng)

print("урок завершён:", ok, "| сообщений:", len(fake.sent))
for message in fake.sent:
    text = (message["text"] or "").replace("\n", " | ")[:120]
    print("  •", text)
print("ответов записано:", bot.store.get_user(S.CHAT_ID)["total_answers"])
print("состояние:", bot.state(S.CHAT_ID))
