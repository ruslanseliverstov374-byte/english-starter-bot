#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Собирает архив проекта для загрузки на GitHub (без секретов и личных данных).

Запуск:  python tools/make_github_zip.py
Результат: english-bot-github.zip рядом с проектом

Пути внутри архива всегда со слэшами "/" - так его одинаково правильно
распакуют и Windows, и macOS, и Linux.
"""

import os
import sys
import zipfile

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT = os.path.join(os.path.dirname(BASE), "english-bot-github.zip")

SKIP_DIRS = {"data", "logs", "__pycache__", ".git", "_run", ".pytest_cache"}
SKIP_FILES = {"token.txt", ".env"}
SKIP_SUFFIX = (".pyc", ".log", ".db", ".db-wal", ".db-shm", ".stored")
SKIP_PREFIX = ("vps_key",)


def include(relative):
    parts = relative.replace("\\", "/").split("/")
    if any(part in SKIP_DIRS for part in parts):
        return False
    name = parts[-1]
    if name in SKIP_FILES or name.startswith(SKIP_PREFIX):
        return False
    if name.lower().endswith(SKIP_SUFFIX):
        return False
    if name == os.path.basename(OUTPUT):
        return False
    return True


def main():
    added = []
    with zipfile.ZipFile(OUTPUT, "w", zipfile.ZIP_DEFLATED) as archive:
        for root, dirs, files in os.walk(BASE):
            dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
            for name in files:
                full = os.path.join(root, name)
                relative = os.path.relpath(full, BASE).replace("\\", "/")
                if not include(relative):
                    continue
                archive.write(full, relative)
                added.append(relative)

    print("Создан: %s (%.0f КБ, %d файлов)" % (OUTPUT, os.path.getsize(OUTPUT) / 1024.0, len(added)))

    suspicious = [name for name in added
                  if name.endswith(".db") or name.endswith(".env")
                  or "token" in name.lower() or "vps_key" in name.lower()]
    print()
    if suspicious:
        print("[!] Проверьте: %s" % ", ".join(suspicious))
    else:
        print("✅ Токенов, ключей и баз данных в архиве нет")

    print()
    print("Папки первого уровня:")
    tops = sorted({name.split("/")[0] for name in added})
    for top in tops:
        count = len([name for name in added if name.split("/")[0] == top])
        print("  %-12s %d файл(ов)" % (top, count))
    return 0


if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    sys.exit(main())
