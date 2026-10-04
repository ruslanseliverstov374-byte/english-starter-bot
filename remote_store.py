# -*- coding: utf-8 -*-
"""Внешнее хранилище снимков базы - чтобы прогресс выжил на бесплатном хостинге.

У бесплатных тарифов (Render, Railway и подобных) файловая система временная:
контейнер перезапустили - data/bot.db пропала. Поэтому раз в несколько минут бот
отправляет снимок базы в простое внешнее key-value хранилище, а при старте -
забирает его обратно, если локальной базы нет.

Поддерживается любой сервис с REST-API в стиле Upstash Redis:

    SET:  POST {url}/set/{key}   тело = значение,  Authorization: Bearer {token}
    GET:  GET  {url}/get/{key}                      Authorization: Bearer {token}
    ответ: {"result": "..."} (или {"result": null}, если ключа нет)

Подходит бесплатный тариф Upstash (без карты) или любой совместимый сервис.
Если переменные не заданы - модуль молчит и ничего не делает (бот работает как обычно).
"""

import base64
import gzip
import json
import os
import time
import urllib.error
import urllib.request


class RemoteSnapshot:
    def __init__(self, url=None, token=None, key="english-starter-db", timeout=30, log=None):
        self.url = (url or "").rstrip("/")
        self.token = token or ""
        self.key = key
        self.timeout = timeout
        self.log = log or (lambda message: None)
        self.enabled = bool(self.url and self.token)

    # ---------- низкий уровень ----------

    def _request(self, method, path, body=None):
        request = urllib.request.Request(
            "%s/%s" % (self.url, path.lstrip("/")),
            data=body,
            method=method,
            headers={
                "Authorization": "Bearer %s" % self.token,
                "Content-Type": "application/octet-stream",
            },
        )
        with urllib.request.urlopen(request, timeout=self.timeout) as response:
            return response.read()

    def _pack(self, path):
        with open(path, "rb") as handle:
            raw = handle.read()
        packed = gzip.compress(raw, 6)
        return base64.b64encode(packed).decode("ascii"), len(raw), len(packed)

    def _unpack(self, payload, destination):
        if isinstance(payload, str):
            payload = payload.encode("utf-8")
        data = gzip.decompress(base64.b64decode(payload))
        if not data.startswith(b"SQLite format 3"):
            raise ValueError("данные не похожи на базу SQLite")
        with open(destination, "wb") as handle:
            handle.write(data)
        return len(data)

    # ---------- операции ----------

    def _set(self, payload):
        """Пробует два способа записи: значение в теле и команда JSON-массивом."""
        value = payload.encode("ascii")
        try:
            response = self._request("POST", "set/%s" % self.key, body=value)
            if b"OK" in response[:80]:
                return True
        except urllib.error.HTTPError:
            pass
        command = json.dumps(["SET", self.key, payload]).encode("utf-8")
        response = self._request("POST", "set", body=command)
        return b"OK" in response[:80]

    def upload(self, file_path):
        if not self.enabled or not os.path.exists(file_path):
            return False
        try:
            payload, raw_size, packed_size = self._pack(file_path)
            if not self._set(payload):
                self.log("внешнее хранилище не подтвердило запись снимка")
                return False
            self.log("снимок базы отправлен во внешнее хранилище: %d КБ -> %d КБ" % (
                raw_size // 1024, packed_size // 1024))
            return True
        except urllib.error.HTTPError as err:
            detail = ""
            try:
                detail = err.read().decode("utf-8", "replace")[:200]
            except Exception:
                pass
            self.log("не удалось отправить снимок: HTTP %s %s" % (err.code, detail))
            return False
        except Exception as err:
            self.log("не удалось отправить снимок: %s" % err)
            return False

    def download(self, destination):
        """Забирает снимок. True - база восстановлена."""
        if not self.enabled:
            return False
        try:
            raw = self._request("GET", "get/%s" % self.key)
            try:
                payload = json.loads(raw.decode("utf-8")).get("result")
            except ValueError:
                payload = raw.decode("utf-8", "replace").strip()
            if not payload:
                self.log("во внешнем хранилище снимка нет")
                return False
            size = self._unpack(payload, destination)
            self.log("база восстановлена из внешнего хранилища: %d КБ" % (size // 1024))
            return True
        except urllib.error.HTTPError as err:
            self.log("не удалось получить снимок: HTTP %s" % err.code)
            return False
        except Exception as err:
            self.log("не удалось получить снимок: %s" % err)
            return False

    def has_snapshot(self):
        if not self.enabled:
            return False
        try:
            raw = self._request("GET", "get/%s" % self.key)
            payload = json.loads(raw.decode("utf-8")).get("result")
            return bool(payload)
        except Exception:
            return False


def snapshot_paths(data_dir):
    return {
        "live": os.path.join(data_dir, "bot.db"),
        "temp": os.path.join(data_dir, "remote-snapshot.db"),
    }


def restore_if_needed(data_dir, remote, log=None):
    """Если локальной базы нет, а во внешнем хранилище снимок есть - восстанавливаем."""
    log = log or (lambda message: None)
    paths = snapshot_paths(data_dir)
    live = paths["live"]
    if not remote.enabled:
        return False
    if os.path.exists(live) and os.path.getsize(live) > 4096:
        log("локальная база на месте, восстановление не нужно")
        return False
    ok = remote.download(paths["temp"])
    if not ok:
        return False
    try:
        os.replace(paths["temp"], live)
        log("прогресс восстановлен из внешнего хранилища")
        return True
    except OSError as err:
        log("не удалось заменить базу: %s" % err)
        return False


class SnapshotUploader:
    """Фоновый поток: раз в N секунд отправляет снимок базы во внешнее хранилище."""

    def __init__(self, store, remote, interval=600, log=None):
        self.store = store
        self.remote = remote
        self.interval = interval
        self.log = log or (lambda message: None)
        self.stopping = False
        self.thread = None
        self.last_upload_at = 0.0

    def upload_now(self):
        if not self.remote.enabled:
            return False
        temp = os.path.join(os.path.dirname(self.store.path), "upload-snapshot.db")
        try:
            self.store.snapshot(temp)
            ok = self.remote.upload(temp)
            if ok:
                self.last_upload_at = time.time()
                self.store.set_meta("last_remote_upload", str(int(self.last_upload_at)))
            return ok
        except Exception as err:
            self.log("ошибка отправки снимка: %s" % err)
            return False
        finally:
            if os.path.exists(temp):
                try:
                    os.remove(temp)
                except OSError:
                    pass

    def upload_in_background(self):
        """Не блокирует обработку сообщений: отправка идёт в отдельном потоке."""
        if not self.remote.enabled:
            return
        import threading
        threading.Thread(target=self.upload_now, daemon=True).start()

    def loop(self):
        # первый снимок - через минуту после старта, чтобы не мешать запуску
        time.sleep(60)
        while not self.stopping:
            if time.time() - self.last_upload_at >= self.interval:
                self.upload_now()
            time.sleep(30)

    def start(self):
        if not self.remote.enabled or self.thread:
            return
        import threading
        self.thread = threading.Thread(target=self.loop, daemon=True)
        self.thread.start()
