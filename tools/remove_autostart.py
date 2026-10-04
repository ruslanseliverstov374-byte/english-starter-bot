#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Снимает автозапуск бота и останавливает его. Запуск: tools/remove_autostart.py"""

import os
import subprocess
import sys

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE)

TASKS = ["EnglishStarterBot", "EnglishStarterBotWatchdog"]


def log(message):
    try:
        print(message)
    except Exception:
        pass


def main():
    for task in TASKS:
        result = subprocess.run(["schtasks", "/delete", "/f", "/tn", task])
        if result.returncode == 0:
            log("[+] Задача %s удалена" % task)

    log("")
    subprocess.run([sys.executable, os.path.join(BASE, "tools", "stop_bot.py")], cwd=BASE)
    return 0


if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    sys.exit(main())
