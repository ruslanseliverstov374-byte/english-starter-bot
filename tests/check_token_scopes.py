# -*- coding: utf-8 -*-
"""Диагностика прав токена GitHub: что можно читать и что можно писать."""

import base64
import json
import sys
import urllib.error
import urllib.request

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

TOKEN_FILE = "data/github_token.txt"
OWNER = "ruslanseliverstov374-byte"
REPO = "english-starter-bot"
token = open(TOKEN_FILE, encoding="utf-8").read().strip()


def try_request(method, path, payload=None):
    data = json.dumps(payload).encode() if payload else None
    request = urllib.request.Request(
        "https://api.github.com" + path, data=data, method=method,
        headers={"Authorization": "Bearer %s" % token,
                 "Accept": "application/vnd.github+json",
                 "User-Agent": "english-starter-bot"})
    try:
        with urllib.request.urlopen(request, timeout=40) as response:
            return response.status, ""
    except urllib.error.HTTPError as error:
        return error.code, error.read().decode("utf-8", "replace")[:160]


print("1) чтение кода (GET contents/bot.py):      ", try_request("GET", "/repos/%s/%s/contents/bot.py" % (OWNER, REPO))[0])
print("2) запись кода (PUT .probe):              ", try_request(
    "PUT", "/repos/%s/%s/contents/.probe" % (OWNER, REPO),
    {"message": "probe", "content": base64.b64encode(b"x").decode(), "branch": "main"})[0])
print("3) запись воркфлоу (PUT .github/...):     ", try_request(
    "PUT", "/repos/%s/%s/contents/.github/workflows/.probe.yml" % (OWNER, REPO),
    {"message": "probe", "content": base64.b64encode(b"name: probe\n").decode(), "branch": "main"})[0])
print()
print("Расшифровка: 200/201 — право есть, 403 — права нет, 404/422 — файла нет (это норма для проб)")
