# -*- coding: utf-8 -*-
"""Логика курса: план дня, интервальное повторение, генерация упражнений и проверка ответов."""

import random
import re
from datetime import timedelta

from content import (
    DIALOGUE_BY_ID,
    DRILLS,
    GRAMMAR_BY_ID,
    TOTAL_DAYS,
    TOTAL_WEEKS,
    WEEK_BY_N,
    WORDS,
    WORD_BY_KEY,
    week_lesson_chunks,
    week_word_pool,
    words_for_lesson_day,
    words_introduced_before,
)
from store import iso, utcnow

# Интервалы повторения по «коробкам» (в днях). box 0 - повторить почти сразу.
SRS_INTERVALS = [0, 1, 2, 4, 8, 16, 32, 64]

DAYS_IN_WEEK = 7
LESSON_DAYS_IN_WEEK = 6

# Режим занятий: сколько слов повторяем в уроке и сколько упражнений даём.
# Программа курса одинаковая, отличается только объём практики.
MODE_LIMITS = {
    "light": (5, 4),
    "standard": (10, 7),
    "intensive": (15, 10),
}


def practice_settings(user):
    """(сколько карточек повторения, сколько упражнений) для режима пользователя."""
    return MODE_LIMITS.get((user or {}).get("mode") or "light", MODE_LIMITS["light"])


# --------------------------------------------------------------------------
# Календарь курса
# --------------------------------------------------------------------------

def clamp_day(day):
    return max(1, min(TOTAL_DAYS, int(day or 1)))


def week_of_day(day):
    return (clamp_day(day) - 1) // DAYS_IN_WEEK + 1


def dow_of_day(day):
    """0..5 - учебный день недели, 6 - день повторения и теста."""
    return (clamp_day(day) - 1) % DAYS_IN_WEEK


def is_review_day(day):
    return dow_of_day(day) == LESSON_DAYS_IN_WEEK


def lesson_index_of_day(day):
    """Номер учебного дня (0-базовый) или None для дня повторения."""
    if is_review_day(day):
        return None
    return (week_of_day(day) - 1) * LESSON_DAYS_IN_WEEK + dow_of_day(day)


def plan_for_day(day, per_day=5):
    """Что учим в конкретный день курса."""
    day = clamp_day(day)
    week_n = week_of_day(day)
    dow = dow_of_day(day)
    week = WEEK_BY_N[week_n]

    plan = {
        "day": day,
        "week": week_n,
        "week_title": week["title"],
        "focus": week["focus"],
        "goal": week["goal"],
        "dow": dow,
        "is_review": is_review_day(day),
        "consolidation": False,
        "new_words": [],
        "grammar": None,
        "dialogue": None,
    }

    cards = [GRAMMAR_BY_ID[g] for g in week["grammar"]]

    if plan["is_review"]:
        plan["dialogue"] = DIALOGUE_BY_ID[week["dialogues"][0]]
        if cards:
            plan["grammar"] = cards[dow % len(cards)]
        return plan

    plan["new_words"] = words_for_lesson_day(week_n, dow)
    if not plan["new_words"]:
        # итоговая неделя: новых слов нет, идёт повторение всего курса
        plan["consolidation"] = True
        plan["is_review"] = True

    if cards:
        idx = min(dow * len(cards) // LESSON_DAYS_IN_WEEK, len(cards) - 1)
        plan["grammar"] = cards[idx]

    dialogues = [DIALOGUE_BY_ID[d] for d in week["dialogues"]]
    if dialogues:
        if len(dialogues) > 1 and dow == 2:
            plan["dialogue"] = dialogues[0]
        elif dow == LESSON_DAYS_IN_WEEK - 1:
            plan["dialogue"] = dialogues[-1]

    return plan


def course_progress(day):
    day = clamp_day(day)
    return {
        "day": day,
        "total_days": TOTAL_DAYS,
        "week": week_of_day(day),
        "total_weeks": TOTAL_WEEKS,
        "percent": round(100.0 * (day - 1) / TOTAL_DAYS),
    }


# --------------------------------------------------------------------------
# Интервальное повторение (SRS)
# --------------------------------------------------------------------------

def grade_srs(store, chat_id, word_key, grade):
    """grade: 0 - не помню, 1 - помню, 2 - легко."""
    row = store.srs_row(chat_id, word_key) or {}
    box = row.get("box") or 0
    reps = row.get("reps") or 0
    lapses = row.get("lapses") or 0
    now = utcnow()

    if grade <= 0:
        box = 0
        lapses += 1
        due = now + timedelta(minutes=15)
    else:
        box = min(box + (2 if grade >= 2 else 1), len(SRS_INTERVALS) - 1)
        due = now + timedelta(days=SRS_INTERVALS[box])

    store.upsert_srs(
        chat_id,
        word_key,
        box=box,
        reps=reps + 1,
        lapses=lapses,
        due_at=iso(due),
        last_seen=iso(now),
        learned=1,
    )
    return {"box": box, "due": due, "days": SRS_INTERVALS[box]}


def register_new_word(store, chat_id, word_key):
    """Новое слово: первый повтор - завтра."""
    row = store.srs_row(chat_id, word_key)
    if row and row.get("learned"):
        return
    store.upsert_srs(
        chat_id,
        word_key,
        box=1,
        reps=1,
        due_at=iso(utcnow() + timedelta(days=SRS_INTERVALS[1])),
        last_seen=iso(utcnow()),
        learned=1,
    )


def interval_label(box):
    days = SRS_INTERVALS[max(0, min(box, len(SRS_INTERVALS) - 1))]
    if days == 0:
        return "скоро"
    if days == 1:
        return "завтра"
    if days % 7 == 0 and days >= 14:
        return "через %d нед." % (days // 7)
    return "через %d дн." % days


def build_review_queue(store, chat_id, limit):
    """Сначала просроченные, потом самые слабые слова - чтобы очередь не пустовала."""
    due = store.due_words(chat_id, limit)
    if len(due) < limit:
        extra = store.weakest_words(chat_id, limit - len(due), exclude=tuple(due))
        due.extend(extra)
    return due


# --------------------------------------------------------------------------
# Проверка ответов
# --------------------------------------------------------------------------

def normalize(text):
    text = (text or "").strip().lower()
    text = text.replace("’", "'")
    text = re.sub(r"[.,!?;:\"()\[\]]", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def levenshtein(a, b):
    if a == b:
        return 0
    if not a:
        return len(b)
    if not b:
        return len(a)
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i]
        for j, cb in enumerate(b, 1):
            cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (ca != cb)))
        prev = cur
    return prev[-1]


def check_typed(answer, expected, accept=()):
    """Возвращает (правильно, заметка). Терпимо к регистру, знакам и одной опечатке."""
    got = normalize(answer)
    variants = [normalize(expected)] + [normalize(v) for v in accept if v]
    variants = [v for v in variants if v]
    if not got:
        return False, "Пустой ответ."
    if got in variants:
        return True, ""
    for v in variants:
        if len(v) >= 3 and (got == v or (len(got) >= 4 and (got in v or v in got))):
            return True, ""
    best = min((levenshtein(got, v) for v in variants), default=99)
    shortest = min((len(v) for v in variants), default=99)
    if best <= 1 and shortest >= 5:
        return True, "Почти! Пишется так: %s" % expected
    return False, ""


def ru_variants(word):
    return [p.strip() for p in word["ru"].split(",") if p.strip()]


# --------------------------------------------------------------------------
# Генерация упражнений
# --------------------------------------------------------------------------

def _pick_distractors(correct, pool, n, rng):
    options = [correct]
    candidates = [p for p in pool if p and p != correct]
    rng.shuffle(candidates)
    for item in candidates:
        if len(options) >= n:
            break
        if item not in options:
            options.append(item)
    return options


def _mc(prompt, correct_text, pool, rng, explain, word_key=None, kind="mc", n=4):
    options = _pick_distractors(correct_text, pool, n, rng)
    if correct_text not in options:
        options[0] = correct_text
    rng.shuffle(options)
    return {
        "kind": kind,
        "prompt": prompt,
        "options": options,
        "correct": options.index(correct_text),
        "explain": explain,
        "word_key": word_key,
    }


def q_choose_ru(word, rng):
    pool = [w["ru"] for w in WORDS]
    explain = "%s — %s\nПример: %s (%s)" % (word["en"], word["ru"], word["ex_en"], word["ex_ru"])
    return _mc(
        "Что значит <b>%s</b>?\n<i>%s</i>" % (word["en"], word["tr"]),
        word["ru"], pool, rng, explain, word["key"],
    )


def q_choose_en(word, rng):
    pool = [w["en"] for w in WORDS]
    explain = "%s — %s\nПример: %s (%s)" % (word["ru"], word["en"], word["ex_en"], word["ex_ru"])
    return _mc(
        "Как сказать по-английски: <b>%s</b>?" % word["ru"],
        word["en"], pool, rng, explain, word["key"],
    )


def q_reading(word, rng):
    pool = [w["tr"] for w in WORDS]
    explain = "%s читается как [%s] — %s" % (word["en"], word["tr"], word["ru"])
    return _mc(
        "Как читается <b>%s</b>?" % word["en"],
        word["tr"], pool, rng, explain, word["key"],
    )


def q_gap(word, rng):
    base = word["en"].split(" (")[0]
    sentence = word["ex_en"]
    if base.lower() not in sentence.lower() or len(base) < 3:
        return q_choose_ru(word, rng)
    pattern = re.compile(re.escape(base), re.IGNORECASE)
    gapped = pattern.sub("___", sentence, count=1)
    pool = [w["en"] for w in WORDS]
    explain = "Правильно: %s\n%s — %s" % (sentence, word["en"], word["ru"])
    return _mc(
        "Вставь пропущенное слово:\n<i>%s</i>\n(%s)" % (gapped, word["ex_ru"]),
        word["en"], pool, rng, explain, word["key"],
    )


def q_order(word, rng):
    sentence = word["ex_en"]
    tokens = sentence.split()
    if len(tokens) < 3 or len(tokens) > 8:
        return q_choose_en(word, rng)
    correct_text = " ".join(tokens)
    variants = []
    for _ in range(6):
        shuffled = tokens[:]
        rng.shuffle(shuffled)
        candidate = " ".join(shuffled)
        if candidate != correct_text and candidate not in variants:
            variants.append(candidate)
        if len(variants) == 3:
            break
    if not variants:
        return q_choose_en(word, rng)
    options = [correct_text] + variants[:3]
    rng.shuffle(options)
    return {
        "kind": "mc",
        "prompt": "Собери предложение правильно:\n<i>%s</i>" % word["ex_ru"],
        "options": options,
        "correct": options.index(correct_text),
        "explain": "Правильный порядок: %s\n(%s)" % (correct_text, word["ex_ru"]),
        "word_key": word["key"],
    }


def q_type_en(word):
    return {
        "kind": "type",
        "prompt": "Напишите по-английски: <b>%s</b>" % word["ru"],
        "answer": word["en"],
        "accept": [],
        "explain": "%s — %s\nПример: %s" % (word["en"], word["ru"], word["ex_en"]),
        "word_key": word["key"],
    }


def q_type_ru(word):
    return {
        "kind": "type",
        "prompt": "Переведите на русский: <b>%s</b>\n<i>%s</i>" % (word["en"], word["tr"]),
        "answer": ru_variants(word)[0],
        "accept": ru_variants(word)[1:],
        "explain": "%s — %s" % (word["en"], word["ru"]),
        "word_key": word["key"],
    }


def q_grammar(card):
    check = card.get("check")
    if not check:
        return None
    options = list(check["options"])
    correct_text = options[check["correct"]]
    return {
        "kind": "mc",
        "prompt": "Грамматика: <b>%s</b>\n%s" % (card["title"], check["q"]),
        "options": options,
        "correct": check["correct"],
        "explain": correct_text + ". " + (card.get("tip") or ""),
        "word_key": None,
        "grammar_id": card["id"],
    }


def q_dialogue(dialogue, rng):
    quiz = dialogue.get("quiz") or []
    if not quiz:
        return None
    item = rng.choice(quiz)
    options = list(item["options"])
    return {
        "kind": "mc",
        "prompt": "Диалог «%s»: %s" % (dialogue["title"], item["q"]),
        "options": options,
        "correct": item["correct"],
        "explain": (dialogue.get("note") or "") + "\nПравильно: " + options[item["correct"]],
        "word_key": None,
    }


TYPE_CYCLE = ["choose_ru", "type_en", "choose_en", "gap", "reading", "type_ru", "order"]


def build_questions_for_words(word_keys, rng, count=None):
    """Упражнения по конкретным словам (по одному на слово, тип меняется)."""
    questions = []
    for i, key in enumerate(word_keys):
        word = WORD_BY_KEY.get(key)
        if not word:
            continue
        kind = TYPE_CYCLE[i % len(TYPE_CYCLE)]
        if kind == "choose_ru":
            questions.append(q_choose_ru(word, rng))
        elif kind == "choose_en":
            questions.append(q_choose_en(word, rng))
        elif kind == "type_en":
            questions.append(q_type_en(word))
        elif kind == "type_ru":
            questions.append(q_type_ru(word))
        elif kind == "reading":
            questions.append(q_reading(word, rng))
        elif kind == "gap":
            questions.append(q_gap(word, rng))
        else:
            questions.append(q_order(word, rng))
    if count:
        questions = questions[:count]
    return questions


def build_lesson_exercises(plan, rng, review_words=(), count=4):
    """Упражнения урока: грамматика + новые слова + (если есть) диалог."""
    questions = []
    card = plan.get("grammar")
    if card:
        gq = q_grammar(card)
        if gq:
            questions.append(gq)

    keys = [w["key"] for w in plan["new_words"]]
    pool = list(keys) + list(review_words)
    rng.shuffle(pool)
    word_questions = max(1, count - len(questions) - (1 if plan.get("dialogue") else 0))
    questions.extend(build_questions_for_words(pool[:word_questions], rng))

    dialogue = plan.get("dialogue")
    if dialogue:
        dq = q_dialogue(dialogue, rng)
        if dq:
            questions.append(dq)

    rng.shuffle(questions)
    return questions[:max(count, 1)]


def build_test_questions(store, chat_id, day, rng, count=10):
    """Тест дня повторения: слова всей недели + грамматика и диалог недели."""
    week_n = week_of_day(day)
    week = WEEK_BY_N[week_n]
    keys = [w["key"] for w in week_word_pool(week_n)]
    if len(keys) < count:
        # итоговая неделя (новых слов нет) - берём слабые слова всего курса
        extra = store.weakest_words(chat_id, count * 2, exclude=tuple(keys))
        keys.extend(extra)
    rng.shuffle(keys)
    keys = keys[: max(3, count - 3)]

    questions = build_questions_for_words(keys, rng)
    for gid in week["grammar"][:2]:
        gq = q_grammar(GRAMMAR_BY_ID[gid])
        if gq:
            questions.append(gq)
    for did in week["dialogues"][:1]:
        dq = q_dialogue(DIALOGUE_BY_ID[did], rng)
        if dq:
            questions.append(dq)
    rng.shuffle(questions)
    return questions[:count]


def build_quiz_questions(store, chat_id, rng, count=10):
    """/quiz - случайные вопросы по уже пройденным словам."""
    learned = [w["key"] for w in WORDS if (store.srs_row(chat_id, w["key"]) or {}).get("learned")]
    if not learned:
        return []
    rng.shuffle(learned)
    questions = build_questions_for_words(learned[:count], rng)
    rng.shuffle(questions)
    return questions


# --------------------------------------------------------------------------
# Тренажёры: новые слова, конструкции, смешанная практика
# --------------------------------------------------------------------------

def recent_new_words(day, limit=12):
    """Последние изученные слова: то, что уже было в уроках до текущего дня."""
    words = words_introduced_before(day)
    return words[-limit:] if words else []


def build_new_words_questions(store, chat_id, day, rng, count=4):
    """Практика последних новых слов."""
    words = recent_new_words(day, limit=max(count * 2, 10))
    if not words:
        return []
    keys = [w["key"] for w in words]
    rng.shuffle(keys)
    questions = build_questions_for_words(keys, rng)
    rng.shuffle(questions)
    return questions[:count]


def drill_cards_available(day):
    """Конструкции, которые уже встречались в уроках к текущему дню."""
    current_week = week_of_day(day)
    cards = []
    for number in range(1, current_week + 1):
        for card_id in WEEK_BY_N[number]["grammar"]:
            if card_id in DRILLS and card_id not in cards:
                cards.append(card_id)
    return cards


def _drill_question(item, card_id, rng):
    card = GRAMMAR_BY_ID.get(card_id, {})
    head = "🧩 <b>Конструкция:</b> %s" % card.get("title", "тренажёр")
    tip = card.get("tip") or ""
    if "answer" in item:
        return {
            "kind": "type",
            "prompt": "%s\n\n%s" % (head, item["q"]),
            "answer": item["answer"],
            "accept": item.get("accept", []),
            "explain": ("Правильно: <b>%s</b>" % item["answer"]) + (("\n💡 " + tip) if tip else ""),
            "word_key": None,
            "grammar_id": card_id,
        }
    options = list(item["options"])
    correct_text = options[item["correct"]]
    rng.shuffle(options)
    return {
        "kind": "mc",
        "prompt": "%s\n\n%s" % (head, item["q"]),
        "options": options,
        "correct": options.index(correct_text),
        "explain": ("Правильно: <b>%s</b>" % correct_text) + (("\n💡 " + tip) if tip else ""),
        "word_key": None,
        "grammar_id": card_id,
    }


def build_drill_questions(card_id, rng, count=6):
    """Упражнения по одной конструкции."""
    items = list((DRILLS.get(card_id) or {}).get("items") or [])
    if not items:
        return []
    rng.shuffle(items)
    return [_drill_question(item, card_id, rng) for item in items[:count]]


def build_mixed_drill_questions(card_ids, rng, count=8, exclude=()):
    """Упражнения сразу по нескольким конструкциям."""
    pairs = []
    for card_id in card_ids:
        for item in (DRILLS.get(card_id) or {}).get("items") or []:
            if item["q"] in exclude:
                continue
            pairs.append((card_id, item))
    rng.shuffle(pairs)
    return [_drill_question(item, card_id, rng) for card_id, item in pairs[:count]]


def build_mixed_questions(store, user, rng, count=4):
    """Смешанная практика: слова + конструкции + диалог недели."""
    day = clamp_day(user["day"])
    questions = []

    word_budget = max(1, count // 2)
    questions.extend(build_new_words_questions(store, chat_id=user["chat_id"], day=day,
                                               rng=rng, count=word_budget))
    weakest = store.weakest_words(user["chat_id"], max(1, count // 3))
    if weakest:
        questions.extend(build_questions_for_words(weakest, rng))
        questions = questions[:count]

    cards = drill_cards_available(day)
    if cards and len(questions) < count:
        questions.extend(build_mixed_drill_questions(cards, rng, count - len(questions)))

    week = WEEK_BY_N[week_of_day(day)]
    if len(questions) < count and week["dialogues"]:
        dialogue_question = q_dialogue(DIALOGUE_BY_ID[week["dialogues"][0]], rng)
        if dialogue_question:
            questions.append(dialogue_question)

    rng.shuffle(questions)
    return questions[:count]
