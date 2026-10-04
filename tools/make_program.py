# -*- coding: utf-8 -*-
"""Генератор документа с программой курса: PROGRAM.md и PROGRAM.docx.

Документ собирается из того же контента, что и бот, поэтому программа
в документе всегда совпадает с тем, что реально приходит в Telegram.

Запуск:
    python tools/make_program.py            # только PROGRAM.md
    python tools/make_program.py --docx     # ещё и PROGRAM.docx (нужен python-docx)
"""

import os
import sys

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE)

from content import (                                   # noqa: E402
    DIALOGUE_BY_ID,
    GRAMMAR_BY_ID,
    STATS,
    TOPIC_BY_ID,
    TOTAL_DAYS,
    WEEKS,
    week_word_pool,
)
from course import LESSON_DAYS_IN_WEEK, SRS_INTERVALS, plan_for_day   # noqa: E402

MD_PATH = os.path.join(BASE, "PROGRAM.md")
DOCX_PATH = os.path.join(BASE, "PROGRAM.docx")

TITLE = "English Starter: программа курса английского с нуля до уровня A1"


# --------------------------------------------------------------------------
# данные для документа
# --------------------------------------------------------------------------

def plural(number, one, few, many):
    """Русское склонение: 1 слово, 2 слова, 5 слов."""
    number = abs(int(number))
    if number % 10 == 1 and number % 100 != 11:
        return "%d %s" % (number, one)
    if 2 <= number % 10 <= 4 and not 12 <= number % 100 <= 14:
        return "%d %s" % (number, few)
    return "%d %s" % (number, many)


def week_rows():
    rows = []
    for week in WEEKS:
        first = (week["n"] - 1) * 7 + 1
        last = first + 6
        pool = week_word_pool(week["n"])
        topics = ", ".join(
            "%s (%s)" % (TOPIC_BY_ID[t]["title"],
                         plural(len(TOPIC_BY_ID[t]["words"]), "слово", "слова", "слов"))
            for t in week["topics"]
        )
        if pool:
            topics = "%s — всего %s" % (topics, plural(len(pool), "слово", "слова", "слов"))
        else:
            topics = "новых слов нет — повторение всего курса"
        grammar = "; ".join(GRAMMAR_BY_ID[g]["title"] for g in week["grammar"])
        dialogues = "; ".join(DIALOGUE_BY_ID[d]["title"] for d in week["dialogues"])
        rows.append({
            "n": week["n"],
            "days": "%d–%d" % (first, last),
            "title": week["title"],
            "focus": week["focus"],
            "topics": topics,
            "grammar": grammar,
            "dialogue": dialogues,
            "goal": week["goal"],
        })
    return rows


def first_week_days():
    rows = []
    for day in range(1, 8):
        plan = plan_for_day(day)
        words = ", ".join(w["en"] for w in plan["new_words"]) or "— (повторение и тест недели)"
        grammar = plan["grammar"]["title"] if plan.get("grammar") else "—"
        rows.append([
            "День %d" % day,
            "повторение %s" % ("+ тест" if plan["is_review"] else "старых слов"),
            words,
            grammar,
        ])
    return rows


# --------------------------------------------------------------------------
# модель документа
# --------------------------------------------------------------------------

def build_blocks():
    blocks = []
    add = blocks.append

    add(("title", TITLE))
    add(("subtitle", "12 недель · 84 занятия по 10 минут · Telegram-бот English Starter"))

    add(("h1", "1. Что вы получите"))
    add(("para",
         "Курс рассчитан на старт с абсолютного нуля и доводит до уровня A1: "
         "вы научитесь читать, представиться, рассказать о себе и семье, заказать еду, "
         "объяснить дорогу, поговорить о работе, планах и о том, что было вчера."))
    add(("bullets", [
        "%s с переводом, русской транскрипцией и примером употребления." % plural(
            STATS["words"], "слово", "слова", "слов").capitalize(),
        "%s — по одной на урок, каждая на 60–90 секунд чтения." % plural(
            STATS["grammar"], "грамматическая карточка", "грамматические карточки", "грамматических карточек").capitalize(),
        "%s на бытовые ситуации: знакомство, кафе, магазин, врач, отель, аэропорт." % plural(
            STATS["dialogues"], "диалог", "диалога", "диалогов").capitalize(),
        "%s (семья, еда, время, город, работа, путешествия и другие)." % plural(
            STATS["topics"], "тематический блок", "тематических блока", "тематических блоков").capitalize(),
        "Интервальное повторение: каждое слово возвращается через 1, 2, 4, 8, 16, 32 дня — "
        "ровно перед тем, как забыться.",
        "Упражнения 7 типов: выбор перевода, перевод в обе стороны, ввод слова текстом, "
        "пропущенное слово в предложении, чтение транскрипции, порядок слов, проверка грамматики.",
        "Двенадцать коротких тестов (по одному в неделю) и итоговый экзамен A1 на 12-й неделе.",
    ]))

    add(("h1", "2. Формат одного занятия (10 минут)"))
    add(("table", {
        "headers": ["Шаг", "Что происходит", "Время"],
        "rows": [
            ["1. Повторение", "5 слов из очереди повторения: вспомнить перевод, оценить себя, "
                              "интервал пересчитывается автоматически", "3 мин"],
            ["2. Новые слова", "5–6 новых слов: слово, транскрипция, перевод, пример с переводом, "
                               "проговорить вслух", "3 мин"],
            ["3. Грамматика", "Одна карточка: правило по-русски, 3 примера, подсказка-запоминалка", "1 мин"],
            ["4. Практика", "4 упражнения по сегодняшним и старым словам, ответы кнопками или текстом", "2 мин"],
            ["5. Диалог дня", "Готовый диалог по теме недели: прочитать вслух за обе стороны", "1 мин"],
        ],
    }))
    add(("para",
         "Каждый 7-й день недели — день повторения и теста: 12 карточек повторения, "
         "10 вопросов по всей неделе, диалог и итоги. Новых слов в этот день нет."))
    add(("para",
         "Программа курса одинаковая для всех режимов. Режим меняет только объём практики: "
         "«10 минут» — 5 карточек повторения и 4 упражнения, «20 минут» — 10 и 7, "
         "«40 минут» — 15 и 10. Слова при этом учите те же и в том же порядке."))

    add(("h1", "3. Программа по неделям"))
    add(("para",
         "Для каждой недели: дни курса, тема, слова, грамматика, диалог и результат, "
         "который вы получаете к концу недели."))
    for row in week_rows():
        add(("week", row))
        add(("table", {
            "headers": ["Что", "Содержание недели"],
            "rows": [
                ["Дни курса", row["days"]],
                ["Тема", "%s. %s" % (row["title"], row["focus"])],
                ["Слова", row["topics"]],
                ["Грамматика", row["grammar"]],
                ["Диалог", row["dialogue"]],
                ["Умею к концу недели", row["goal"]],
            ],
            "widths": [4.0, 13.0],
        }))

    add(("h1", "4. Как выглядит первая неделя"))
    add(("table", {
        "headers": ["День", "Повторение", "Новые слова", "Грамматика"],
        "rows": first_week_days(),
        "widths": [1.6, 3.4, 7.0, 6.4],
    }))

    add(("h1", "5. Методика: почему это работает"))
    add(("bullets", [
        "Активное припоминание. Бот не показывает перевод сразу: сначала вы вспоминаете сами, "
        "потом нажимаете «Показать перевод» и честно оцениваете себя.",
        "Интервальное повторение (SRS). Оценка «не помню» возвращает слово в конец очереди, "
        "«помню» увеличивает интервал: 1 → 2 → 4 → 8 → 16 → 32 → 64 дня.",
        "Ошибка в упражнении тоже работает: слово автоматически возвращается в очередь повторения.",
        "Два канала памяти: выбор варианта (узнавание) и ввод слова текстом (воспроизведение). "
        "Ввод текста — самое ценное упражнение, не пропускайте его.",
        "Опора на родной язык. Все объяснения грамматики — по-русски, у каждого слова есть "
        "русская транскрипция, пока чтение не станет автоматическим.",
        "Диалоги вслух. Курс учит не «знать слова», а говорить: каждый диалог нужно прочитать "
        "за обе роли.",
        "Короткие занятия. 10 минут ежедневно эффективнее двух часов раз в неделю.",
    ]))

    add(("h1", "6. Контроль и прогресс"))
    add(("table", {
        "headers": ["Когда", "Что проверяется", "Как"],
        "rows": [
            ["Каждый 7-й день", "Слова и грамматика недели", "Тест 10 вопросов + повторение слабых слов"],
            ["Каждый день", "Точность ответов, серия дней", "Команда /progress: процент, стрик, слабые слова"],
            ["Любой момент", "Знание случайных слов", "Команда /quiz: 10 быстрых вопросов"],
            ["День 84", "Весь курс", "Экзамен A1: тест по всем темам, затем итоговая сводка"],
        ],
    }))

    add(("h1", "7. Что требуется от вас"))
    add(("bullets", [
        "10 минут в день. Лучше утром: бот присылает напоминание в выбранное время.",
        "Отвечать честно. Если не помните — нажмите «не помню»: так курс подстроится под вас.",
        "Не пропускать ввод текста. Кнопки — это узнавание, текст — настоящее знание.",
        "Проговаривать слова и диалоги вслух, даже шёпотом.",
        "Если пропустили день — просто продолжайте. День курса не «сгорает»: бот продолжит "
        "с того места, где вы остановились, а накопленные слова дождутся вас в очереди повторения.",
    ]))

    add(("h1", "8. Что дальше, после A1"))
    add(("para",
         "На 84-й день курс завершается итоговым тестом. Следующий блок — A2:"))
    add(("bullets", [
        "Present Perfect и разница с Past Simple.",
        "Условные предложения (if I have time, I will...), модальные глаголы в прошлом.",
        "Фразовые глаголы и устойчивые выражения (get up, look for, take care of).",
        "Аудирование: короткие диалоги и подкасты, работа над беглостью речи.",
        "Письмо: короткие сообщения, письма, резюме.",
        "Разговорная практика: 10 тем для speaking с готовыми вопросами.",
    ]))

    add(("h1", "9. Чек-лист прохождения курса"))
    add(("para", "Отмечайте пройденные недели, чтобы видеть путь целиком."))
    add(("table", {
        "headers": ["Неделя", "Тема", "Дни", "Пройдено"],
        "rows": [[str(row["n"]), row["title"], row["days"], "☐"] for row in week_rows()],
        "widths": [1.6, 8.0, 2.4, 2.4],
    }))

    add(("h1", "10. Технические факты о курсе"))
    add(("table", {
        "headers": ["Параметр", "Значение"],
        "rows": [
            ["Длительность", "%d дней (12 недель)" % TOTAL_DAYS],
            ["Новых слов", "%d" % STATS["words"]],
            ["Грамматических карточек", "%d" % STATS["grammar"]],
            ["Диалогов", "%d" % STATS["dialogues"]],
            ["Тем", "%d" % STATS["topics"]],
            ["Интервалы повторения", ", ".join("%d дн." % d for d in SRS_INTERVALS[1:])],
            ["Уроков с новыми словами", "%d из %d" % (
                sum(1 for day in range(1, TOTAL_DAYS + 1)
                    if plan_for_day(day)["new_words"] and not plan_for_day(day)["consolidation"]),
                TOTAL_DAYS)],
            ["Первое занятие", "День 1 — «%s»" % WEEKS[0]["title"]],
        ],
        "widths": [6.0, 11.0],
    }))

    return blocks


# --------------------------------------------------------------------------
# вывод: Markdown
# --------------------------------------------------------------------------

def render_markdown(blocks):
    lines = []
    for kind, content in blocks:
        if kind == "title":
            lines += ["# %s" % content, ""]
        elif kind == "subtitle":
            lines += ["*%s*" % content, ""]
        elif kind == "h1":
            lines += ["", "## %s" % content, ""]
        elif kind == "week":
            lines += ["", "### Неделя %s — %s (дни %s)" % (content["n"], content["title"], content["days"]), ""]
        elif kind == "para":
            lines += [content, ""]
        elif kind == "bullets":
            lines += ["- %s" % item for item in content] + [""]
        elif kind == "table":
            headers = content["headers"]
            rows = content["rows"]
            lines.append("| %s |" % " | ".join(headers))
            lines.append("|%s|" % "|".join(["---"] * len(headers)))
            for row in rows:
                cells = [str(cell).replace("\n", " ") for cell in row]
                lines.append("| %s |" % " | ".join(cells))
            lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("Документ сгенерирован из контента бота (`python tools/make_program.py`), "
                 "поэтому программа здесь всегда совпадает с тем, что приходит в Telegram.")
    return "\n".join(lines)


# --------------------------------------------------------------------------
# вывод: DOCX
# --------------------------------------------------------------------------

def render_docx(blocks, path):
    from docx import Document
    from docx.enum.text import WD_ALIGN_PARAGRAPH
    from docx.shared import Pt, Cm, RGBColor

    document = Document()
    section = document.sections[0]
    section.top_margin = Cm(1.8)
    section.bottom_margin = Cm(1.8)
    section.left_margin = Cm(1.8)
    section.right_margin = Cm(1.5)

    style = document.styles["Normal"]
    style.font.name = "Calibri"
    style.font.size = Pt(10)

    for kind, content in blocks:
        if kind == "title":
            heading = document.add_heading(content, level=0)
            heading.alignment = WD_ALIGN_PARAGRAPH.LEFT
        elif kind == "subtitle":
            paragraph = document.add_paragraph()
            run = paragraph.add_run(content)
            run.italic = True
            run.font.size = Pt(11)
            run.font.color.rgb = RGBColor(0x44, 0x44, 0x44)
        elif kind == "h1":
            document.add_heading(content, level=1)
        elif kind == "week":
            heading = document.add_heading(
                "Неделя %s — %s (дни %s)" % (content["n"], content["title"], content["days"]),
                level=2,
            )
            for run in heading.runs:
                run.font.size = Pt(13)
        elif kind == "para":
            document.add_paragraph(content)
        elif kind == "bullets":
            for item in content:
                document.add_paragraph(item, style="List Bullet")
        elif kind == "table":
            headers = content["headers"]
            rows = content["rows"]
            table = document.add_table(rows=1, cols=len(headers))
            table.style = "Light Grid Accent 1"
            for index, header in enumerate(headers):
                cell = table.rows[0].cells[index]
                cell.text = ""
                run = cell.paragraphs[0].add_run(header)
                run.bold = True
                run.font.size = Pt(9)
            for row in rows:
                cells = table.add_row().cells
                for index, value in enumerate(row):
                    cells[index].text = ""
                    run = cells[index].paragraphs[0].add_run(str(value))
                    run.font.size = Pt(8.5)
            widths = content.get("widths")
            if widths:
                for row in table.rows:
                    for index, width in enumerate(widths):
                        if index < len(row.cells):
                            row.cells[index].width = Cm(width)
            document.add_paragraph()

    document.save(path)
    return path


def main(argv):
    blocks = build_blocks()
    markdown = render_markdown(blocks)
    with open(MD_PATH, "w", encoding="utf-8") as handle:
        handle.write(markdown)
    print("Сохранено: %s (%d символов)" % (MD_PATH, len(markdown)))

    if "--docx" in argv:
        render_docx(blocks, DOCX_PATH)
        print("Сохранено: %s" % DOCX_PATH)
    return 0


if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    sys.exit(main(sys.argv[1:]))
