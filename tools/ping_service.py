#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Будит облачного бота одним запросом (для планировщика Windows).

Бесплатный Render засыпает после 15 минут без запросов: спящий сервис не может
отправить напоминание. Этот скрипт раз в 5 минут дёргает /health и держит бота
проснувшимся. Запускается задачей планировщика, вручную нужен только для проверки.

Проверка:  python tools/ping_service.py
"""

import os
import sys
import time
import urllib.request

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
URL = os.environ.get("PING_URL", "https://english-starter-bot.onrender.com/health")
LOG_PATH = os.path.join(BASE, "logs", "ping.log")
MAX_LOG_BYTES = 200 * 1024


def log(message):
    line = "[%s] %s" % (time.strftime("%Y-%m-%d %H:%M:%S"), message)
    try:
        print(line)
    except Exception:
        pass
    try:
        os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)
        if os.path.exists(LOG_PATH) and os.path.getsize(LOG_PATH) > MAX_LOG_BYTES:
            with open(LOG_PATH, "r", encoding="utf-8-sig", errors="ignore") as handle:
                tail = handle.readlines()[-200:]
            with open(LOG_PATH, "w", encoding="utf-8-sig") as handle:
                handle.writelines(tail)
        with open(LOG_PATH, "a", encoding="utf-8-sig") as handle:
            handle.write(line + "\n")
    except Exception:
        pass


def main():
    started = time.time()
    try:
        with urllib.request.urlopen(URL, timeout=90) as response:
            body = response.read().decode("utf-8", "replace").strip()
            code = response.status
        log("ping %s -> HTTP %s (%s) за %.1f с" % (URL, code, body[:20], time.time() - started))
        return 0 if code == 200 else 1
    except Exception as error:
        log("ping %s -> ошибка: %s" % (URL, error))
        return 1


if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    sys.exit(main())
