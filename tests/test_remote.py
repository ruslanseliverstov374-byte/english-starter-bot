# -*- coding: utf-8 -*-
"""Проверка внешнего хранилища снимков (бесплатный хостинг без постоянного диска).

Поднимает локальный HTTP-сервер, работающий как Upstash REST, и проверяет:
  * отправку снимка базы;
  * восстановление базы, когда локальный файл пропал (имитация перезапуска контейнера);
  * что бот не падает, когда внешнее хранилище пустое или недоступно.

Запуск:  python tests/test_remote.py
"""

import json
import os
import shutil
import sys
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE)

from remote_store import RemoteSnapshot, SnapshotUploader, restore_if_needed   # noqa: E402
from store import Store                                                        # noqa: E402

FAILURES = []
STORE = {}


def check(condition, message):
    print(("  ✅ " if condition else "  ❌ ") + message)
    if not condition:
        FAILURES.append(message)
    return condition


class KvHandler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def _send(self, payload):
        body = json.dumps(payload).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self):
        length = int(self.headers.get("Content-Length") or 0)
        raw = self.rfile.read(length) if length else b""
        path = self.path.strip("/")
        if path.startswith("set/"):
            STORE[path[4:]] = raw.decode("ascii", "replace")
            self._send({"result": "OK"})
            return
        if path == "set":
            try:
                _, key, value = json.loads(raw.decode("utf-8"))
                STORE[key] = value
                self._send({"result": "OK"})
                return
            except Exception:
                self._send({"error": "bad command"})
                return
        self._send({"error": "unknown"})

    def do_GET(self):
        path = self.path.strip("/")
        if path.startswith("get/"):
            self._send({"result": STORE.get(path[4:])})
            return
        self._send({"error": "unknown"})

    def log_message(self, fmt, *args):
        return


def main():
    workdir = os.path.join(BASE, "tests", "_run", "remote")
    shutil.rmtree(workdir, ignore_errors=True)
    os.makedirs(workdir, exist_ok=True)
    # имя файла как у бота: data/bot.db - именно его ищет restore_if_needed
    db_path = os.path.join(workdir, "bot.db")
    for suffix in ("", "-wal", "-shm"):
        if os.path.exists(db_path + suffix):
            os.remove(db_path + suffix)

    server = ThreadingHTTPServer(("127.0.0.1", 0), KvHandler)
    port = server.server_address[1]
    threading.Thread(target=server.serve_forever, daemon=True).start()
    url = "http://127.0.0.1:%d" % port

    print("=" * 70)
    print("ПРОВЕРКА ВНЕШНЕГО ХРАНИЛИЩА СНИМКОВ (порт %d)" % port)
    print("=" * 70)

    logs = []
    remote = RemoteSnapshot(url=url, token="test-token", log=logs.append)
    check(remote.enabled, "хранилище включается, когда заданы адрес и токен")

    # создаём базу с «прогрессом»
    store = Store(db_path)
    store.ensure_user(111, "tester", "Тест")
    for word in ("hello", "hi", "good morning"):
        store.upsert_srs(111, word, learned=1, box=2)
    store.log_answer(111, "hello", "mc", True)
    users_before = len(store.all_users())
    srs_before = store.srs_counts(111)["total"]

    uploader = SnapshotUploader(store, remote, interval=1, log=logs.append)
    check(uploader.upload_now(), "снимок ушёл во внешнее хранилище")
    check(bool(STORE), "хранилище получило данные (%d КБ)" % (len(list(STORE.values())[0]) // 1024))
    store.close()

    # имитируем перезапуск бесплатного контейнера: диск пуст
    for suffix in ("", "-wal", "-shm"):
        if os.path.exists(db_path + suffix):
            os.remove(db_path + suffix)
    check(not os.path.exists(db_path), "локальная база удалена (как при перезапуске Render)")

    restored = restore_if_needed(workdir, remote, log=logs.append)
    check(restored, "база восстановлена из внешнего хранилища автоматически")

    store2 = Store(db_path)
    check(len(store2.all_users()) == users_before,
          "ученики на месте: %d" % len(store2.all_users()))
    check(store2.srs_counts(111)["total"] == srs_before,
          "прогресс повторения на месте: %d слов" % store2.srs_counts(111)["total"])
    check(store2.get_user(111)["first_name"] == "Тест", "данные ученика не потерялись")
    store2.close()

    # когда локальная база есть - восстановление не трогает её
    check(not restore_if_needed(workdir, remote, log=logs.append),
          "существующая база не перезаписывается")

    # пустое хранилище
    empty = RemoteSnapshot(url=url, token="test", key="нет-такого-ключа", log=logs.append)
    check(not empty.download(os.path.join(workdir, "none.db")), "пустой снимок не скачивается")

    # недоступное хранилище не ломает бота
    broken = RemoteSnapshot(url="http://127.0.0.1:9", token="x", log=logs.append)
    check(not broken.upload(db_path), "недоступное хранилище: отправка возвращает False без падения")
    check(not broken.download(os.path.join(workdir, "x.db")), "недоступное хранилище: скачивание False")

    # выключенное хранилище - просто молчит
    off = RemoteSnapshot(url="", token="", log=logs.append)
    check(not off.enabled and not off.upload(db_path), "без настроек хранилище отключено")

    server.shutdown()

    print()
    if FAILURES:
        print("РЕЗУЛЬТАТ: %d ПРОВЕРОК ПРОВАЛЕНО" % len(FAILURES))
        for failure in FAILURES:
            print("  - %s" % failure)
        return 1
    print("РЕЗУЛЬТАТ: ВСЕ ПРОВЕРКИ ПРОЙДЕНЫ ✅")
    return 0


if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    sys.exit(main())
