#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Установка English Starter на сервер (Ubuntu/Debian) без bash-скриптов.

Запуск на сервере от root:
    python3 /opt/english-bot/deploy/vps_install.py <ТОКЕН_БОТА>

Проверка без изменений (можно и на Windows):
    python3 deploy/vps_install.py ТОКЕН --dry-run --app-dir ./tests/_run/vps

Что делает:
  1) проверяет python3 и структуру проекта;
  2) создаёт .env с токеном (права 600), каталоги data/ и logs/;
  3) переносит базу с прогрессом, если приехал снимок deploy-snapshot.db;
  4) ставит четыре systemd-юнита:
       english-starter.service            - сам бот, автозапуск + перезапуск при падении
       english-starter-backup.timer       - ежедневная резервная копия в Telegram (20:00)
       english-starter-healthcheck.timer  - проверка каждые 5 минут: завис - перезапустить
       (и их .service-файлы)
  5) включает всё, проверяет связь с Telegram и печатает статус.

Внешние библиотеки не нужны: только стандартная библиотека Python.
"""

import argparse
import os
import shutil
import subprocess
import sys
import time
import urllib.error
import urllib.request

SOURCE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UNIT_DIR = "/etc/systemd/system"
DEFAULT_APP_DIR = "/opt/english-bot"

SERVICE = "english-starter"
BACKUP = "english-starter-backup"
HEALTHCHECK = "english-starter-healthcheck"

REQUIRED_FILES = ["bot.py", "course.py", "store.py", "texts.py", "tgbot.py",
                  "instance_lock.py", "content", "tools"]


def log(message):
    print("==> %s" % message)


def fail(message):
    print("[!] %s" % message)
    return 1


def py_version_ok():
    return sys.version_info >= (3, 8)


def unit_service(app_dir, python):
    return """[Unit]
Description=English Starter Telegram bot
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
WorkingDirectory={app}
EnvironmentFile={app}/.env
ExecStart={python} {app}/bot.py
Restart=always
RestartSec=5
StandardOutput=append:{app}/logs/bot.log
StandardError=append:{app}/logs/bot.log

[Install]
WantedBy=multi-user.target
""".format(app=app_dir, python=python)


def unit_backup_service(app_dir, python):
    return """[Unit]
Description=English Starter: backup progress to Telegram
After=network-online.target

[Service]
Type=oneshot
WorkingDirectory={app}
EnvironmentFile={app}/.env
ExecStart={python} {app}/bot.py --backup-now
""".format(app=app_dir, python=python)


def unit_backup_timer():
    return """[Unit]
Description=Daily English Starter backup

[Timer]
OnCalendar=*-*-* 20:00:00
Persistent=true

[Install]
WantedBy=timers.target
"""


def unit_health_service(app_dir, python):
    return """[Unit]
Description=English Starter: health check and self-healing
After=network-online.target

[Service]
Type=oneshot
WorkingDirectory={app}
EnvironmentFile={app}/.env
ExecStart={python} {app}/tools/health_check.py --restart-cmd "systemctl restart {svc}"
""".format(app=app_dir, python=python, svc=SERVICE)


def unit_health_timer():
    return """[Unit]
Description=Check English Starter every 5 minutes

[Timer]
OnBootSec=3min
OnUnitActiveSec=5min
Unit={svc}-healthcheck.service

[Install]
WantedBy=timers.target
""".format(svc=SERVICE)


def write_file(path, content, mode=None, dry=False):
    if dry:
        print("    [dry-run] записал бы %s (%d байт)" % (path, len(content)))
        return
    with open(path, "w", encoding="utf-8") as handle:
        handle.write(content)
    if mode is not None:
        os.chmod(path, mode)


def run(command, dry=False):
    printable = command if isinstance(command, str) else " ".join(command)
    if dry:
        print("    [dry-run] выполнил бы: %s" % printable)
        return 0
    print("    $ %s" % printable)
    return subprocess.run(command, shell=isinstance(command, str)).returncode


def copy_project(source, target, dry=False):
    os.makedirs(target, exist_ok=True)
    for item in REQUIRED_FILES:
        src = os.path.join(source, item)
        dst = os.path.join(target, item)
        if not os.path.exists(src):
            continue
        if os.path.abspath(src) == os.path.abspath(dst):
            continue
        if dry:
            print("    [dry-run] скопировал бы %s -> %s" % (src, dst))
            continue
        if os.path.isdir(src):
            shutil.rmtree(dst, ignore_errors=True)
            shutil.copytree(src, dst)
        else:
            shutil.copy2(src, dst)
    for extra in ("deploy",):
        src = os.path.join(source, extra)
        if os.path.isdir(src):
            dst = os.path.join(target, extra)
            if os.path.abspath(src) != os.path.abspath(dst) and not dry:
                shutil.rmtree(dst, ignore_errors=True)
                shutil.copytree(src, dst)


def verify_telegram(token, timeout=25):
    url = "https://api.telegram.org/bot%s/getMe" % token
    try:
        with urllib.request.urlopen(url, timeout=timeout) as response:
            body = response.read().decode("utf-8", "replace")
        return True, body[:200]
    except urllib.error.HTTPError as err:
        return False, "HTTP %s: %s" % (err.code, err.read().decode("utf-8", "replace")[:200])
    except Exception as err:
        return False, str(err)


def main(argv=None):
    parser = argparse.ArgumentParser(description="Установка English Starter на сервер")
    parser.add_argument("token", help="токен бота от @BotFather")
    parser.add_argument("--app-dir", default=DEFAULT_APP_DIR, help="каталог установки")
    parser.add_argument("--dry-run", action="store_true", help="только показать действия")
    parser.add_argument("--no-systemd", action="store_true", help="не трогать systemd")
    args = parser.parse_args(argv)

    app_dir = os.path.abspath(args.app_dir)
    dry = args.dry_run

    print("=" * 70)
    print("УСТАНОВКА ENGLISH STARTER  %s" % ("(ПРОВЕРКА, без изменений)" if dry else ""))
    print("=" * 70)
    print("  каталог установки: %s" % app_dir)
    print("  исходники:         %s" % SOURCE_DIR)
    print()

    if not py_version_ok():
        return fail("нужен Python 3.8+, найден %s" % sys.version.split()[0])

    if not dry and hasattr(os, "geteuid") and os.geteuid() != 0:
        return fail("запустите от root: sudo python3 deploy/vps_install.py <ТОКЕН>")

    missing = [item for item in REQUIRED_FILES if not os.path.exists(os.path.join(SOURCE_DIR, item))]
    if missing:
        return fail("в проекте нет файлов: %s" % ", ".join(missing))

    log("1/7 Проверяю Python и файлы проекта")
    print("    python: %s" % sys.executable)
    print("    версия: %s" % sys.version.split()[0])

    log("2/7 Копирую проект в %s" % app_dir)
    copy_project(SOURCE_DIR, app_dir, dry=dry)
    for directory in ("data", "logs"):
        path = os.path.join(app_dir, directory)
        if dry:
            print("    [dry-run] создал бы каталог %s" % path)
        else:
            os.makedirs(path, exist_ok=True)

    log("3/7 Пишу .env с токеном")
    env_body = "\n".join([
        "BOT_TOKEN=%s" % args.token,
        "DB_PATH=%s/data/bot.db" % app_dir,
        "AUTO_BACKUP=1",
        "",
    ])
    write_file(os.path.join(app_dir, ".env"), env_body, mode=0o600, dry=dry)

    log("4/7 Переношу прогресс, если приехал снимок базы")
    snapshot = os.path.join(app_dir, "data", "deploy-snapshot.db")
    live = os.path.join(app_dir, "data", "bot.db")
    if os.path.exists(snapshot) and not os.path.exists(live):
        if dry:
            print("    [dry-run] перенёс бы снимок базы в %s" % live)
        else:
            shutil.move(snapshot, live)
            print("    база с прогрессом перенесена")
    else:
        print("    снимка нет или база уже на месте (ничего не делаю)")
    for stale in ("bot.lock", "bot.pid", "conflict.flag"):
        path = os.path.join(app_dir, "data", stale)
        if os.path.exists(path) and not dry:
            os.remove(path)

    log("5/7 Проверяю контент курса")
    code = run([sys.executable, os.path.join(app_dir, "bot.py"), "--check"], dry=dry)
    if code != 0:
        return fail("проверка контента не прошла")

    log("6/7 Ставлю systemd-юниты (автозапуск, бэкапы, самовосстановление)")
    units = {
        "%s.service" % SERVICE: unit_service(app_dir, sys.executable),
        "%s.service" % BACKUP: unit_backup_service(app_dir, sys.executable),
        "%s.timer" % BACKUP: unit_backup_timer(),
        "%s.service" % HEALTHCHECK: unit_health_service(app_dir, sys.executable),
        "%s.timer" % HEALTHCHECK: unit_health_timer(),
    }
    target_dir = UNIT_DIR if not dry else os.path.join(app_dir, "dry-run-units")
    if dry:
        os.makedirs(target_dir, exist_ok=True)
    for name, body in units.items():
        write_file(os.path.join(target_dir, name), body, dry=False)

    if not dry and not args.no_systemd:
        run(["systemctl", "daemon-reload"])
        run(["systemctl", "enable", "--now", "%s.service" % SERVICE])
        run(["systemctl", "enable", "--now", "%s.timer" % BACKUP])
        run(["systemctl", "enable", "--now", "%s.timer" % HEALTHCHECK])
    else:
        print("    [dry-run] включил бы сервис и таймеры")

    log("7/7 Проверяю, что бот запустился и видит Telegram")
    if dry:
        print("    [dry-run] проверил бы getMe и статус сервиса")
        print()
        print("ГОТОВО (проверка). Юниты лежат в %s" % target_dir)
        return 0

    time.sleep(6)
    ok, body = verify_telegram(args.token)
    print("    Telegram ответил: %s" % body)
    status = subprocess.run(["systemctl", "is-active", "%s.service" % SERVICE],
                            capture_output=True, text=True).stdout.strip()
    print("    сервис: %s" % (status or "нет ответа"))
    timers = subprocess.run(["systemctl", "list-timers", "--no-pager"],
                            capture_output=True, text=True).stdout
    for line in timers.splitlines():
        if "english-starter" in line:
            print("    таймер: %s" % " ".join(line.split()))

    if ok and status == "active":
        print()
        print("ГОТОВО: бот работает круглосуточно, поднимется сам после перезагрузки,")
        print("зависание лечится автопроверкой каждые 5 минут, копии — ежедневно в 20:00.")
        print()
        print("Полезные команды на сервере:")
        print("  systemctl status %s" % SERVICE)
        print("  journalctl -u %s -f" % SERVICE)
        print("  tail -f %s/logs/bot.log" % app_dir)
        print("  systemctl restart %s" % SERVICE)
        return 0

    return fail("бот не поднялся — смотрите: journalctl -u %s -n 50" % SERVICE)


if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    sys.exit(main())
