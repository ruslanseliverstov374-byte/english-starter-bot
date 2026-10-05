#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Ставит пинг облачного бота в планировщик Windows (каждые 5 минут).

Нужен, чтобы бесплатный Render не засыпал и напоминания приходили вовремя.
Снять задачу:  python tools/install_ping.py --remove
"""

import argparse
import os
import shutil
import subprocess
import sys

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPT = os.path.join(BASE, "tools", "ping_service.py")
TASK = "EnglishStarterPing"


def log(message):
    try:
        print(message)
    except Exception:
        pass


def pythonw():
    base = getattr(sys, "_base_executable", None) or sys.executable
    candidate = os.path.join(os.path.dirname(base), "pythonw.exe")
    if os.path.exists(candidate) and "WindowsApps" not in candidate:
        return candidate
    found = shutil.which("pythonw")
    if found and "WindowsApps" not in found:
        return found
    return sys.executable


def main(argv=None):
    parser = argparse.ArgumentParser(description="Пинг облачного бота по расписанию")
    parser.add_argument("--remove", action="store_true", help="удалить задачу")
    parser.add_argument("--every", type=int, default=5, help="интервал в минутах")
    args = parser.parse_args(argv)

    if os.name != "nt":
        log("Скрипт для Windows. На Linux/VPS пинг не нужен — сервис не спит.")
        return 1

    if args.remove:
        result = subprocess.run(["schtasks", "/delete", "/f", "/tn", TASK])
        log("Задача %s удалена" if result.returncode == 0 else "Задача не найдена")
        return 0

    interpreter = pythonw()
    command = '"%s" "%s"' % (interpreter, SCRIPT)
    log("Интерпретатор: %s" % interpreter)
    log("Команда: %s" % command)

    result = subprocess.run([
        "schtasks", "/create", "/f", "/tn", TASK, "/tr", command,
        "/sc", "minute", "/mo", str(args.every), "/rl", "limited",
    ])
    if result.returncode != 0:
        log("")
        log("[!] Не удалось создать задачу автоматически.")
        log("    Ручной способ: Win+R → taskschd.msc → «Создать задачу»")
        log("    Триггер: каждые 5 минут; действие: %s" % interpreter)
        log("    Аргументы: %s" % SCRIPT)
        return 1

    log("")
    log("[+] Задача %s создана: пинг каждые %d мин." % (TASK, args.every))
    log("    Лог: logs\\ping.log   |   снять: python tools\\install_ping.py --remove")

    log("")
    log("Проверяю прямо сейчас...")
    subprocess.run([sys.executable, SCRIPT], cwd=BASE)
    return 0


if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    sys.exit(main())
