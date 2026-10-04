# -*- coding: utf-8 -*-
"""Нагрузочный тест: сколько ресурсов нужно боту на N активных учеников.

Запуск:  python tests/stress.py [пользователей] [дней]

Что измеряет:
  * память процесса до и после (working set);
  * процессорное время на одно действие и на один урок;
  * скорость обработки (действий в секунду) - сколько выдержит бот;
  * рост базы данных: байт на ученика за день -> прогноз на весь курс (84 дня);
  * отсутствие ошибок при одновременной работе всех пользователей.
"""

import ctypes
import os
import random
import sqlite3
import sys
import time

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE)
sys.path.insert(0, os.path.join(BASE, "tests"))

import bot as botmod                       # noqa: E402
import simulate as S                       # noqa: E402

USERS = int(sys.argv[1]) if len(sys.argv) > 1 else 30
DAYS = int(sys.argv[2]) if len(sys.argv) > 2 else 2
CORRECT_PROBABILITY = 0.8
MESSAGES_PER_LESSON_ESTIMATE = 34          # ~34 сообщения на урок (карточки + упражнения)


def rss_mb():
    """Память текущего процесса в МБ."""
    if os.name == "nt":
        class Counters(ctypes.Structure):
            _fields_ = [
                ("cb", ctypes.c_uint32), ("PageFaultCount", ctypes.c_uint32),
                ("PeakWorkingSetSize", ctypes.c_size_t), ("WorkingSetSize", ctypes.c_size_t),
                ("QuotaPeakPagedPoolUsage", ctypes.c_size_t), ("QuotaPagedPoolUsage", ctypes.c_size_t),
                ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t), ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
                ("PagefileUsage", ctypes.c_size_t), ("PeakPagefileUsage", ctypes.c_size_t),
            ]
        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        psapi = ctypes.WinDLL("psapi", use_last_error=True)
        kernel32.GetCurrentProcess.restype = ctypes.c_void_p
        psapi.GetProcessMemoryInfo.argtypes = [ctypes.c_void_p, ctypes.POINTER(Counters), ctypes.c_uint32]
        psapi.GetProcessMemoryInfo.restype = ctypes.c_int
        counters = Counters()
        counters.cb = ctypes.sizeof(counters)
        if not psapi.GetProcessMemoryInfo(kernel32.GetCurrentProcess(), ctypes.byref(counters),
                                          counters.cb):
            return -1.0
        return counters.WorkingSetSize / 1048576.0
    import resource
    return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024.0


class MultiFakeTg(S.FakeTg):
    """Заглушка Telegram с отдельной клавиатурой для каждого чата."""

    def __init__(self):
        super().__init__()
        self.current_by_chat = {}

    def send_message(self, chat_id, text, reply_markup=None, **kwargs):
        message = super().send_message(chat_id, text, reply_markup=reply_markup, **kwargs)
        if reply_markup:
            self.current_by_chat[chat_id] = message
        return message

    def edit_message(self, chat_id, message_id, text, reply_markup=None, **kwargs):
        record = super().edit_message(chat_id, message_id, text, reply_markup=reply_markup, **kwargs)
        current = self.current_by_chat.get(chat_id)
        if reply_markup is not None:
            if current and current["message_id"] == message_id:
                current["reply_markup"] = reply_markup
                current["text"] = text
            else:
                self.current_by_chat[chat_id] = {
                    "message_id": message_id, "chat_id": chat_id,
                    "text": text, "reply_markup": reply_markup,
                }
        return record


def buttons_for(fake, chat_id):
    message = fake.current_by_chat.get(chat_id)
    if not message or not message.get("reply_markup"):
        return []
    keyboard = message["reply_markup"].get("inline_keyboard") or []
    return [b.get("callback_data", "") for row in keyboard for b in row if b.get("callback_data")]


def message(chat_id, text):
    return {
        "update_id": 1,
        "message": {"message_id": 1, "chat": {"id": chat_id, "type": "private"},
                    "from": {"id": chat_id, "username": "u%d" % chat_id, "first_name": "Ученик %d" % chat_id},
                    "text": text},
    }


def press(chat_id, data, fake=None):
    """Нажатие кнопки. Если известна текущая клавиатура чата - берём её message_id,
    как это делает настоящий Telegram."""
    message_id = 1
    if fake is not None:
        current = fake.current_by_chat.get(chat_id) or {}
        message_id = current.get("message_id", 1)
    return {
        "update_id": 2,
        "callback_query": {"id": "cb-%s-%s" % (chat_id, data),
                           "from": {"id": chat_id},
                           "message": {"message_id": message_id,
                                       "chat": {"id": chat_id, "type": "private"}},
                           "data": data},
    }


def one_action(bot, fake, chat_id, rng):
    """Одно действие ученика. True - что-то сделали, False - занятие закончилось."""
    session = (bot.state(chat_id) or {}).get("session")
    if session and session.get("await"):
        question = session["questions"][session["qi"]]
        answer = question["answer"] if rng.random() < CORRECT_PROBABILITY else "чепуха"
        bot.handle_update(message(chat_id, answer))
        return True

    available = buttons_for(fake, chat_id)
    if not available:
        return False

    def find(prefix):
        for data in available:
            if data.startswith(prefix):
                return data
        return None

    answer_button = find("a|")
    if answer_button:
        parts = answer_button.split("|")
        question = session["questions"][int(parts[1])]
        if rng.random() < CORRECT_PROBABILITY:
            chosen = "a|%s|%d" % (parts[1], question["correct"])
        else:
            wrong = [i for i in range(len(question["options"])) if i != question["correct"]]
            chosen = "a|%s|%d" % (parts[1], rng.choice(wrong))
        bot.handle_update(press(chat_id, chosen, fake))
        return True

    for prefix in ("c|show|", "c|next|", "n|", "s|next|", "go|lesson"):
        data = find(prefix)
        if data:
            bot.handle_update(press(chat_id, data, fake))
            return True

    grade = find("c|g|")
    if grade:
        parts = grade.split("|")
        value = 1 if rng.random() < CORRECT_PROBABILITY else 0
        bot.handle_update(press(chat_id, "c|g|%s|%d" % (parts[2], value), fake))
        return True

    for prefix in ("onb|mode|light", "onb|time|09:00", "onb|tz|180"):
        if prefix in available:
            bot.handle_update(press(chat_id, prefix, fake))
            return True

    if available:
        bot.handle_update(press(chat_id, available[0], fake))
        return True
    return False


def main():
    botmod.log = lambda text: None
    rng = random.Random(7)

    workdir = os.path.join(BASE, "tests", "_run")
    os.makedirs(workdir, exist_ok=True)
    db_path = os.path.join(workdir, "stress.db")
    for suffix in ("", "-journal", "-wal"):
        if os.path.exists(db_path + suffix):
            os.remove(db_path + suffix)

    bot = botmod.Bot("111:STRESS", db_path=db_path)
    fake = MultiFakeTg()
    bot.tg = fake
    bot.me = fake.get_me()

    users = [700000000 + i for i in range(USERS)]

    print("=" * 74)
    print("НАГРУЗОЧНЫЙ ТЕСТ: %d учеников, %d дня занятий" % (USERS, DAYS))
    print("=" * 74)

    rss_start = rss_mb()
    cpu_start = time.process_time()
    wall_start = time.time()

    # онбординг всех учеников
    for chat_id in users:
        bot.handle_update(message(chat_id, "/start"))
        bot.handle_update(press(chat_id, "onb|mode|light", fake))
        bot.handle_update(press(chat_id, "onb|time|09:00", fake))
        bot.handle_update(press(chat_id, "onb|tz|180", fake))

    actions = 0
    lessons_done = 0
    errors = 0

    for day in range(1, DAYS + 1):
        for chat_id in users:
            S.shift_time_back_one_day(bot.store, chat_id)
            bot.handle_update(message(chat_id, "/today"))

        # круговорот: все ученики работают «одновременно», по одному действию за проход
        active = set(users)
        guard = 0
        while active and guard < 20000:
            guard += 1
            for chat_id in list(active):
                session = (bot.state(chat_id) or {}).get("session")
                if not session:
                    active.discard(chat_id)
                    lessons_done += 1
                    continue
                try:
                    if not one_action(bot, fake, chat_id, rng):
                        active.discard(chat_id)
                        lessons_done += 1
                    else:
                        actions += 1
                except Exception as error:                 # noqa: BLE001
                    errors += 1
                    if errors <= 3:
                        print("  ошибка у %s: %s" % (chat_id, error))
                    active.discard(chat_id)
        print("  день %d: занятий завершено %d, действий %d" % (day, lessons_done, actions))

    wall = time.time() - wall_start
    cpu = time.process_time() - cpu_start
    rss_end = rss_mb()

    conn = sqlite3.connect(db_path)
    rows = {table: conn.execute("SELECT COUNT(*) FROM %s" % table).fetchone()[0]
            for table in ("users", "srs", "answers")}
    conn.close()
    db_bytes = os.path.getsize(db_path)

    per_user_bytes = db_bytes / float(USERS)
    per_user_day_bytes = per_user_bytes / float(DAYS)
    course_bytes = per_user_day_bytes * 84

    print()
    print("РЕЗУЛЬТАТЫ")
    print("-" * 74)
    print("  действий всего ............ %d" % actions)
    print("  занятий завершено ......... %d" % lessons_done)
    print("  ошибок .................... %d" % errors)
    print("  сообщений отправлено ...... %d" % len(fake.sent))
    print("  общее время ............... %.1f с" % wall)
    print("  процессорное время ........ %.1f с" % cpu)
    print("  действий в секунду ........ %.0f" % (actions / wall if wall else 0))
    print("  процессор на действие ..... %.2f мс" % (1000.0 * cpu / actions if actions else 0))
    print("  процессор на урок ......... %.0f мс" % (1000.0 * cpu / lessons_done if lessons_done else 0))
    print("  сообщений в секунду ....... %.0f" % (len(fake.sent) / wall if wall else 0))
    print()
    print("  память до ................. %.1f МБ" % rss_start)
    print("  память после .............. %.1f МБ" % rss_end)
    print("  прирост памяти ............ %.1f МБ на %d учеников" % (rss_end - rss_start, USERS))
    print()
    print("  база после теста .......... %.0f КБ" % (db_bytes / 1024.0))
    print("    users=%d, srs=%d, answers=%d" % (rows["users"], rows["srs"], rows["answers"]))
    print("  на ученика за день ........ %.1f КБ" % (per_user_day_bytes / 1024.0))
    print("  прогноз на курс 84 дня .... %.0f КБ на ученика" % (course_bytes / 1024.0))
    print("  прогноз для %d учеников ... %.1f МБ (полный курс)" % (USERS, course_bytes * USERS / 1048576.0))

    print()
    print("ПРОГНОЗ ОБСЛУЖИВАНИЯ")
    print("-" * 74)
    messages = MESSAGES_PER_LESSON_ESTIMATE
    print("  один урок = ~%d сообщений; Telegram разрешает ~30 сообщений/с на бота" % messages)
    print("  пропускная способность бота: %.0f действий/с -> %.0f уроков/с" % (
        actions / wall if wall else 0, (actions / wall if wall else 0) / messages))
    print("  если %d учеников одновременно нажмут кнопку, задержка ~%.2f с" % (
        USERS, USERS / (actions / wall if wall else 1)))
    print("  напоминания %d ученикам в 09:00: ~%.1f с" % (USERS, USERS / (len(fake.sent) / wall if wall else 1)))

    return 1 if errors else 0


if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    sys.exit(main())
