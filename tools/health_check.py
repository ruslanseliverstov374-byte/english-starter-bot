#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Проверка «бот жив?» по файлу-отметке и самовосстановление.

Бот каждые 30 секунд обновляет файл data/heartbeat. Если отметка устарела
(процесс завис, съел память, оборвалась сеть внутри цикла) - скрипт перезапускает бота.

Использование:
    python tools/health_check.py                          # только проверить (код 1, если плохо)
    python tools/health_check.py --restart-cmd "systemctl restart english-starter"
                                                          # перезапустить, если отметка старая

На сервере запускается systemd-таймером каждые 5 минут (см. deploy/vps_install.py).
На домашнем ПК тот же файл использует сторож tools/watchdog.py.
"""

import argparse
import os
import subprocess
import sys
import time

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HEARTBEAT_PATH = os.environ.get("HEARTBEAT_PATH", os.path.join(BASE, "data", "heartbeat"))
STALE_SECONDS = int(os.environ.get("HEARTBEAT_STALE_SECONDS", "900"))   # 15 минут


def log(message):
    line = "[%s] %s" % (time.strftime("%Y-%m-%d %H:%M:%S"), message)
    try:
        print(line)
    except Exception:
        pass
    try:
        path = os.path.join(BASE, "logs", "health.log")
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "a", encoding="utf-8-sig") as handle:
            handle.write(line + "\n")
    except Exception:
        pass


def heartbeat_age():
    """Сколько секунд назад бот давал о себе знать. None - отметки нет."""
    try:
        return time.time() - os.path.getmtime(HEARTBEAT_PATH)
    except OSError:
        return None


def main(argv=None):
    parser = argparse.ArgumentParser(description="Проверка живости бота")
    parser.add_argument("--restart-cmd", default=None,
                        help="команда перезапуска, если отметка устарела")
    parser.add_argument("--stale", type=int, default=STALE_SECONDS,
                        help="сколько секунд считать отметку устаревшей")
    args = parser.parse_args(argv)

    age = heartbeat_age()
    if age is None:
        log("отметки нет — бот, похоже, ещё не запускался (это нормально при первом старте)")
        return 0

    if age <= args.stale:
        return 0

    log("ВНИМАНИЕ: бот не отвечает %.0f минут (порог %d с)" % (age / 60.0, args.stale))

    if not args.restart_cmd:
        return 1

    log("перезапускаю: %s" % args.restart_cmd)
    try:
        result = subprocess.run(args.restart_cmd, shell=True, timeout=120)
        log("команда перезапуска завершилась с кодом %d" % result.returncode)
        return 0 if result.returncode == 0 else 1
    except Exception as err:
        log("не удалось перезапустить: %s" % err)
        return 1


if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    sys.exit(main())
