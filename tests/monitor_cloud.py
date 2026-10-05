# -*- coding: utf-8 -*-
"""Одна строка состояния облачного сервиса - для наблюдения за пересборкой."""

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
    print("%s -> учеников: %s | слов в повторении: %s | работает: %s" % (
        time.strftime("%H:%M:%S"),
        stats.get("учеников", "?"),
        stats.get("слов в повторении", "?"),
        stats.get("бот работает без сбоев", "?"),
    ))
except Exception as error:
    print("%s -> сервис недоступен (%s)" % (time.strftime("%H:%M:%S"), error))
