# -*- coding: utf-8 -*-
"""Тексты и оформление сообщений бота (HTML)."""

from html import escape

from content import STATS, TOTAL_DAYS, TOTAL_WEEKS, WEEKS, WORD_BY_KEY
from course import course_progress, interval_label, plan_for_day, week_of_day

from tgbot import btn, inline, reply_keyboard

TITLE = "🇬🇧 English Starter"

MAIN_MENU = reply_keyboard([
    ["▶️ Урок дня", "🆕 Новые слова"],
    ["🧩 Конструкции", "✍️ Практика"],
    ["📖 Словарь", "📊 Прогресс"],
    ["📚 Программа", "⚙️ Настройки"],
])

DICT_MODES = {
    "learned": "✅ Выученные слова",
    "weak": "🤔 Шаткие слова",
    "strong": "💪 Закреплённые",
    "ahead": "🆕 Впереди по курсу",
}

DICT_MODE_HINT = {
    "learned": "Все слова, которые уже были в уроках.",
    "weak": "Здесь слова, где вы чаще ошибаетесь или отвечали «не помню».",
    "strong": "Эти слова повторяются реже всего — вы их уверенно помните.",
    "ahead": "Эти слова ещё впереди: курс дойдёт до них позже.",
}


def bar(percent, width=10):
    """Текстовый индикатор прогресса."""
    percent = max(0, min(100, int(percent)))
    filled = int(round(width * percent / 100.0))
    return "▰" * filled + "▱" * (width - filled)


def rule(width=16):
    return "─" * width

MODE_TITLES = {
    "light": "🌱 10 минут в день — 5–6 новых слов + короткое повторение",
    "standard": "🌿 20 минут в день — та же программа + больше повторения и практики",
    "intensive": "🌳 40 минут в день — та же программа + интенсивная практика",
}


def esc(text):
    return escape(str(text or ""), quote=False)


# --------------------------------------------------------------------------
# Карточки слов
# --------------------------------------------------------------------------

def word_front(word, index=None, total=None, review=False):
    head = "🔁 Повторение %s/%s" % (index, total) if review else "🆕 Новое слово %s/%s" % (index, total)
    lines = [
        "<b>%s</b>" % head,
        "",
        "🇬🇧 <b>%s</b>" % esc(word["en"]),
        "🗣 <i>%s</i>" % esc(word["tr"]),
        "",
        "<i>Сначала вспомните перевод сами, потом нажмите кнопку.</i>",
    ]
    return "\n".join(lines)


def word_back(word, first_time=False):
    lines = [
        "🇬🇧 <b>%s</b>  —  %s" % (esc(word["en"]), esc(word["ru"])),
        "🗣 <i>%s</i>" % esc(word["tr"]),
        "",
        "✍️ <b>%s</b>" % esc(word["ex_en"]),
        "    %s" % esc(word["ex_ru"]),
    ]
    if first_time:
        lines += ["", "<i>Скажите слово вслух 3 раза и повторите пример.</i>"]
    return "\n".join(lines)


def pronunciation_url(word):
    from urllib.parse import quote_plus
    return "https://translate.google.com/?sl=en&tl=ru&text=%s&op=translate" % quote_plus(
        word["en"].split(" (")[0]
    )


# --------------------------------------------------------------------------
# Урок
# --------------------------------------------------------------------------

def lesson_intro(plan, day, user, review_count, new_count):
    prog = course_progress(day)
    lines = [
        "📅 <b>День %d из %d</b>  ·  неделя %d «%s»" % (plan["day"], TOTAL_DAYS, plan["week"], esc(plan["week_title"])),
        "🎯 <b>Сегодня:</b> %s" % esc(plan["focus"]),
        "",
        "🔁 повторение: <b>%d</b> слов" % review_count,
    ]
    if plan["is_review"] and not new_count:
        if plan.get("consolidation"):
            lines.append("🏁 <b>Итоговая неделя:</b> повторяем весь курс, затем экзамен A1")
        else:
            lines.append("🏁 <b>День повторения и теста недели</b> (новых слов нет)")
    else:
        lines.append("🆕 новых слов: <b>%d</b>" % new_count)
    if plan.get("grammar"):
        lines.append("📘 грамматика: <b>%s</b>" % esc(plan["grammar"]["title"]))
    if plan.get("dialogue"):
        lines.append("💬 диалог: <b>%s</b>" % esc(plan["dialogue"]["title"]))
    lines += ["", "⏱ Примерно %d минут. Поехали!" % (10 if not plan["is_review"] else 12)]
    lines += ["", "<i>Прогресс курса: %d%%</i>" % prog["percent"]]
    return "\n".join(lines)


def grammar_card(card):
    lines = [
        "📘 <b>%s</b>" % esc(card["title"]),
        "",
        esc(card["body"]),
        "",
        "🔹 <b>Примеры</b>",
    ]
    for en, ru in card["examples"]:
        lines.append("• <b>%s</b> — %s" % (esc(en), esc(ru)))
    if card.get("tip"):
        lines += ["", "💡 <i>%s</i>" % esc(card["tip"])]
    return "\n".join(lines)


def dialogue_card(dialogue):
    lines = [
        "💬 <b>Диалог: %s</b>" % esc(dialogue["title"]),
        "",
    ]
    for who, line in dialogue["lines"]:
        lines.append("<b>%s:</b> %s" % (esc(who), esc(line)))
    if dialogue.get("note"):
        lines += ["", "💡 <i>%s</i>" % esc(dialogue["note"])]
    lines += ["", "<i>Прочитайте диалог вслух — сначала по ролям, потом за обе стороны.</i>"]
    return "\n".join(lines)


def question_text(question, number=None, total=None):
    head = ""
    if number and total:
        head = "✍️ <b>Упражнение %d/%d</b>\n\n" % (number, total)
    return head + question["prompt"]


def answer_result(question, correct, note=""):
    if correct:
        head = "✅ <b>Верно!</b>"
    else:
        head = "❌ <b>Не совсем.</b>"
    lines = [head, ""]
    lines.append(question["explain"])
    if note:
        lines += ["", "💡 <i>%s</i>" % esc(note)]
    return "\n".join(lines)


def session_finish(store, user, correct, total, streak, extra=""):
    acc = round(100.0 * correct / total) if total else 0
    lines = [
        "🏆 <b>Урок завершён!</b>",
        "",
        "Правильных ответов: <b>%d из %d</b> (%d%%)" % (correct, total, acc),
        "🔥 Серия дней подряд: <b>%d</b>" % streak,
    ]
    if extra:
        lines += ["", extra]
    counts = store.srs_counts(user["chat_id"])
    lines += [
        "",
        "📈 Слов в изучении: <b>%d</b>, из них закреплено: <b>%d</b>" % (counts["total"], counts["strong"]),
        "⏰ Следующее напоминание: в <b>%s</b>" % user["remind_time"],
    ]
    return "\n".join(lines)


# --------------------------------------------------------------------------
# Справочные экраны
# --------------------------------------------------------------------------

def help_text(user):
    day = user["day"] if user else 1
    return "\n".join([
        "❓ <b>Как заниматься</b>",
        "",
        "<b>Каждый день</b> — кнопка <b>▶️ Урок дня</b> (10 минут):",
        "повторение → новые слова → грамматика → упражнения → диалог.",
        "",
        "<b>Когда есть 5 минут</b> — короткие тренажёры:",
        "🆕 <b>Новые слова</b> — закрепление слов последних уроков.",
        "🧩 <b>Конструкции</b> — отработка грамматики: подстановка, выбор формы, перевод.",
        "✍️ <b>Практика</b> — микс: слова + конструкции + диалог недели.",
        "🔁 <b>Повторение</b> — только карточки слов из очереди.",
        "",
        "📖 <b>Словарь</b> — все выученные слова, шаткие и закреплённые, по страницам и темам.",
        "📊 <b>Прогресс</b> — день курса, серия, точность, слабые места.",
        "",
        "Каждый 7-й день недели — повторение и тест. 12-я неделя — экзамен A1.",
        "",
        "📋 <b>Команды</b>",
        "/today — урок дня",
        "/newwords — практика новых слов",
        "/constructions — тренажёр конструкций",
        "/practice — смешанная практика",
        "/dictionary — словарь",
        "/review — повторение слов",
        "/quiz — быстрый тест на 10 вопросов",
        "/progress — статистика и серия",
        "/program — программа курса",
        "/words — слова по темам",
        "/word hello — карточка слова",
        "/grammar — справочник грамматики",
        "/settings — напоминание, пояс, объём",
        "/backup — резервная копия прогресса (пришлите файл обратно для восстановления)",
        "/stop — выключить напоминания",
        "",
        "Сейчас вы на дне <b>%d</b> из %d." % (day, TOTAL_DAYS),
    ])


def program_text(current_day=1):
    lines = [
        "📚 <b>Программа курса: с нуля до A1</b>",
        "",
        "<b>Как устроен курс</b>",
        "• 12 недель, 84 дня, 6 занятий + 1 день повторения в неделю.",
        "• Каждое занятие 10 минут: повторение → 5 новых слов → грамматика → упражнения → диалог.",
        "• Всего в курсе: %d слов, %d грамматических карточек, %d диалогов." % (
            STATS["words"], STATS["grammar"], STATS["dialogues"]),
        "• Слова возвращаются по системе интервального повторения: завтра, через 2, 4, 8, 16, 32 дня.",
        "• Каждые 4 недели — контрольная неделя: тест и повторение слабых слов.",
        "",
        "<b>Недели</b>",
    ]
    cur_week = week_of_day(current_day)
    for week in WEEKS:
        first = (week["n"] - 1) * 7 + 1
        last = first + 6
        mark = "👉 " if week["n"] == cur_week else ""
        lines.append(
            "%s<b>%d. Дни %d–%d. %s</b>\n    %s\n    ✅ %s" % (
                mark, week["n"], first, last, esc(week["title"]), esc(week["focus"]), esc(week["goal"])
            )
        )
    lines += [
        "",
        "<b>Что будет после курса</b>",
        "Дальше — блок A2: Present Perfect, условные предложения, фразовые глаголы,",
        "аудирование и разговорная практика. Об этом бот напомнит на 12-й неделе.",
    ]
    return "\n".join(lines)


def settings_text(user):
    return "\n".join([
        "⚙️ <b>Настройки</b>",
        "",
        "Режим: <b>%s</b>" % MODE_TITLES.get(user["mode"], user["mode"]),
        "Напоминание: <b>%s</b> (часовой пояс UTC%+d)" % (
            user["remind_time"], (user["tz_offset"] or 0) // 60),
        "Напоминания: <b>%s</b>" % ("включены" if user["reminders_on"] else "выключены"),
        "День курса: <b>%d</b>" % user["day"],
        "",
        "Выберите, что изменить:",
    ])


def settings_keyboard(user):
    return inline([
        [btn("⏰ Время напоминания", "set|time")],
        [btn("🌍 Часовой пояс", "set|tz")],
        [btn("📚 Объём в день", "set|mode")],
        [btn(("🔕 Выключить напоминания" if user["reminders_on"] else "🔔 Включить напоминания"),
             "set|toggle_remind")],
        [btn("⏪ Перейти на другой день курса", "set|day")],
        [btn("🗑 Сбросить прогресс", "set|reset")],
    ])


def progress_text(store, user):
    counts = store.srs_counts(user["chat_id"])
    acc = store.week_accuracy(user["chat_id"], days=7)
    prog = course_progress(user["day"])
    total = user["total_lessons"] or 0
    weak = store.weakest_words(user["chat_id"], limit=5)
    weak_titles = ", ".join(WORD_BY_KEY[k]["en"] for k in weak if k in WORD_BY_KEY) or "—"
    drills = store.drill_stats(user["chat_id"])
    drill_total = sum(item["total"] for item in drills.values())
    drill_correct = sum(item["correct"] for item in drills.values())
    drill_percent = round(100.0 * drill_correct / drill_total) if drill_total else 0

    done = prog["percent"]
    return "\n".join([
        "📊 <b>ВАШ ПРОГРЕСС</b>",
        rule(),
        "Курс: %s %d%%" % (bar(done), done),
        "📅 День <b>%d</b> из %d (неделя %d/%d)" % (prog["day"], prog["total_days"], prog["week"], prog["total_weeks"]),
        "🔥 Серия: <b>%d</b> дн. (рекорд %d)" % (user["streak"], user["best_streak"] or 0),
        "🏫 Занятий пройдено: <b>%d</b>" % total,
        "",
        "📈 Слов в изучении: <b>%d</b>" % counts["total"],
        "💪 Закреплено: <b>%d</b>" % counts["strong"],
        "⏳ К повторению сейчас: <b>%d</b>" % counts["due"],
        "🎯 Точность за 7 дней: <b>%d%%</b> (%d ответов)" % (acc["percent"], acc["total"]),
        "🧩 Конструкции: <b>%d%%</b> (%d заданий)" % (drill_percent, drill_total),
        "",
        "🤔 Слабые слова: %s" % esc(weak_titles),
        "",
        "<i>До конца курса A1 осталось %d дней занятий.</i>" % max(0, prog["total_days"] - prog["day"] + 1),
    ])


def words_text(store, user, topic_id=None):
    from content import TOPICS, WORDS_BY_TOPIC
    lines = ["📖 <b>Слова курса</b>", "", "Нажмите тему, чтобы посмотреть слова:"]
    keyboard = []
    row = []
    for topic in TOPICS:
        words = WORDS_BY_TOPIC[topic["id"]]
        learned = sum(1 for w in words if (store.srs_row(user["chat_id"], w["key"]) or {}).get("learned"))
        row.append(btn("%s %s %d/%d" % (topic.get("emoji", "📘"), topic["title"], learned, len(words)),
                       "topic|%s" % topic["id"]))
        if len(row) == 2:
            keyboard.append(row)
            row = []
    if row:
        keyboard.append(row)
    return "\n".join(lines), inline(keyboard)


def topic_text(store, user, topic_id):
    from content import TOPIC_BY_ID, WORDS_BY_TOPIC
    topic = TOPIC_BY_ID[topic_id]
    lines = ["%s <b>%s</b>" % (topic.get("emoji", "📘"), esc(topic["title"])), ""]
    for word in WORDS_BY_TOPIC[topic_id]:
        row = store.srs_row(user["chat_id"], word["key"])
        mark = "✅" if row and row.get("learned") else "⬜️"
        lines.append("%s <b>%s</b> — %s\n     <i>%s</i>" % (
            mark, esc(word["en"]), esc(word["ru"]), esc(word["tr"])))
    lines += ["", "✅ — слово уже в вашем повторении, ⬜️ — ещё впереди."]
    return "\n".join(lines), inline([[btn("⬅️ К темам", "words|topics")]])


def word_card_text(store, user, word_key):
    word = WORD_BY_KEY.get(word_key.strip().lower())
    if not word:
        return None
    row = store.srs_row(user["chat_id"], word["key"])
    status = "не начато"
    if row and row.get("learned"):
        status = "в повторении, следующий раз %s" % interval_label(row.get("box") or 0)
    return "\n".join([
        "📖 <b>%s</b> — %s" % (esc(word["en"]), esc(word["ru"])),
        "🗣 <i>%s</i>" % esc(word["tr"]),
        "📚 Тема: %s" % esc(word["topic_title"]),
        "",
        "✍️ <b>%s</b>" % esc(word["ex_en"]),
        "    %s" % esc(word["ex_ru"]),
        "",
        "Статус: %s" % status,
    ])


def grammar_index_text():
    from content import GRAMMAR
    lines = ["📘 <b>Грамматика курса</b>", ""]
    keyboard = []
    for card in GRAMMAR:
        lines.append("• <b>%s</b> (неделя %d)" % (esc(card["title"]), card["week"]))
        keyboard.append([btn(card["title"][:52], "gr|%s" % card["id"])])
    return "\n".join(lines), inline(keyboard)


def reminder_text(user, late_minutes=0):
    day = user["day"]
    plan = plan_for_day(day, user["per_day"] or 5)
    lines = [
        "☀️ <b>Доброе утро!</b>",
        "",
        "День <b>%d</b> из %d · неделя %d «%s»" % (day, TOTAL_DAYS, plan["week"], esc(plan["week_title"])),
        "🎯 %s" % esc(plan["focus"]),
        "🔥 Серия: %d дн." % user["streak"],
        "",
        "10 минут — и день закрыт. Начнём?",
    ]
    if int(late_minutes or 0) > 180:
        lines += ["", "⏳ <i>Напоминание с задержкой: сервер просыпался. Ничего не потеряно — "
                      "продолжаем с того же дня.</i>"]
    return "\n".join(lines)


def reminder_keyboard():
    return inline([[btn("▶️ Начать урок", "go|lesson")], [btn("⏰ Позже", "go|later")]])


def done_keyboard():
    return inline([
        [btn("🔁 Повторить слабые слова", "go|review")],
        [btn("📊 Прогресс", "go|progress"), btn("➡️ Следующий день", "go|next_day")],
    ])


def lesson_keyboard():
    return inline([
        [btn("▶️ Начать урок", "go|lesson")],
        [btn("🔁 Только повторение", "go|review")],
    ])


# --------------------------------------------------------------------------
# Словарь
# --------------------------------------------------------------------------

def _dict_rows(store, user, mode):
    from content import WORDS
    learned_map = store.srs_map(user["chat_id"])
    if mode == "ahead":
        return [w for w in WORDS if not (learned_map.get(w["key"]) or {}).get("learned")]
    rows = []
    for word in WORDS:
        row = learned_map.get(word["key"]) or {}
        if not row.get("learned"):
            continue
        box = row.get("box") or 0
        lapses = row.get("lapses") or 0
        if mode == "weak" and not (box <= 1 or lapses > 0):
            continue
        if mode == "strong" and box < 4:
            continue
        rows.append(word)
    return rows


def dictionary_home(store, user):
    from content import WORDS
    counts = store.srs_counts(user["chat_id"])
    learned_map = store.srs_map(user["chat_id"])
    learned = counts["total"]
    strong = counts["strong"]
    weak = sum(1 for w in WORDS
               if (learned_map.get(w["key"]) or {}).get("learned")
               and ((learned_map[w["key"]].get("box") or 0) <= 1
                    or (learned_map[w["key"]].get("lapses") or 0) > 0))
    percent = round(100.0 * learned / len(WORDS)) if WORDS else 0
    text = "\n".join([
        "📖 <b>СЛОВАРЬ</b>",
        rule(),
        "Выучено: <b>%d</b> из %d слов" % (learned, len(WORDS)),
        "%s %d%%" % (bar(percent), percent),
        "",
        "✅ Выученные: <b>%d</b>" % learned,
        "💪 Закреплённые: <b>%d</b>" % strong,
        "🤔 Шаткие: <b>%d</b>" % weak,
        "",
        "<i>Карточка одного слова: /word hello</i>",
    ])
    keyboard = inline([
        [btn("✅ Выученные (%d)" % learned, "dic|learned|0")],
        [btn("🤔 Шаткие (%d)" % weak, "dic|weak|0"), btn("💪 Закреплённые (%d)" % strong, "dic|strong|0")],
        [btn("🆕 Впереди (%d)" % (len(WORDS) - learned), "dic|ahead|0")],
        [btn("📚 По темам", "words|topics")],
    ])
    return text, keyboard


def dictionary_list(store, user, mode="learned", page=0, per_page=12):
    from content import WORDS
    words = _dict_rows(store, user, mode)
    total_pages = max(1, (len(words) + per_page - 1) // per_page)
    page = max(0, min(total_pages - 1, int(page or 0)))
    chunk = words[page * per_page:(page + 1) * per_page]

    learned_map = store.srs_map(user["chat_id"])
    lines = [
        "📖 <b>%s</b>" % DICT_MODES.get(mode, "Словарь").upper(),
        rule(),
        "%s" % DICT_MODE_HINT.get(mode, ""),
        "Всего: <b>%d</b> · страница %d из %d" % (len(words), page + 1, total_pages),
        "",
    ]
    if not chunk:
        lines.append("<i>Здесь пока пусто.</i>")
    for offset, word in enumerate(chunk):
        number = page * per_page + offset + 1
        row = learned_map.get(word["key"]) or {}
        mark = "✅" if (row.get("box") or 0) >= 4 else ("🟡" if row.get("learned") else "▫️")
        lines.append("%d. %s <b>%s</b> — %s · <i>%s</i>" % (
            number, mark, esc(word["en"]), esc(word["ru"]), esc(word["tr"])))

    rows = []
    nav = []
    if page > 0:
        nav.append(btn("◀️", "dic|%s|%d" % (mode, page - 1)))
    nav.append(btn("%d/%d" % (page + 1, total_pages), "dic|noop|%d" % page))
    if page < total_pages - 1:
        nav.append(btn("▶️", "dic|%s|%d" % (mode, page + 1)))
    rows.append(nav)
    rows.append([
        btn("✅", "dic|learned|0"), btn("🤔", "dic|weak|0"),
        btn("💪", "dic|strong|0"), btn("🆕", "dic|ahead|0"),
    ])
    rows.append([btn("📚 По темам", "words|topics"), btn("⬅️ В словарь", "dic|home|0")])
    return "\n".join(lines), inline(rows), total_pages


# --------------------------------------------------------------------------
# Тренажёры
# --------------------------------------------------------------------------

def trainer_intro(kind, title, count, subtitle="", extra=""):
    icons = {"new_words": "🆕", "constructions": "🧩", "mixed": "✍️"}
    lines = [
        "%s <b>%s</b>" % (icons.get(kind, "✍️"), title),
        rule(),
    ]
    if subtitle:
        lines += [subtitle, ""]
    lines.append("Заданий: <b>%d</b>" % count)
    if extra:
        lines += ["", extra]
    lines.append("")
    lines.append("<i>Отвечайте кнопками или текстом — как удобнее.</i>")
    return "\n".join(lines)


def new_words_intro(words_count, count):
    return trainer_intro(
        "new_words", "ПРАКТИКА НОВЫХ СЛОВ", count,
        "Слова из последних уроков: <b>%d</b>" % words_count,
        "<i>Это закрепление: слова уже знакомы, сейчас доводим их до автоматизма.</i>",
    )


def constructions_home(store, user):
    from content import GRAMMAR_BY_ID
    from course import drill_cards_available, clamp_day
    stats = store.drill_stats(user["chat_id"])
    cards = drill_cards_available(clamp_day(user["day"]))
    practiced = sum(1 for card_id in cards if stats.get(card_id))
    text = "\n".join([
        "🧩 <b>ТРЕНАЖЁР КОНСТРУКЦИЙ</b>",
        rule(),
        "Отработка грамматики: подстановка, выбор формы, перевод.",
        "Доступно конструкций: <b>%d</b> · начато: <b>%d</b>" % (len(cards), practiced),
        "",
        "<i>Выберите конструкцию или смешайте всё сразу.</i>",
    ])
    rows = [[btn("🎲 Смешать всё (%d)" % min(len(cards), 8), "drl|mix|0")]]
    for card_id in cards:
        card = GRAMMAR_BY_ID[card_id]
        stat = stats.get(card_id)
        if not stat:
            mark = "▫️"
        elif stat["correct"] >= stat["total"] * 0.8:
            mark = "✅"
        else:
            mark = "🟡"
        title = card["title"]
        if len(title) > 42:
            title = title[:41] + "…"
        rows.append([btn("%s %s" % (mark, title), "drl|card|%s" % card_id)])
    return text, inline(rows)


def drill_result_note(store, user, card_ids):
    from content import GRAMMAR_BY_ID
    stats = store.drill_stats(user["chat_id"])
    lines = ["🧩 <b>Конструкции</b>"]
    for card_id in card_ids:
        stat = stats.get(card_id)
        card = GRAMMAR_BY_ID.get(card_id, {})
        if not stat:
            continue
        percent = round(100.0 * stat["correct"] / stat["total"]) if stat["total"] else 0
        lines.append("• %s — %d%% (%d ответов)" % (
            esc(card.get("title", card_id)), percent, stat["total"]))
    return "\n".join(lines) if len(lines) > 1 else ""
