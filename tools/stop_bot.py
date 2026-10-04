#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Аккуратно останавливает работающего бота.

Читает PID из data/bot.pid, проверяет, что это действительно python/pythonw
(а не чужая программа с тем же номером), и только потом завершает процесс.

Запуск:  python tools/stop_bot.py
"""

import ctypes
import os
import sys
import time

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE)

from instance_lock import InstanceLock          # noqa: E402

PID_PATH = os.path.join(BASE, "data", "bot.pid")
LOCK_PATH = os.path.join(BASE, "data", "bot.lock")

IS_WINDOWS = os.name == "nt"


def log(message):
    try:
        print(message)
    except Exception:
        pass


def process_image_name(pid):
    """Имя исполняемого файла процесса без запуска внешних программ."""
    if IS_WINDOWS:
        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        handle = kernel32.OpenProcess(0x1000, False, pid)      # QUERY_LIMITED_INFORMATION
        if not handle:
            return ""
        try:
            size = ctypes.c_ulong(32768)
            buffer = ctypes.create_unicode_buffer(size.value)
            if not kernel32.QueryFullProcessImageNameW(handle, 0, buffer, ctypes.byref(size)):
                return ""
            return os.path.basename(buffer.value).lower()
        finally:
            kernel32.CloseHandle(handle)
    try:
        with open("/proc/%d/cmdline" % pid, "r", encoding="utf-8", errors="ignore") as handle:
            return os.path.basename(handle.read().split("\0")[0]).lower()
    except OSError:
        return ""


def terminate(pid):
    if IS_WINDOWS:
        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        handle = kernel32.OpenProcess(0x0001, False, pid)      # PROCESS_TERMINATE
        if not handle:
            return False
        try:
            return bool(kernel32.TerminateProcess(handle, 0))
        finally:
            kernel32.CloseHandle(handle)
    try:
        os.kill(pid, 15)
        return True
    except OSError:
        return False


def main():
    os.makedirs(os.path.dirname(PID_PATH), exist_ok=True)

    lock = InstanceLock(LOCK_PATH, PID_PATH)
    if lock.acquire():
        lock.release()
        log("Бот не запущен — останавливать нечего.")
        return 0

    pid = InstanceLock.running_pid(PID_PATH)
    if not pid:
        log("Бот работает, но файл data/bot.pid не читается. "
            "Остановите процесс python/pythonw вручную (диспетчер задач).")
        return 1

    name = process_image_name(pid)
    if not name.startswith("python"):
        log("PID %d — это %s, а не бот. Ничего не делаю (защита от чужого процесса)."
            % (pid, name or "неизвестный процесс"))
        return 1

    log("Останавливаю бота (PID %d, %s)..." % (pid, name))
    if not terminate(pid):
        log("Не удалось завершить процесс.")
        return 1

    for _ in range(12):
        time.sleep(0.5)
        check = InstanceLock(LOCK_PATH, PID_PATH)
        if check.acquire():
            check.release()
            log("Бот остановлен.")
            return 0
    log("Процесс ещё держит блокировку — подождите пару секунд и проверьте снова.")
    return 1


if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    sys.exit(main())
