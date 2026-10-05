# -*- coding: utf-8 -*-
"""Проверка токена GitHub: кто мы и есть ли доступ к репозиторию."""

import json
import sys
import urllib.request

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

TOKEN_FILE = "data/github_token.txt"
OWNER = "ruslanseliverstov374-byte"
REPO = "english-starter-bot"

token = open(TOKEN_FILE, encoding="utf-8").read().strip()
print("токен: %s...%s (%d символов)" % (token[:12], token[-4:], len(token)))


def api(path):
    request = urllib.request.Request(
        "https://api.github.com" + path,
        headers={
            "Authorization": "Bearer %s" % token,
            "Accept": "application/vnd.github+json",
            "User-Agent": "english-starter-bot",
        },
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.loads(response.read().decode("utf-8"))


try:
    user = api("/user")
    print("аккаунт: %s" % user.get("login"))
except Exception as error:
    print("❌ токен не работает: %s" % error)
    sys.exit(1)

try:
    repo = api("/repos/%s/%s" % (OWNER, REPO))
    print("репозиторий: %s (ветка %s)" % (repo.get("full_name"), repo.get("default_branch")))
except Exception as error:
    print("❌ нет доступа к репозиторию: %s" % error)
    sys.exit(1)

try:
    head = api("/repos/%s/%s/commits/main" % (OWNER, REPO))
    print("последний коммит: %s — %s" % (head["sha"][:8], head["commit"]["message"].splitlines()[0]))
except Exception as error:
    print("коммиты недоступны: %s" % error)

# проверяем право на запись: пробуем создать/обновить служебный файл
try:
    import base64
    body = json.dumps({
        "message": "Проверка прав записи (можно удалить)",
        "content": base64.b64encode("test\n".encode()).decode(),
        "branch": "main",
    }).encode()
    request = urllib.request.Request(
        "https://api.github.com/repos/%s/%s/contents/.write-test" % (OWNER, REPO),
        data=body, method="PUT",
        headers={"Authorization": "Bearer %s" % token,
                 "Accept": "application/vnd.github+json",
                 "User-Agent": "english-starter-bot"},
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        result = json.loads(response.read().decode())
    print("✅ право на запись есть (создан .write-test, sha %s)" % result["content"]["sha"][:8])
except Exception as error:
    print("❌ нет права на запись: %s" % error)
