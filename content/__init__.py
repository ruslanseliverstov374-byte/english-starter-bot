# -*- coding: utf-8 -*-
"""Сборка и проверка контента курса."""

from .words1 import TOPICS as _T1
from .words2 import TOPICS as _T2
from .words3 import TOPICS as _T3
from .words4 import TOPICS as _T4
from .grammar import GRAMMAR
from .phrases import DIALOGUES
from .drills1 import DRILLS as _D1
from .drills2 import DRILLS as _D2
from .plan import (
    WEEKS,
    TOTAL_DAYS,
    TOTAL_WEEKS,
    DAYS_IN_WEEK,
    LESSON_DAYS_IN_WEEK,
    COVER_WEEKS,
)

DRILLS = dict(_D1)
DRILLS.update(_D2)
DRILL_ITEMS = sum(len(d["items"]) for d in DRILLS.values())

TOPICS = list(_T1) + list(_T2) + list(_T3) + list(_T4)

TOPIC_BY_ID = {t["id"]: t for t in TOPICS}
GRAMMAR_BY_ID = {g["id"]: g for g in GRAMMAR}
DIALOGUE_BY_ID = {d["id"]: d for d in DIALOGUES}
WEEK_BY_N = {w["n"]: w for w in WEEKS}


class Word(dict):
    """Слово курса с удобным доступом по ключам."""

    @property
    def en(self):
        return self["en"]

    @property
    def ru(self):
        return self["ru"]

    @property
    def tr(self):
        return self["tr"]

    @property
    def key(self):
        return self["key"]


def _build_words():
    words = []
    for topic in TOPICS:
        for idx, item in enumerate(topic["words"]):
            en, ru, tr, ex_en, ex_ru = item
            words.append(
                Word(
                    key=en.strip().lower(),
                    en=en.strip(),
                    ru=ru.strip(),
                    tr=tr.strip(),
                    ex_en=ex_en.strip(),
                    ex_ru=ex_ru.strip(),
                    topic=topic["id"],
                    topic_title=topic["title"],
                    topic_emoji=topic.get("emoji", "📘"),
                    index_in_topic=idx,
                )
            )
    return words


WORDS = _build_words()
WORD_BY_KEY = {w["key"]: w for w in WORDS}
WORD_INDEX = {w["key"]: i for i, w in enumerate(WORDS)}

# Слова темы, сгруппированные по id (для /words и справочника)
WORDS_BY_TOPIC = {}
for _w in WORDS:
    WORDS_BY_TOPIC.setdefault(_w["topic"], []).append(_w)


def words_for_lesson(lesson_index, per_day=5):
    """Слова для урока № lesson_index (0-базовый) - срез линейной последовательности."""
    start = lesson_index * per_day
    return WORDS[start:start + per_day]


def week_word_pool(week_n):
    """Пул слов недели - все слова тем, закреплённых за неделей."""
    week = WEEK_BY_N.get(week_n)
    if not week:
        return []
    pool = []
    for topic_id in week["topics"]:
        pool.extend(WORDS_BY_TOPIC.get(topic_id, []))
    return pool


def words_for_lesson_day(week_n, dow, per_day=None):
    """Слова урока: день dow (0..5) недели week_n.

    Пул недели делится между её 6 уроками почти поровну (обычно 5-6 слов в день),
    поэтому каждое слово курса попадает ровно в один урок.
    """
    chunks = week_lesson_chunks(week_n)
    if 0 <= dow < len(chunks):
        return chunks[dow]
    return []


def week_lesson_chunks(week_n, days=None):
    """Пул недели, разложенный по урокам недели."""
    days = days or LESSON_DAYS_IN_WEEK
    pool = week_word_pool(week_n)
    chunks = []
    if not pool:
        return [[] for _ in range(days)]
    base, extra = divmod(len(pool), days)
    offset = 0
    for index in range(days):
        size = base + (1 if index < extra else 0)
        chunks.append(pool[offset:offset + size])
        offset += size
    return chunks


def words_learned_after(lesson_index, per_day=5):
    """Все слова, пройденные к началу урока lesson_index (не включая его)."""
    return WORDS[: lesson_index * per_day]


def words_introduced_before(day):
    """Слова, которые уже были в уроках до дня day (сам день не считается)."""
    day = max(1, min(TOTAL_DAYS, int(day or 1)))
    week_n = (day - 1) // DAYS_IN_WEEK + 1
    dow = (day - 1) % DAYS_IN_WEEK
    words = []
    for number in range(1, week_n):
        words.extend(week_word_pool(number))
    chunks = week_lesson_chunks(week_n)
    for index in range(min(dow, len(chunks))):
        words.extend(chunks[index])
    return words


def grammar_cards_with_drills():
    """Грамматические карточки, у которых есть тренажёр конструкций."""
    return [card for card in GRAMMAR if card["id"] in DRILLS]


def validate():
    """Проверка целостности контента. Возвращает список проблем (пусто = всё ок)."""
    problems = []

    seen = {}
    for w in WORDS:
        if w["key"] in seen:
            problems.append("дубликат слова: %s (%s и %s)" % (w["key"], seen[w["key"]], w["topic"]))
        seen[w["key"]] = w["topic"]
        for field in ("en", "ru", "tr", "ex_en", "ex_ru"):
            if not w.get(field):
                problems.append("пустое поле %s у слова %s" % (field, w["key"]))
        if not w["ex_en"].lower().startswith(w["en"].split(" (")[0].lower()[:3]) and \
                w["en"].split(" (")[0].lower() not in w["ex_en"].lower():
            # пример может не содержать слово буквально (например, "I am fine"); это лишь подсказка
            pass

    if len(WORDS) < 200:
        problems.append("слишком мало слов в курсе: %d" % len(WORDS))

    for g in GRAMMAR:
        if g["week"] not in WEEK_BY_N:
            problems.append("грамматика %s ссылается на несуществующую неделю" % g["id"])
        check = g.get("check")
        if check:
            if check["correct"] >= len(check["options"]):
                problems.append("грамматика %s: неверный индекс ответа" % g["id"])
            if len(check["options"]) < 2:
                problems.append("грамматика %s: мало вариантов ответа" % g["id"])

    for d in DIALOGUES:
        if d["week"] not in WEEK_BY_N:
            problems.append("диалог %s ссылается на несуществующую неделю" % d["id"])
        if len(d["lines"]) < 4:
            problems.append("диалог %s: слишком короткий" % d["id"])
        for q in d.get("quiz", []):
            if q["correct"] >= len(q["options"]):
                problems.append("диалог %s: неверный индекс ответа" % d["id"])

    for w in WEEKS:
        for gid in w["grammar"]:
            if gid not in GRAMMAR_BY_ID:
                problems.append("неделя %d: нет грамматики %s" % (w["n"], gid))
            elif GRAMMAR_BY_ID[gid]["week"] != w["n"]:
                problems.append(
                    "неделя %d: карточка %s помечена неделей %d"
                    % (w["n"], gid, GRAMMAR_BY_ID[gid]["week"])
                )
        for did in w["dialogues"]:
            if did not in DIALOGUE_BY_ID:
                problems.append("неделя %d: нет диалога %s" % (w["n"], did))
            elif DIALOGUE_BY_ID[did]["week"] != w["n"]:
                problems.append(
                    "неделя %d: диалог %s помечен неделей %d"
                    % (w["n"], did, DIALOGUE_BY_ID[did]["week"])
                )
        for tid in w["topics"]:
            if tid not in TOPIC_BY_ID:
                problems.append("неделя %d: нет темы %s" % (w["n"], tid))

    # каждая неделя с новыми словами должна давать 6 уроков по 4-8 слов
    used_topics = set()
    covered = set()
    for w in WEEKS:
        pool = week_word_pool(w["n"])
        used_topics.update(w["topics"])
        if not w["topics"]:
            continue                     # итоговая неделя: только повторение
        for chunk in week_lesson_chunks(w["n"]):
            if not 4 <= len(chunk) <= 8:
                problems.append(
                    "неделя %d: в уроке %d слов (нужно 4-8), проверьте темы" % (w["n"], len(chunk))
                )
            covered.update(word["key"] for word in chunk)

    missing = [w["key"] for w in WORDS if w["key"] not in covered]
    if missing:
        problems.append("слова не попадают ни в один урок (%d): %s" % (
            len(missing), ", ".join(missing[:10])))

    unused = set(TOPIC_BY_ID) - used_topics
    if unused:
        problems.append("темы не входят ни в одну неделю: %s" % ", ".join(sorted(unused)))

    # тренажёр конструкций
    for card_id, drill in DRILLS.items():
        if card_id not in GRAMMAR_BY_ID:
            problems.append("тренажёр ссылается на несуществующую карточку: %s" % card_id)
            continue
        items = drill.get("items") or []
        if len(items) < 4:
            problems.append("тренажёр %s: только %d заданий (нужно 4+)" % (card_id, len(items)))
        for index, item in enumerate(items):
            where = "%s[%d]" % (card_id, index)
            if not item.get("q"):
                problems.append("тренажёр %s: пустой вопрос" % where)
            if "answer" in item:
                if not item["answer"]:
                    problems.append("тренажёр %s: пустой ответ" % where)
            else:
                options = item.get("options") or []
                if len(options) < 2:
                    problems.append("тренажёр %s: меньше двух вариантов" % where)
                if not isinstance(item.get("correct"), int) or not 0 <= item["correct"] < len(options):
                    problems.append("тренажёр %s: неверный индекс ответа" % where)
                if len(set(options)) != len(options):
                    problems.append("тренажёр %s: повторяющиеся варианты" % where)

    no_drills = [card["id"] for card in GRAMMAR if card["id"] not in DRILLS]
    if len(no_drills) > 4:
        problems.append("у %d карточек нет тренажёра: %s" % (len(no_drills), ", ".join(no_drills)))

    duplicated_topics = []
    for w in WEEKS:
        for tid in w["topics"]:
            if sum(1 for other in WEEKS if tid in other["topics"]) > 1:
                duplicated_topics.append(tid)
    if duplicated_topics:
        problems.append("темы повторяются в нескольких неделях: %s" % ", ".join(sorted(set(duplicated_topics))))

    return problems


STATS = {
    "topics": len(TOPICS),
    "words": len(WORDS),
    "grammar": len(GRAMMAR),
    "dialogues": len(DIALOGUES),
    "weeks": TOTAL_WEEKS,
    "days": TOTAL_DAYS,
    "drill_cards": len(DRILLS),
    "drill_items": DRILL_ITEMS,
}
