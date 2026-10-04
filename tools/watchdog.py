#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Сторож: следит, чтобы бот работал круглосуточно.

Запускается планировщиком Windows каждые 5 минут и при входе в систему.
Если бот уже запущен (файл data/bot.lock занят живым процессом) - ничего не делает.
Если бота нет - запускает его отдельным процессом без окна консоли.

Ручной запуск для проверки:  python tools/watchdog.py
"""

import os
import subprocess
import sys
import time

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE)

from instance_lock import InstanceLock          # noqa: E402
from store import utcnow                        # noqa: E402

LOCK_PATH = os.path.join(BASE, "data", "bot.lock")
PID_PATH = os.path.join(BASE, "data", "bot.pid")
HEARTBEAT_PATH = os.path.join(BASE, "data", "heartbeat")
STATE_PATH = os.path.join(BASE, "data", "watchdog.state")
CONFLICT_FLAG = os.path.join(BASE, "data", "conflict.flag")
LOG_PATH = os.path.join(BASE, "logs", "watchdog.log")
BOT_LOG = os.path.join(BASE, "logs", "bot.log")
DB_PATH = os.environ.get("DB_PATH", os.path.join(BASE, "data", "bot.db"))
CONFLICT_PAUSE_SECONDS = 30 * 60          # не перезапускать при конфликте экземпляров
HUNG_SECONDS = int(os.environ.get("HUNG_SECONDS", "900"))   # 15 минут без отметки = завис


def log(message, only_if_changed=False):
    line = "[%s] %s" % (time.strftime("%Y-%m-%d %H:%M:%S"), message)
    if only_if_changed:
        try:
            with open(STATE_PATH, "r", encoding="utf-8") as handle:
                if handle.read().strip() == message:
                    return
        except OSError:
            pass
        try:
            with open(STATE_PATH, "w", encoding="utf-8") as handle:
                handle.write(message)
        except OSError:
            pass
    try:
        print(line)
    except Exception:
        pass
    try:
        os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)
        with open(LOG_PATH, "a", encoding="utf-8-sig") as handle:
            handle.write(line + "\n")
    except Exception:
        pass


def python_for_background():
    """pythonw.exe - запуск без окна консоли (Windows)."""
    executable = sys.executable
    if os.name == "nt":
        candidate = os.path.join(os.path.dirname(executable), "pythonw.exe")
        if os.path.exists(candidate):
            return candidate
    return executable


def conflict_recently():
    if not os.path.exists(CONFLICT_FLAG):
        return False
    age = time.time() - os.path.getmtime(CONFLICT_FLAG)
    return age < CONFLICT_PAUSE_SECONDS


def hung_bot():
    """Бот держит блокировку, но давно не давал о себе знать - значит завис."""
    try:
        age = time.time() - os.path.getmtime(HEARTBEAT_PATH)
    except OSError:
        return False                     # отметки ещё нет - бот только стартовал
    return age > HUNG_SECONDS


def restart_hung_bot():
    import ctypes
    pid = InstanceLock.running_pid(PID_PATH)
    if not pid:
        return False
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    handle = kernel32.OpenProcess(0x0001, False, pid)       # PROCESS_TERMINATE
    if not handle:
        return False
    try:
        killed = bool(kernel32.TerminateProcess(handle, 0))
    finally:
        kernel32.CloseHandle(handle)
    log("бот завис (нет отметки %d мин) — завершаю PID %s" % (HUNG_SECONDS // 60, pid))
    time.sleep(2)
    return killed


def start_bot():
    os.makedirs(os.path.dirname(BOT_LOG), exist_ok=True)
    stdout = open(BOT_LOG, "ab")
    command = [python_for_background(), os.path.join(BASE, "bot.py"), "--db", DB_PATH]
    creationflags = 0
    if os.name == "nt":
        creationflags = 0x00000008 | 0x00000200      # DETACHED_PROCESS | CREATE_NEW_PROCESS_GROUP
    process = subprocess.Popen(
        command,
        cwd=BASE,
        stdout=stdout,
        stderr=stdout,
        stdin=subprocess.DEVNULL,
        creationflags=creationflags,
        close_fds=True,
    )
    log("бот запущен сторожем, PID %s" % process.pid)
    return process


def main():
    os.makedirs(os.path.join(BASE, "data"), exist_ok=True)

    lock = InstanceLock(LOCK_PATH, PID_PATH)
    if not lock.acquire():
        # файл занят - значит бот работает
        if hung_bot():
            restart_hung_bot()
            log("поднимаю бота заново после зависания")
        else:
            log("бот работает (PID %s), ничего не делаю" % InstanceLock.running_pid(PID_PATH),
                only_if_changed=True)
            return 0
    else:
        lock.release()

    if conflict_recently():
        log("пропускаю запуск: был конфликт экземпляров (два бота одновременно). "
            "Остановите лишний экземпляр и удалите data/conflict.flag")
        return 0

    log("бот не найден - запускаю")
    start_bot()
    time.sleep(6)

    check = InstanceLock(LOCK_PATH, PID_PATH)
    if check.acquire():
        check.release()
        log("ВНИМАНИЕ: бот запустился, но не удержал блокировку - проверьте logs/bot.log")
        return 1
    log("бот работает, блокировка удерживается")
    return 0


if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    sys.exit(main())
