# -*- coding: utf-8 -*-
"""Проверка облачного сервиса снаружи: health, страница статистики, webhook."""

import re
import sys
import urllib.request

BASE_URL = "https://english-starter-bot.onrender.com"

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

try:
    with urllib.request.urlopen(BASE_URL + "/health", timeout=90) as response:
        print("health: HTTP %d, тело: %r" % (response.status, response.read().decode()))
except Exception as error:
    print("health: ОШИБКА %s" % error)

try:
    with urllib.request.urlopen(BASE_URL + "/", timeout=90) as response:
        html = response.read().decode("utf-8", "replace")
    stats = re.findall(r"class='num'>([^<]+)</div><div class='lbl'>([^<]+)<", html)
    print("страница статистики: HTTP %d" % response.status)
    for value, label in stats:
        print("   %-12s %s" % (value, label))
except Exception as error:
    print("страница статистики: ОШИБКА %s" % error)
