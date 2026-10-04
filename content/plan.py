# -*- coding: utf-8 -*-
"""План курса: 12 недель по 7 дней (6 уроков + 1 день повторения и теста).

Как собирается урок дня:
  - у каждой недели свой ПУЛ слов - слова тем, перечисленных в "topics";
  - урок №k недели берёт из пула слова [k*5 : (k+1)*5] (5 слов в день при режиме «10 минут»);
  - грамматика и диалог - из своей недели;
  - 7-й день недели - повторение (SRS), тест недели и диалог;
  - 12-я неделя - итоговая: новых слов нет, идёт повторение всего курса и экзамен A1.

Всего: 33 темы, 360 слов, 34 грамматические карточки, 14 диалогов.
"""

WEEKS = [
    {
        "n": 1,
        "title": "Чтение и первые слова",
        "focus": "Алфавит, правила чтения, порядок слов; приветствия, числа, цвета",
        "topics": ["greetings", "numbers", "colors"],
        "grammar": ["reading_basics", "syllables", "digraphs", "word_order"],
        "dialogues": ["first_hello"],
        "goal": "Читаю знакомые слова вслух, считаю до 100, говорю 5 фраз приветствия",
    },
    {
        "n": 2,
        "title": "Я и моя семья",
        "focus": "to be (am/is/are), вопросы и отрицания, местоимения, знакомство",
        "topics": ["people", "family", "intro"],
        "grammar": ["to_be", "to_be_neg", "pronouns"],
        "dialogues": ["meeting"],
        "goal": "Представляюсь, рассказываю о семье, спрашиваю имя и откуда человек",
    },
    {
        "n": 3,
        "title": "Вещи и еда",
        "focus": "a/an, множественное число, this/that; заказ еды в кафе",
        "topics": ["things", "food", "meal"],
        "grammar": ["articles_plural", "this_that"],
        "dialogues": ["cafe"],
        "goal": "Заказываю еду и напитки, называю предметы вокруг",
    },
    {
        "n": 4,
        "title": "Дом, природа, времена года",
        "focus": "there is/are, Present Simple; описание места, где живу",
        "topics": ["home", "nature", "seasons"],
        "grammar": ["there_is", "present_simple", "present_simple_q"],
        "dialogues": ["small_talk"],
        "goal": "Описываю квартиру и природу вокруг, говорю что где находится",
    },
    {
        "n": 5,
        "title": "Время и распорядок дня",
        "focus": "наречия частоты, предлоги времени, притяжательный 's",
        "topics": ["time", "days", "routine"],
        "grammar": ["adverbs_freq", "prepositions_time", "possessive"],
        "dialogues": ["my_day"],
        "goal": "Рассказываю о своём дне и времени, называю дни недели и месяцы",
    },
    {
        "n": 6,
        "title": "Город и транспорт",
        "focus": "предлоги места, some/any, much/many; как пройти и доехать",
        "topics": ["city", "transport", "directions"],
        "grammar": ["prepositions_place", "some_any", "much_many"],
        "dialogues": ["in_the_city"],
        "goal": "Спрашиваю и объясняю дорогу, пользуюсь транспортом",
    },
    {
        "n": 7,
        "title": "Магазин и вещи",
        "focus": "can, повелительное наклонение, вежливые просьбы, покупки",
        "topics": ["shopping", "clothes", "tech"],
        "grammar": ["can", "imperative", "polite_requests"],
        "dialogues": ["shopping"],
        "goal": "Покупаю вещи, спрашиваю цену и размер, вежливо прошу",
    },
    {
        "n": 8,
        "title": "Здоровье и погода",
        "focus": "Present Continuous, Present Simple vs Continuous",
        "topics": ["weather", "body", "feelings"],
        "grammar": ["present_continuous", "ps_vs_pc"],
        "dialogues": ["doctor", "weather_chat"],
        "goal": "Говорю о самочувствии и погоде, описываю что происходит сейчас",
    },
    {
        "n": 9,
        "title": "Работа, хобби, месяцы",
        "focus": "like + ing, сравнения, was/were",
        "topics": ["hobby", "work", "months"],
        "grammar": ["like_ing", "comparatives", "was_were"],
        "dialogues": ["work_meeting", "phone"],
        "goal": "Рассказываю о работе и увлечениях, звоню по телефону",
    },
    {
        "n": 10,
        "title": "Путешествия и учёба",
        "focus": "Past Simple: -ed, неправильные глаголы, did",
        "topics": ["travel", "school", "talk"],
        "grammar": ["past_regular", "past_irregular", "past_questions"],
        "dialogues": ["hotel"],
        "goal": "Рассказываю, что делал вчера и в отпуске, бронирую отель",
    },
    {
        "n": 11,
        "title": "Планы и будущее",
        "focus": "going to, will, WH-вопросы; главные глаголы, прилагательные, связки",
        "topics": ["verbs", "adjectives", "linkwords"],
        "grammar": ["going_to", "will", "wh_questions"],
        "dialogues": ["airport"],
        "goal": "Говорю о планах, задаю любые простые вопросы, прохожу регистрацию",
    },
    {
        "n": 12,
        "title": "Итог A1: повторение и экзамен",
        "focus": "must/should, карта времён, повторение всех 33 тем",
        "topics": [],
        "grammar": ["must_should", "course_map"],
        "dialogues": ["weekend_invite"],
        "goal": "Свободно держу простой разговор на бытовые темы - уровень A1",
    },
]

DAYS_IN_WEEK = 7
LESSON_DAYS_IN_WEEK = 6      # 7-й день - повторение и тест недели
TOTAL_WEEKS = len(WEEKS)
TOTAL_DAYS = DAYS_IN_WEEK * TOTAL_WEEKS        # 84 дня курса
COVER_WEEKS = 11             # недели 1-11 дают новые слова, 12-я - итоговая
