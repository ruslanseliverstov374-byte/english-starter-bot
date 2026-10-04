# -*- coding: utf-8 -*-
"""Диагностика нагрузочного стенда: показывает, что происходит на каждом шаге."""

import os
import random
import sys

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE)
sys.path.insert(0, os.path.join(BASE, "tests"))

import bot as botmod          # noqa: E402
import simulate as S          # noqa: E402
import stress as ST           # noqa: E402

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
botmod.log = lambda text: print("   [bot] %s" % text)

workdir = os.path.join(BASE, "tests", "_run")
os.makedirs(workdir, exist_ok=True)
db_path = os.path.join(workdir, "diag.db")
for suffix in ("", "-journal", "-wal", "-shm"):
    if os.path.exists(db_path + suffix):
        os.remove(db_path + suffix)

bot = botmod.Bot("111:DIAG", db_path=db_path)
fake = ST.MultiFakeTg()
bot.tg = fake
bot.me = fake.get_me()
rng = random.Random(3)

chat_id = 700000001
print("=== онбординг ===")
bot.handle_update(ST.message(chat_id, "/start"))
print("   клавиатура:", ST.buttons_for(fake, chat_id))
bot.handle_update(ST.press(chat_id, "onb|mode|light"))
bot.handle_update(ST.press(chat_id, "onb|time|09:00"))
bot.handle_update(ST.press(chat_id, "onb|tz|180"))
print("   клавиатура:", ST.buttons_for(fake, chat_id))

print("=== старт урока ===")
S.shift_time_back_one_day(bot.store, chat_id)
bot.handle_update(ST.message(chat_id, "/today"))
print("   клавиатура:", ST.buttons_for(fake, chat_id))
print("   состояние:", (bot.state(chat_id) or {}).get("session", {}).get("steps"))

for step in range(1, 16):
    session = (bot.state(chat_id) or {}).get("session") or {}
    available = ST.buttons_for(fake, chat_id)
    before = len(fake.sent)
    action = ST.one_action(bot, fake, chat_id, rng)
    after = len(fake.sent)
    print("шаг %2d | step=%s si=%s qi=%s await=%s | кнопок %d | действие=%s | новых сообщений %d" % (
        step, session.get("step"), session.get("si"), session.get("qi"),
        session.get("await"), len(available), action, after - before))
    if after - before:
        print("        последнее: %s" % fake.sent[-1]["text"].replace("\n", " | ")[:100])
    if not action:
        print("   стенд остановился: действия закончились")
        break
