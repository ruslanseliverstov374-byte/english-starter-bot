#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Публикует файлы проекта в GitHub через API (без git и без паролей).

Сравнивает локальные файлы с содержимым репозитория по git-хэшу блоба и
отправляет только изменения. Токен берётся из data/github_token.txt или
переменной GITHUB_TOKEN (в архив и в репозиторий токен не попадает).

Запуск:
    python tools/push_to_github.py                  # отправить изменения
    python tools/push_to_github.py --dry-run        # только показать, что изменится
"""

import argparse
import base64
import hashlib
import json
import os
import sys
import urllib.error
import urllib.request

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE)

from tools.make_github_zip import include          # noqa: E402  (единый список исключений)

TOKEN_FILE = os.path.join(BASE, "data", "github_token.txt")
OWNER = os.environ.get("GITHUB_OWNER", "ruslanseliverstov374-byte")
REPO = os.environ.get("GITHUB_REPO", "english-starter-bot")
BRANCH = "main"
API = "https://api.github.com"


def log(message):
    print(message)


def token_value():
    value = os.environ.get("GITHUB_TOKEN")
    if value:
        return value.strip()
    if os.path.exists(TOKEN_FILE):
        return open(TOKEN_FILE, encoding="utf-8").read().strip()
    return ""


class GitHub:
    def __init__(self, token):
        self.token = token

    def request(self, method, path, payload=None):
        data = json.dumps(payload).encode("utf-8") if payload is not None else None
        request = urllib.request.Request(
            API + path, data=data, method=method,
            headers={
                "Authorization": "Bearer %s" % self.token,
                "Accept": "application/vnd.github+json",
                "User-Agent": "english-starter-bot",
                "Content-Type": "application/json",
            },
        )
        try:
            with urllib.request.urlopen(request, timeout=60) as response:
                body = response.read().decode("utf-8")
            return json.loads(body) if body else {}
        except urllib.error.HTTPError as error:
            detail = error.read().decode("utf-8", "replace")[:300]
            raise RuntimeError("GitHub API %s %s -> HTTP %s: %s" % (method, path, error.code, detail))

    # ---------- вспомогательное ----------

    def remote_tree(self):
        data = self.request("GET", "/repos/%s/%s/git/trees/%s?recursive=1" % (OWNER, REPO, BRANCH))
        return {item["path"]: item["sha"] for item in data.get("tree", []) if item["type"] == "blob"}

    def put_file(self, path, content_bytes, sha, message):
        payload = {
            "message": message,
            "content": base64.b64encode(content_bytes).decode("ascii"),
            "branch": BRANCH,
        }
        if sha:
            payload["sha"] = sha
        return self.request("PUT", "/repos/%s/%s/contents/%s" % (OWNER, REPO, path), payload)

    def delete_file(self, path, sha, message):
        return self.request("DELETE", "/repos/%s/%s/contents/%s" % (OWNER, REPO, path),
                            {"message": message, "sha": sha, "branch": BRANCH})


def local_blob_sha(data):
    """git считает хэш блоба как sha1('blob <размер>\\0' + содержимое)."""
    header = ("blob %d\0" % len(data)).encode("ascii")
    return hashlib.sha1(header + data).hexdigest()


def collect_local():
    files = {}
    for root, dirs, names in os.walk(BASE):
        dirs[:] = [d for d in dirs
                   if d not in {"data", "logs", "__pycache__", ".git", "_run", ".pytest_cache"}]
        for name in names:
            full = os.path.join(root, name)
            relative = os.path.relpath(full, BASE).replace("\\", "/")
            if not include(relative):
                continue
            with open(full, "rb") as handle:
                files[relative] = handle.read()
    return files


def main(argv=None):
    parser = argparse.ArgumentParser(description="Публикация проекта в GitHub")
    parser.add_argument("--dry-run", action="store_true", help="только показать изменения")
    parser.add_argument("--message", default="Обновление бота: копии в Telegram, сторож, напоминания")
    parser.add_argument("--prune", action="store_true",
                        help="удалить из репозитория файлы, которых нет локально")
    args = parser.parse_args(argv)

    token = token_value()
    if not token:
        log("Нет токена: положите его в data/github_token.txt или задайте GITHUB_TOKEN")
        return 2

    github = GitHub(token)
    local = collect_local()
    remote = github.remote_tree()
    log("локально файлов: %d | в репозитории: %d" % (len(local), len(remote)))

    changed, added = [], []
    for path, data in sorted(local.items()):
        sha = local_blob_sha(data)
        if path not in remote:
            added.append(path)
        elif remote[path] != sha:
            changed.append(path)

    orphaned = [path for path in remote if path not in local]

    log("")
    log("новые файлы (%d): %s" % (len(added), ", ".join(added) or "—"))
    log("изменённые (%d): %s" % (len(changed), ", ".join(changed) or "—"))
    log("только в репозитории (%d): %s" % (len(orphaned), ", ".join(orphaned) or "—"))

    if args.dry_run:
        log("")
        log("(dry-run: ничего не отправлено)")
        return 0

    sent = 0
    failures = []
    for path in added + changed:
        try:
            github.put_file(path, local[path], remote.get(path), args.message)
            sent += 1
            log("  ↑ %s" % path)
        except RuntimeError as error:
            failures.append(path)
            hint = ""
            if path.startswith(".github/workflows/"):
                hint = (" — у токена нет права «Workflows: Read and write». "
                        "Добавьте его в настройках токена или настройте пинг иначе.")
            log("  ! %s: %s%s" % (path, error, hint))

    if args.prune:
        for path in orphaned:
            try:
                github.delete_file(path, remote[path], "Удаление устаревшего файла")
                log("  ✗ %s" % path)
            except RuntimeError as error:
                log("  ! не удалось удалить %s: %s" % (path, error))

    log("")
    log("ГОТОВО: отправлено файлов %d, не удалось %d" % (sent, len(failures)))
    if failures:
        log("не отправлены: %s" % ", ".join(failures))
    return 1 if failures else 0


if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    sys.exit(main())
