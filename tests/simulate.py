# -*- coding: utf-8 -*-
"""Офлайн-проверка бота: полный прогон 84 дней курса без Telegram.

Запуск:  python tests/simulate.py
"""

import os
import random
import shutil
import sys
import tempfile

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE)

import bot as botmod                                    # noqa: E402
import course                                           # noqa: E402
import texts                                            # noqa: E402
from content import STATS, WORDS, validate               # noqa: E402
from store import local_now, utcnow                     # noqa: E402

CORRECT_PROBABILITY = 0.8
CHAT_ID = 555000111

FAILURES = []


def check(condition, message):
    if condition:
        print("  ✅ %s" % message)
    else:
        print("  ❌ %s" % message)
        FAILURES.append(message)
    return condition


class FakeTg:
    """Заглушка Telegram API: запоминает сообщения, отдаёт «текущую» клавиатуру."""

    def __init__(self):
        self.sent = []
        self.edits = []
        self.current = None
        self.next_id = 1000
        self.toasts = []
        self.commands = None
        self.webhook = None
        self.documents = []

    # --- API, совместимый с tgbot.Telegram ---
    def delete_webhook(self, **kwargs):
        return True

    def get_me(self):
        return {"username": "english_starter_test_bot", "first_name": "English Starter"}

    def set_my_commands(self, commands):
        self.commands = commands
        return True

    def send_message(self, chat_id, text, reply_markup=None, parse_mode="HTML", **kwargs):
        message = {
            "message_id": self.next_id,
            "chat_id": chat_id,
            "text": text,
            "reply_markup": reply_markup,
        }
        self.next_id += 1
        self.sent.append(message)
        if reply_markup:
            self.current = message
        return message

    def edit_message(self, chat_id, message_id, text, reply_markup=None, parse_mode="HTML"):
        record = {"message_id": message_id, "text": text, "reply_markup": reply_markup}
        self.edits.append(record)
        if self.current and self.current["message_id"] == message_id:
            self.current["text"] = text
            if reply_markup is not None:
                self.current["reply_markup"] = reply_markup
        elif reply_markup:
            self.current = {"message_id": message_id, "chat_id": chat_id, "text": text,
                            "reply_markup": reply_markup}
        return record

    def answer_callback(self, callback_id, text=None, show_alert=False):
        self.toasts.append(text)
        return True

    def send_chat_action(self, chat_id, action="typing"):
        return True

    def send_document(self, chat_id, file_path, caption=None, filename=None):
        stored = file_path + ".stored"
        shutil.copy2(file_path, stored)
        self.documents.append({"chat_id": chat_id, "path": file_path, "stored": stored,
                               "caption": caption, "filename": filename})
        return {"message_id": self.next_id,
                "document": {"file_id": stored, "file_name": filename or os.path.basename(file_path)}}

    def get_file(self, file_id):
        return {"file_path": file_id}

    def download_file(self, file_id, destination):
        shutil.copy2(file_id, destination)
        return destination, os.path.getsize(destination)

    def call(self, method, params=None, **kwargs):
        return None


def text_update(text):
    return {
        "update_id": 1,
        "message": {
            "message_id": 1,
            "chat": {"id": CHAT_ID, "type": "private"},
            "from": {"id": CHAT_ID, "username": "tester", "first_name": "Тест"},
            "text": text,
        },
    }


def text_update_from(chat_id, text):
    return {
        "update_id": 3,
        "message": {
            "message_id": 2,
            "chat": {"id": chat_id, "type": "private"},
            "from": {"id": chat_id, "username": "other", "first_name": "Другой"},
            "text": text,
        },
    }


def callback_update(data):
    return {
        "update_id": 2,
        "callback_query": {
            "id": "cb-%s" % data,
            "from": {"id": CHAT_ID, "username": "tester", "first_name": "Тест"},
            "message": {"message_id": 1, "chat": {"id": CHAT_ID, "type": "private"}},
            "data": data,
        },
    }


def buttons(fake):
    if not fake.current or not fake.current.get("reply_markup"):
        return []
    keyboard = fake.current["reply_markup"].get("inline_keyboard") or []
    return [b for row in keyboard for b in row]


def pick_question_button(fake, rng):
    """/a|qi|idx - виртуальный ученик отвечает верно с вероятностью 80%."""
    for button in buttons(fake):
        data = button["callback_data"]
        if data.startswith("a|"):
            return data
    return None


def run_step(bot, fake, state_before, rng):
    """Одно действие виртуального ученика. Возвращает True, если что-то сделано."""
    session = (bot.state(CHAT_ID) or {}).get("session")
    if session and session.get("await"):
        question = session["questions"][session["qi"]]
        answer = question["answer"] if rng.random() < CORRECT_PROBABILITY else "чепуха"
        bot.handle_update(text_update(answer))
        return True

    available = [b.get("callback_data", "") for b in buttons(fake)]
    available = [data for data in available if data]
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
        bot.handle_update(callback_update(chosen))
        return True

    for prefix in ("c|show|", "c|next|", "n|", "s|next|", "go|lesson", "go|next_day"):
        data = find(prefix)
        if data:
            bot.handle_update(callback_update(data))
            return True

    grade = find("c|g|")
    if grade:
        parts = grade.split("|")
        value = 2 if rng.random() < 0.2 else (1 if rng.random() < CORRECT_PROBABILITY else 0)
        bot.handle_update(callback_update("c|g|%s|%d" % (parts[2], value)))
        return True

    for prefix in ("onb|mode|light", "onb|time|09:00", "onb|tz|180"):
        if prefix in available:
            bot.handle_update(callback_update(prefix))
            return True

    if available:
        bot.handle_update(callback_update(available[0]))
        return True
    return False


def run_lesson(bot, fake, rng, max_steps=600):
    bot.handle_update(text_update("/today"))
    steps = 0
    while steps < max_steps:
        steps += 1
        session = (bot.state(CHAT_ID) or {}).get("session")
        if not session:
            return True
        if not run_step(bot, fake, session, rng):
            return False
    return False


def shift_time_back_one_day(store, chat_id):
    """Имитируем наступление следующего дня: даты повторений и «урок сделан» сдвигаются."""
    from store import iso, parse_iso
    from datetime import timedelta
    with store.lock:
        rows = store.conn.execute(
            "SELECT word_key, due_at FROM srs WHERE chat_id = ?", (chat_id,)
        ).fetchall()
        for row in rows:
            due = parse_iso(row["due_at"])
            if due:
                store.conn.execute(
                    "UPDATE srs SET due_at = ? WHERE chat_id = ? AND word_key = ?",
                    (iso(due - timedelta(days=1)), chat_id, row["word_key"]),
                )
        store.conn.commit()
    store.update_user(chat_id, last_lesson_date=None)


def main():
    botmod.log = lambda message: None      # в тесте логи бота не нужны
    os.environ["TELEGRAM_BACKUP"] = "0"    # и внешние копии: тест не должен слать файлы
    print("=" * 70)
    print("ПРОВЕРКА КОНТЕНТА")
    print("=" * 70)
    problems = validate()
    check(not problems, "контент без ошибок (%d тем, %d слов, %d карточек, %d диалогов)" % (
        STATS["topics"], STATS["words"], STATS["grammar"], STATS["dialogues"]))
    for problem in problems:
        print("     ! %s" % problem)

    print()
    print("=" * 70)
    print("ПРОВЕРКА ПЛАНА НА 84 ДНЯ")
    print("=" * 70)
    plan_problems = []
    covered = []
    word_day = {}
    for day in range(1, 85):
        plan = course.plan_for_day(day)
        dow = course.dow_of_day(day)
        if plan["is_review"] and dow == 6:
            if not plan["dialogue"]:
                plan_problems.append("день %d: день повторения без диалога" % day)
            if not plan["new_words"]:
                continue
        if plan.get("consolidation"):
            if not plan["grammar"]:
                plan_problems.append("день %d: итоговый день без грамматики" % day)
            continue
        if not 4 <= len(plan["new_words"]) <= 8:
            plan_problems.append("день %d: %d новых слов" % (day, len(plan["new_words"])))
        if not plan["grammar"]:
            plan_problems.append("день %d: нет грамматики" % day)
        for word in plan["new_words"]:
            covered.append(word["key"])
            if word["key"] in word_day:
                plan_problems.append("слово %s встречается в уроках %d и %d" % (
                    word["key"], word_day[word["key"]], day))
            word_day[word["key"]] = day
    check(not plan_problems, "все 84 дня имеют полный набор материалов")
    for problem in plan_problems[:10]:
        print("     ! %s" % problem)
    check(len(covered) == len(WORDS),
          "все %d слов курса попадают в уроки (покрыто %d)" % (len(WORDS), len(covered)))

    print()
    print("=" * 70)
    print("ПРОВЕРКА ОТВЕТОВ (устойчивость к опечаткам)")
    print("=" * 70)
    check(course.check_typed("Hello", "hello")[0], "регистр не важен: Hello = hello")
    check(course.check_typed("  hello!  ", "hello")[0], "знаки и пробелы не важны")
    check(course.check_typed("helo", "hello")[0], "одна опечатка прощается (helo)")
    check(not course.check_typed("cat", "hello")[0], "чужое слово не засчитывается")
    check(course.check_typed("привет", "привет", ["здравствуйте"])[0], "варианты перевода принимаются")

    print()
    print("=" * 70)
    print("ПРОГОН КУРСА: 84 дня занятий виртуальным учеником")
    print("=" * 70)
    rng = random.Random(42)
    workdir = os.path.join(BASE, "tests", "_run")
    os.makedirs(workdir, exist_ok=True)
    db_path = os.path.join(workdir, "sim.db")
    if os.path.exists(db_path):
        os.remove(db_path)
    bot = botmod.Bot("111:TEST", db_path=db_path)
    fake = FakeTg()
    bot.tg = fake
    bot.me = fake.get_me()

    bot.handle_update(text_update("/start"))
    check(fake.current is not None and "onb|mode|light" in
          [b.get("callback_data") for b in buttons(fake)], "/start показывает выбор режима")
    bot.handle_update(callback_update("onb|mode|light"))
    bot.handle_update(callback_update("onb|time|09:00"))
    bot.handle_update(callback_update("onb|tz|180"))
    user = bot.store.get_user(CHAT_ID)
    check(user["onboarded"] == 1 and user["per_day"] == 5 and user["remind_time"] == "09:00",
          "онбординг сохранил режим, время и часовой пояс")

    days_ok = 0
    for day in range(1, 85):
        shift_time_back_one_day(bot.store, CHAT_ID)
        ok = run_lesson(bot, fake, rng)
        user = bot.store.get_user(CHAT_ID)
        expected = min(day + 1, 84)
        if not ok:
            check(False, "день %d: занятие не завершилось (шагов не хватило)" % day)
            break
        if user["day"] != expected:
            check(False, "день %d: ожидался день курса %d, получен %d" % (day, expected, user["day"]))
            break
        days_ok += 1

    check(days_ok == 84, "пройдены все 84 дня курса (пройдено %d)" % days_ok)

    user = bot.store.get_user(CHAT_ID)
    counts = bot.store.srs_counts(CHAT_ID)
    check(counts["total"] >= len(WORDS) - 5,
          "в повторении %d слов из %d" % (counts["total"], len(WORDS)))
    check((user["total_lessons"] or 0) >= 84,
          "засчитано занятий: %d" % (user["total_lessons"] or 0))
    check((user["streak"] or 0) >= 1, "серия дней считается: %d" % (user["streak"] or 0))
    check((user["total_answers"] or 0) > 300,
          "записано ответов: %d" % (user["total_answers"] or 0))
    accuracy = bot.store.week_accuracy(CHAT_ID, days=3650)
    check(60 <= accuracy["percent"] <= 95,
          "итоговая точность %d%% (%d ответов)" % (accuracy["percent"], accuracy["total"]))

    print()
    print("=" * 70)
    print("ПРОВЕРКА КОМАНД")
    print("=" * 70)
    for command in ["/help", "/progress", "/program", "/words", "/grammar",
                    "/word hello", "/settings", "/quiz", "/today", "/stop", "/review"]:
        before = len(fake.sent)
        try:
            bot.handle_update(text_update(command))
            ok = len(fake.sent) > before
        except Exception as error:              # noqa: BLE001
            ok = False
            print("     ! %s: %s" % (command, error))
        check(ok, "команда %s отвечает" % command)

    text, _ = texts.words_text(bot.store, bot.store.get_user(CHAT_ID))
    check("Слова курса" in text, "/words формирует список тем")

    print()
    print("=" * 70)
    print("ПРОВЕРКА РЕЖИМОВ (интенсивный: больше повторения и упражнений)")
    print("=" * 70)
    bot.store.update_user(CHAT_ID, mode="intensive", per_day=15, state=None,
                          last_lesson_date=None, day=1)
    bot.handle_update(text_update("/today"))
    intensive_start = len(fake.sent)
    steps = 0
    while steps < 900 and (bot.state(CHAT_ID) or {}).get("session"):
        steps += 1
        if not run_step(bot, fake, None, rng):
            break
    intensive_text = [m["text"] for m in fake.sent[intensive_start:]]
    exercises = [t for t in intensive_text if "Упражнение" in t]
    check(any("Упражнение 10/" in t for t in exercises),
          "в интенсивном режиме 10 упражнений (найдено %d)" % len(exercises))
    check(any("Повторение 15/15" in t for t in intensive_text),
          "в интенсивном режиме 15 карточек повторения")

    print()
    print("=" * 70)
    print("ПРОВЕРКА МЕНЮ, СЛОВАРЯ И ТРЕНАЖЁРОВ")
    print("=" * 70)
    bot.store.update_user(CHAT_ID, state=None)

    menu_texts = [text for row in texts.MAIN_MENU["keyboard"] for text in row]
    check(len(menu_texts) >= 8 and "📖 Словарь" in menu_texts and "🧩 Конструкции" in menu_texts,
          "в меню %d кнопок: %s" % (len(menu_texts), ", ".join(menu_texts)))

    bot.handle_update(text_update("/dictionary"))
    check("СЛОВАРЬ" in fake.sent[-1]["text"], "/dictionary открывает словарь")
    bot.handle_update(callback_update("dic|learned|0"))
    check("ВЫУЧЕННЫЕ" in fake.edits[-1]["text"], "раздел «Выученные слова»")
    bot.handle_update(callback_update("dic|learned|1"))
    check("страница 2" in fake.edits[-1]["text"], "листание словаря работает")
    for mode in ("weak", "strong", "ahead"):
        bot.handle_update(callback_update("dic|%s|0" % mode))
        check("Всего" in fake.edits[-1]["text"], "раздел словаря «%s»" % mode)
    bot.handle_update(callback_update("words|topics"))
    check("Слова курса" in fake.edits[-1]["text"], "переход из словаря к темам")
    bot.handle_update(callback_update("dic|noop|3"))
    check(any("Страница 4" in (toast or "") for toast in fake.toasts), "кнопка-счётчик страниц отвечает")

    # тренажёр новых слов
    bot.store.update_user(CHAT_ID, state=None)
    fresh_user = bot.store.get_user(CHAT_ID)
    words = course.recent_new_words(fresh_user["day"], limit=10)
    check(len(words) > 0, "для практики новых слов есть %d слов" % len(words))
    bot.handle_update(text_update("/newwords"))
    check(any("ПРАКТИКА НОВЫХ СЛОВ" in m["text"] for m in fake.sent[-3:]),
          "/newwords запускает тренажёр")
    steps = 0
    while steps < 300 and (bot.state(CHAT_ID) or {}).get("session"):
        steps += 1
        if not run_step(bot, fake, None, rng):
            break
    check(not (bot.state(CHAT_ID) or {}).get("session"), "тренажёр новых слов завершается")

    # тренажёр конструкций: каталог + одна конструкция
    bot.handle_update(text_update("/constructions"))
    check("ТРЕНАЖЁР КОНСТРУКЦИЙ" in fake.sent[-1]["text"], "каталог конструкций открывается")
    cards = course.drill_cards_available(fresh_user["day"])
    check(len(cards) >= 4, "доступно конструкций по текущему дню: %d" % len(cards))
    card_id = cards[0]
    bot.handle_update(callback_update("drl|card|%s" % card_id))
    check("Конструкция" in fake.sent[-1]["text"], "запуск тренажёра по конструкции %s" % card_id)
    steps = 0
    while steps < 300 and (bot.state(CHAT_ID) or {}).get("session"):
        steps += 1
        if not run_step(bot, fake, None, rng):
            break
    stat = bot.store.drill_stats(CHAT_ID).get(card_id) or {}
    check(stat.get("total", 0) >= 4, "ответы по конструкции записаны: %d" % stat.get("total", 0))

    # смешанная практика
    bot.handle_update(text_update("/practice"))
    check(any("СМЕШАННАЯ ПРАКТИКА" in m["text"] for m in fake.sent[-3:]),
          "/practice запускает микс")
    steps = 0
    while steps < 300 and (bot.state(CHAT_ID) or {}).get("session"):
        steps += 1
        if not run_step(bot, fake, None, rng):
            break
    check(not (bot.state(CHAT_ID) or {}).get("session"), "смешанная практика завершается")

    # кнопки «что дальше» и переходы
    for data in ("go|constructions", "go|dictionary", "go|newwords", "go|practice"):
        before = len(fake.sent)
        bot.handle_update(callback_update(data))
        check(len(fake.sent) > before, "кнопка %s отвечает" % data)
        bot.store.update_user(CHAT_ID, state=None)

    all_drills = sorted(bot.store.drill_stats(CHAT_ID).keys())
    check(len(all_drills) >= 2, "статистика тренажёра ведётся по %d конструкциям" % len(all_drills))

    print()
    print("=" * 70)
    print("ПРОВЕРКА РЕЗЕРВНОЙ КОПИИ И ВОССТАНОВЛЕНИЯ (24/7 без потери прогресса)")
    print("=" * 70)
    admin = bot.admin_chat_id()
    check(admin == CHAT_ID, "владелец определён: %s" % admin)

    others = [u for u in bot.store.all_users() if u["chat_id"] != admin]
    if not others:
        bot.store.ensure_user(999000111, "helper", "Помощник")
        others = [bot.store.get_user(999000111)]
    other_id = others[0]["chat_id"]

    fake.sent = []
    bot.handle_update(text_update_from(other_id, "/backup"))
    check(any("только владелец" in message["text"] for message in fake.sent),
          "посторонний не может скачать базу")

    ok = bot.send_backup(admin, reason="тест")
    check(ok and fake.documents, "резервная копия отправлена (%s)" % (
        fake.documents[-1]["filename"] if fake.documents else "нет"))
    users_before = len(bot.store.all_users())
    learned_before = bot.store.srs_counts(admin)["total"]

    # ломаем базу: добавляем «лишнего» ученика
    bot.store.ensure_user(777000222, "extra", "Лишний")
    check(len(bot.store.all_users()) == users_before + 1, "база изменена (появился лишний ученик)")

    backup = fake.documents[-1]
    bot.restore_from_document(admin, {"file_id": backup["stored"],
                                      "file_name": "english-starter-backup.db"})
    check(len(bot.store.all_users()) == users_before,
          "база восстановлена из копии (%d учеников)" % len(bot.store.all_users()))
    check(bot.store.srs_counts(admin)["total"] == learned_before,
          "прогресс владельца сохранился: %d слов" % bot.store.srs_counts(admin)["total"])
    check(any("Прогресс восстановлен" in message["text"] for message in fake.sent),
          "бот подтвердил восстановление")

    bad_file = os.path.join(os.path.dirname(db_path), "not-a-db.db")
    with open(bad_file, "wb") as handle:
        handle.write(b"this is not sqlite")
    bot.restore_from_document(admin, {"file_id": bad_file, "file_name": "not-a-db.db"})
    check(any("не похоже на базу" in message["text"] for message in fake.sent),
          "битый файл отклонён")

    print()
    print("=" * 70)
    print("ПРОВЕРКА НАПОМИНАНИЙ")
    print("=" * 70)
    user = bot.store.get_user(CHAT_ID)
    now_local = local_now(user["tz_offset"])
    bot.store.update_user(CHAT_ID, reminders_on=1, onboarded=1,
                          remind_time="%02d:%02d" % (now_local.hour, now_local.minute),
                          last_lesson_date=None, last_remind_date=None)
    sent_first = bot.check_reminders()
    sent_second = bot.check_reminders()
    check(sent_first == 1, "напоминание отправлено один раз (%d)" % sent_first)
    check(sent_second == 0, "повторное напоминание в тот же день не отправляется (%d)" % sent_second)
    check(any("Доброе утро" in message["text"] for message in fake.sent),
          "текст напоминания корректен")

    print()
    print("=" * 70)
    if FAILURES:
        print("РЕЗУЛЬТАТ: %d ПРОВЕРОК ПРОВАЛЕНО" % len(FAILURES))
        for failure in FAILURES:
            print("  - %s" % failure)
        print("=" * 70)
        return 1
    print("РЕЗУЛЬТАТ: ВСЕ ПРОВЕРКИ ПРОЙДЕНЫ ✅")
    print("=" * 70)
    return 0


if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    sys.exit(main())
