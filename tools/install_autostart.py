#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Ставит бота на автозапуск в Windows (две задачи планировщика).

1) EnglishStarterBot         - запуск сторожа при входе в систему;
2) EnglishStarterBotWatchdog - проверка каждые 5 минут: если бот упал, поднять.

Запуск:  python tools/install_autostart.py     (или install_autostart.bat)
Снять:   python tools/remove_autostart.py
"""

import os
import shutil
import subprocess
import sys

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE)

WATCHDOG = os.path.join(BASE, "tools", "watchdog.py")
TASK_MAIN = "EnglishStarterBot"
TASK_WATCH = "EnglishStarterBotWatchdog"


def log(message):
    try:
        print(message)
    except Exception:
        pass


def find_pythonw():
    """Настоящий pythonw.exe (без окна), минуя алиасы WindowsApps."""
    candidates = []

    base = getattr(sys, "_base_executable", None) or sys.executable
    candidates.append(os.path.join(os.path.dirname(base), "pythonw.exe"))

    for name in ("pythonw.exe",):
        found = shutil.which(name)
        if found:
            candidates.append(found)

    home = os.environ.get("USERPROFILE", "")
    if home:
        candidates.append(os.path.join(home, "AppData", "Local", "Python", "bin", "pythonw.exe"))

    candidates.append(os.path.join(os.path.dirname(sys.executable), "pythonw.exe"))

    for path in candidates:
        if path and os.path.exists(path) and "WindowsApps" not in path:
            return path
    return None   # запустим через python.exe (появится окно консоли)


def create_task(name, executable, argument, schedule_args):
    command = '"%s" "%s"' % (executable, argument)
    args = ["schtasks", "/create", "/f", "/tn", name, "/tr", command] + schedule_args
    log("  schtasks %s" % " ".join(args[2:]))
    result = subprocess.run(args)          # без перехвата вывода: видно текст ошибки
    if result.returncode != 0:
        log("    команда завершилась с кодом %d" % result.returncode)
    return result.returncode == 0


def main():
    if os.name != "nt":
        log("Этот скрипт только для Windows. На Linux используйте systemd (deploy/vps-install.sh).")
        return 1

    interpreter = find_pythonw()
    windowless = interpreter is not None
    if not windowless:
        interpreter = sys.executable
        log("ВНИМАНИЕ: pythonw.exe не найден, будет использован python.exe — "
            "при проверках может мигать окно консоли.")

    log("Интерпретатор: %s" % interpreter)
    log("Сторож: %s" % WATCHDOG)
    log("")

    ok_main = create_task(TASK_MAIN, interpreter, WATCHDOG, ["/sc", "onlogon", "/rl", "limited"])
    ok_watch = create_task(TASK_WATCH, interpreter, WATCHDOG, ["/sc", "minute", "/mo", "5", "/rl", "limited"])

    log("")
    if ok_main and ok_watch:
        log("[+] Задачи созданы:")
        log("    %s         — запуск бота при входе в систему" % TASK_MAIN)
        log("    %s — проверка каждые 5 минут" % TASK_WATCH)
    else:
        log("[!] Не удалось создать задачи автоматически.")
        log("    Ручной способ (1 минута):")
        log("      1) Win+R → введите  shell:startup  → Enter")
        log("      2) положите в открывшуюся папку ярлык на run.bat")
        log("    Или создайте задачу вручную: Win+R → taskschd.msc →")
        log("      «Создать задачу» → триггер «При входе в систему» →")
        log("      действие: %s" % interpreter)
        log("      аргументы: %s" % WATCHDOG)
        log("      рабочая папка: %s" % BASE)

    log("")
    log("Запускаю бота сейчас...")
    subprocess.run([sys.executable, WATCHDOG], cwd=BASE)

    pid_path = os.path.join(BASE, "data", "bot.pid")
    if os.path.exists(pid_path):
        with open(pid_path, "r", encoding="ascii", errors="ignore") as handle:
            log("Бот работает, PID %s" % handle.read().strip())
    log("")
    log("Логи: logs\\bot.log и logs\\watchdog.log")
    log("Остановить и снять автозапуск: remove_autostart.bat")
    if not windowless:
        return 0
    return 0 if ok_main and ok_watch else 0


if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    sys.exit(main())
