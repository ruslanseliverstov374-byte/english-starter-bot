# -*- coding: utf-8 -*-
"""Одна строка состояния облачного сервиса - для наблюдения за пересборкой и пингом."""

import re
import sys
import time
import urllib.request

BASE_URL = "https://english-starter-bot.onrender.com"
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

try:
    with urllib.request.urlopen(BASE_URL + "/", timeout=60) as response:
        html = response.read().decode("utf-8", "replace")
    stats = {label: value for value, label in
             re.findall(r"class='num'>([^<]+)</div><div class='lbl'>([^<]+)<", html)}
    keys = ["учеников", "слов в повторении", "последний сигнал пинга",
            "внешних пингов не было", "бот работает без сбоев"]
    parts = ["%s: %s" % (key, stats[key]) for key in keys if key in stats]
    print("%s -> %s" % (time.strftime("%H:%M:%S"), " | ".join(parts) or "страница без статистики"))
except Exception as error:
    print("%s -> сервис недоступен (%s)" % (time.strftime("%H:%M:%S"), error))
