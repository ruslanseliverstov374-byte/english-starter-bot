# -*- coding: utf-8 -*-
"""Грамматические карточки курса: 1 карточка = 60-90 секунд чтения.

Формат:
    id      - короткий ключ
    week    - в какую неделю курса даётся
    title   - заголовок
    body    - объяснение по-русски (можно с переводами строк)
    examples- примеры (en, ru)
    tip     - короткая подсказка-запоминалка (может быть None)
    check   - мини-проверка: q, options, correct (может быть None)
"""

GRAMMAR = [
    {
        "id": "reading_basics",
        "week": 1,
        "title": "Как читать по-английски: 4 главных правила",
        "body": (
            "В английском пишется одно, а читается другое. Запомни базу:\n"
            "1) Ударение в слове чаще всего на первом слоге: TEA-cher.\n"
            "2) Буква e в конце слова обычно НЕ читается, но делает гласную длинной: name - [нэйм], like - [лайк].\n"
            "3) Двойные согласные читаются как одна: letter - [лЭтэ].\n"
            "4) Гласные в коротких закрытых слогах читаются коротко: cat - [кэт], dog - [дог], pen - [пен]."
        ),
        "examples": [
            ("name, like, home", "долгая гласная из-за конечной e"),
            ("cat, dog, pen", "короткая гласная в закрытом слоге"),
        ],
        "tip": "Правило немой e: «e на конце - гласная поёт».",
        "check": {
            "q": "Как читается слово home?",
            "options": ["[хомэ]", "[хоум]", "[хом]"],
            "correct": 1,
        },
    },
    {
        "id": "syllables",
        "week": 1,
        "title": "Открытый и закрытый слог",
        "body": (
            "Открытый слог (заканчивается на гласную) - гласная читается как в алфавите:\n"
            "a [эй], e [и:], i [ай], o [оу], u [ю:].\n"
            "Закрытый слог (после гласной согласная) - короткий звук:\n"
            "a [э], e [э], i [и], o [о], u [а].\n"
            "Сравни: hat [хэт] - hate [хэйт], not [нот] - note [ноут], bit [бит] - bite [байт]."
        ),
        "examples": [
            ("cap - cape", "кэп (кепка) - кэйп (плащ)"),
            ("kit - kite", "кит (набор) - кайт (воздушный змей)"),
        ],
        "tip": "Слог открыт - звук «поёт по алфавиту».",
        "check": {
            "q": "Как читается слово note?",
            "options": ["[нот]", "[ноут]", "[нотэ]"],
            "correct": 1,
        },
    },
    {
        "id": "digraphs",
        "week": 1,
        "title": "Буквосочетания: th, sh, ch, ph, ee, oo",
        "body": (
            "th - язык между зубами: think [синк], this [зис]\n"
            "sh - [ш]: she [ши:], shop [шоп]\n"
            "ch - [ч]: chair [чэа], cheese [чи:з]\n"
            "ph - [ф]: phone [фоун], photo [фоутоу]\n"
            "ee - [и:]: see [си:], green [гри:н]\n"
            "oo - [у:]: book [бук], food [фу:д]"
        ),
        "examples": [
            ("I think this shop is good.", "Я думаю, этот магазин хороший."),
            ("She has a phone and a photo.", "У неё есть телефон и фотография."),
        ],
        "tip": "th - не [з] и не [ф]: кончик языка между зубами.",
        "check": {
            "q": "Как читается ph в слове phone?",
            "options": ["[п]", "[ф]", "[пх]"],
            "correct": 1,
        },
    },
    {
        "id": "word_order",
        "week": 1,
        "title": "Порядок слов в предложении",
        "body": (
            "Английское предложение почти всегда строится так:\n"
            "КТО + ДЕЙСТВИЕ + ЧТО/КОГО + ГДЕ + КОГДА\n"
            "I  |  drink  |  coffee  |  at home  |  in the morning.\n"
            "В русском порядок свободный, в английском - нет: подлежащее всегда перед глаголом.\n"
            "Вопрос строится перестановкой: Do you drink coffee?"
        ),
        "examples": [
            ("I read books at home in the evening.", "Я читаю книги дома вечером."),
            ("She drinks tea in the morning.", "Она пьёт чай утром."),
        ],
        "tip": "Сначала «кто», потом «что делает». Всегда.",
        "check": {
            "q": "Какой порядок слов правильный?",
            "options": ["Coffee I drink.", "I drink coffee.", "Drink I coffee."],
            "correct": 1,
        },
    },
    {
        "id": "to_be",
        "week": 2,
        "title": "Глагол to be: am / is / are",
        "body": (
            "В английском нельзя сказать «Я студент» без глагола-связки. Нужен to be:\n"
            "I am - я есть\n"
            "he / she / it is - он / она / оно есть\n"
            "you / we / they are - ты, вы / мы / они есть\n"
            "Сокращения: I'm, he's, she's, it's, you're, we're, they're.\n"
            "По-русски «есть» мы не говорим, а по-английски - обязательно."
        ),
        "examples": [
            ("I am a student. / I'm a student.", "Я студент."),
            ("She is my sister.", "Она моя сестра."),
            ("We are from Russia.", "Мы из России."),
        ],
        "tip": "«Я - это я»: I всегда с am, а he/she/it - с is.",
        "check": {
            "q": "She ___ a doctor.",
            "options": ["am", "is", "are"],
            "correct": 1,
        },
    },
    {
        "id": "to_be_neg",
        "week": 2,
        "title": "to be: отрицание и вопрос",
        "body": (
            "Отрицание - просто добавь not после am/is/are:\n"
            "I am not (I'm not) tired. He is not (isn't) here. They are not (aren't) ready.\n"
            "Вопрос - поменяй местами подлежащее и глагол:\n"
            "Are you a student? Is she at home?\n"
            "Короткие ответы: Yes, I am. / No, I'm not. Yes, she is. / No, she isn't."
        ),
        "examples": [
            ("I'm not busy today.", "Я сегодня не занят."),
            ("Are you from Moscow?", "Вы из Москвы?"),
            ("Is he your brother?", "Он твой брат?"),
        ],
        "tip": "Вопрос = to be вперёд: Are you...? Is he...?",
        "check": {
            "q": "Как спросить «Ты устал?»",
            "options": ["You are tired?", "Are you tired?", "Do you tired?"],
            "correct": 1,
        },
    },
    {
        "id": "pronouns",
        "week": 2,
        "title": "Личные и притяжательные местоимения",
        "body": (
            "I - my (я - мой)\n"
            "you - your (ты - твой)\n"
            "he - his (он - его)\n"
            "she - her (она - её)\n"
            "it - its (оно - его)\n"
            "we - our (мы - наш)\n"
            "they - their (они - их)\n"
            "Первое слово отвечает на вопрос «кто?», второе - «чей?»."
        ),
        "examples": [
            ("This is my phone.", "Это мой телефон."),
            ("Her name is Anna.", "Её зовут Анна."),
            ("Their house is big.", "Их дом большой."),
        ],
        "tip": "her - и «её», и «ей». Контекст подскажет.",
        "check": {
            "q": "Это их машина. - This is ___ car.",
            "options": ["they", "their", "them"],
            "correct": 1,
        },
    },
    {
        "id": "articles_plural",
        "week": 3,
        "title": "Артикли a / an и множественное число",
        "body": (
            "a - перед согласным звуком: a book, a car.\n"
            "an - перед гласным звуком: an apple, an hour.\n"
            "Множественное число - добавь -s: book - books, car - cars.\n"
            "Если слово заканчивается на -s, -sh, -ch, -x - добавь -es: bus - buses, box - boxes.\n"
            "Некоторые слова меняются: man - men, woman - women, child - children."
        ),
        "examples": [
            ("I have a cat and two dogs.", "У меня есть кошка и две собаки."),
            ("She has three children.", "У неё трое детей."),
        ],
        "tip": "an - когда слово начинается с гласного ЗВУКА (an hour - [ауэ]).",
        "check": {
            "q": "Выбери правильный вариант:",
            "options": ["a apple", "an apple", "an apples"],
            "correct": 1,
        },
    },
    {
        "id": "this_that",
        "week": 3,
        "title": "this / that / these / those",
        "body": (
            "this - этот, это (рядом, один)\n"
            "these - эти (рядом, много)\n"
            "that - тот, то (далеко, один)\n"
            "those - те (далеко, много)\n"
            "Произнося «this», покажи рукой рядом; «that» - на расстояние."
        ),
        "examples": [
            ("This is my book.", "Это (рядом) моя книга."),
            ("These are my keys.", "Это (рядом) мои ключи."),
            ("That house is old.", "Тот дом старый."),
        ],
        "tip": "this/these - «тут», that/those - «там».",
        "check": {
            "q": "___ are my friends. (показываю на людей рядом)",
            "options": ["This", "These", "That"],
            "correct": 1,
        },
    },
    {
        "id": "there_is",
        "week": 4,
        "title": "there is / there are - «есть, находится»",
        "body": (
            "there is + один предмет: There is a shop near my house.\n"
            "there are + много: There are three shops in my street.\n"
            "Отрицание: There isn't a park here. There aren't any cafes.\n"
            "Вопрос: Is there a bank near here? Are there any shops?\n"
            "Это конструкция «где-то что-то есть», а не «у меня есть» (для этого - have)."
        ),
        "examples": [
            ("There is a park near my flat.", "Рядом с моей квартирой есть парк."),
            ("Are there any shops here?", "Здесь есть магазины?"),
        ],
        "tip": "there is = «где-то лежит один», there are = «их несколько».",
        "check": {
            "q": "___ two cats on the sofa.",
            "options": ["There is", "There are", "It is"],
            "correct": 1,
        },
    },
    {
        "id": "present_simple",
        "week": 4,
        "title": "Present Simple: простое настоящее",
        "body": (
            "Используем для привычек и фактов: I drink tea every morning.\n"
            "Форма глагола почти не меняется, НО с he / she / it добавляется -s:\n"
            "I work - he works; we live - she lives; you read - it reads.\n"
            "Если глагол на -s, -sh, -ch, -o - добавляем -es: go - goes, watch - watches.\n"
            "Если на согласную + y: study - studies."
        ),
        "examples": [
            ("I get up at seven.", "Я встаю в семь."),
            ("He works in a bank.", "Он работает в банке."),
            ("She studies English.", "Она учит английский."),
        ],
        "tip": "Он/она/оно - всегда с «s» на конце глагола.",
        "check": {
            "q": "She ___ in an office.",
            "options": ["work", "works", "working"],
            "correct": 1,
        },
    },
    {
        "id": "present_simple_q",
        "week": 4,
        "title": "Present Simple: вопрос и отрицание (do / does)",
        "body": (
            "Вопрос: Do + I/you/we/they + глагол? Does + he/she/it + глагол?\n"
            "Do you speak English? Does she like tea?\n"
            "ВАЖНО: с does окончание -s уходит к does, глагол остаётся чистым: Does he work? (не works)\n"
            "Отрицание: do not (don't) / does not (doesn't): I don't work on Sunday. He doesn't like coffee."
        ),
        "examples": [
            ("Do you live in Moscow?", "Ты живёшь в Москве?"),
            ("Does he speak Russian?", "Он говорит по-русски?"),
            ("I don't eat meat.", "Я не ем мясо."),
        ],
        "tip": "does уже забрал «s» себе - глагол без окончания.",
        "check": {
            "q": "Как правильно?",
            "options": ["Does he works here?", "Does he work here?", "Do he work here?"],
            "correct": 1,
        },
    },
    {
        "id": "adverbs_freq",
        "week": 5,
        "title": "Наречия частоты: always, usually, sometimes, never",
        "body": (
            "always - всегда (100%)\n"
            "usually - обычно\n"
            "often - часто\n"
            "sometimes - иногда\n"
            "rarely - редко\n"
            "never - никогда\n"
            "Место в предложении: ПЕРЕД смысловым глаголом, но ПОСЛЕ to be.\n"
            "I always drink coffee. She is never late."
        ),
        "examples": [
            ("I usually get up at seven.", "Я обычно встаю в семь."),
            ("He is always busy.", "Он всегда занят."),
            ("We never watch TV.", "Мы никогда не смотрим телевизор."),
        ],
        "tip": "never сам по себе отрицание - «not» не нужен.",
        "check": {
            "q": "Выбери правильный порядок:",
            "options": ["I drink always tea.", "I always drink tea.", "Always I drink tea."],
            "correct": 1,
        },
    },
    {
        "id": "prepositions_time",
        "week": 5,
        "title": "Предлоги времени: at, on, in",
        "body": (
            "at - точное время и ночь: at 7 o'clock, at noon, at night\n"
            "on - дни и даты: on Monday, on my birthday, on the 5th of May\n"
            "in - месяцы, времена года, годы, части дня: in May, in summer, in 2026, in the morning\n"
            "Исключение: at night, но in the morning / in the afternoon / in the evening."
        ),
        "examples": [
            ("The lesson starts at nine.", "Урок начинается в девять."),
            ("I work on Monday.", "Я работаю в понедельник."),
            ("We rest in August.", "Мы отдыхаем в августе."),
        ],
        "tip": "at - часы, on - дни, in - всё большое (месяц, год, сезон).",
        "check": {
            "q": "My birthday is ___ May.",
            "options": ["at", "on", "in"],
            "correct": 2,
        },
    },
    {
        "id": "possessive",
        "week": 5,
        "title": "Притяжательный падеж: 's и of",
        "body": (
            "Одушевлённые - добавляем 's: my brother's car (машина моего брата), Anna's phone.\n"
            "Если слово во множественном числе на -s, ставим только апостроф: my parents' house.\n"
            "Неодушевлённые - обычно через of: the name of the street, the door of the room.\n"
            "Сравни: Tom's book (книга Тома) - the end of the book (конец книги)."
        ),
        "examples": [
            ("This is my sister's room.", "Это комната моей сестры."),
            ("What is the name of this street?", "Как называется эта улица?"),
        ],
        "tip": "'s ставим людям и животным, of - вещам.",
        "check": {
            "q": "Машина моего друга:",
            "options": ["my friend's car", "my friends car", "the car of my friend"],
            "correct": 0,
        },
    },
    {
        "id": "prepositions_place",
        "week": 6,
        "title": "Предлоги места: in, on, at, under, next to",
        "body": (
            "in - внутри: in the room, in the bag\n"
            "on - на поверхности: on the table, on the wall\n"
            "under - под: under the bed\n"
            "next to / near - рядом: next to the bank\n"
            "between - между: between the shop and the bank\n"
            "behind - за: behind the house. in front of - перед."
        ),
        "examples": [
            ("The keys are on the table.", "Ключи на столе."),
            ("The cat is under the chair.", "Кошка под стулом."),
            ("The bank is next to the shop.", "Банк рядом с магазином."),
        ],
        "tip": "on - «касается сверху», in - «внутри».",
        "check": {
            "q": "The phone is ___ my bag.",
            "options": ["on", "in", "at"],
            "correct": 1,
        },
    },
    {
        "id": "some_any",
        "week": 6,
        "title": "some и any",
        "body": (
            "some - в утверждениях: I have some money. There are some apples.\n"
            "any - в вопросах и отрицаниях: Do you have any money? I don't have any money.\n"
            "Но в вежливой просьбе и предложении - тоже some: Would you like some tea?\n"
            "В разговорной речи в утверждении some часто просто опускают: I have money."
        ),
        "examples": [
            ("I need some bread.", "Мне нужно немного хлеба."),
            ("Do you have any questions?", "У вас есть вопросы?"),
        ],
        "tip": "some - «да», any - «нет?».",
        "check": {
            "q": "I don't have ___ time today.",
            "options": ["some", "any", "a"],
            "correct": 1,
        },
    },
    {
        "id": "much_many",
        "week": 6,
        "title": "much / many / a lot of",
        "body": (
            "many - с тем, что можно посчитать: many books, many people.\n"
            "much - с тем, что нельзя посчитать: much water, much time, much money.\n"
            "a lot of - универсально, подходит и там, и там: a lot of books, a lot of water.\n"
            "Вопросы: How many books? How much water?\n"
            "В утверждениях чаще говорят a lot of, а much/many - в вопросах и отрицаниях."
        ),
        "examples": [
            ("How many brothers do you have?", "Сколько у тебя братьев?"),
            ("How much does it cost?", "Сколько это стоит?"),
            ("I have a lot of work today.", "У меня сегодня много работы."),
        ],
        "tip": "many - «штуки», much - «субстанция».",
        "check": {
            "q": "How ___ money do you need?",
            "options": ["many", "much", "a lot"],
            "correct": 1,
        },
    },
    {
        "id": "can",
        "week": 7,
        "title": "can / can't - умею и можно",
        "body": (
            "can + глагол без to: I can swim. She can drive.\n"
            "Отрицание: cannot / can't: I can't come today.\n"
            "Вопрос: Can you help me?\n"
            "can не меняется по лицам: he can (не «cans»).\n"
            "Ещё can используют для просьбы: Can I take your pen? Can you repeat, please?"
        ),
        "examples": [
            ("I can speak a little English.", "Я немного говорю по-английски."),
            ("Can you help me, please?", "Вы можете мне помочь?"),
            ("I can't drive.", "Я не умею водить."),
        ],
        "tip": "после can - глагол без to и без -s.",
        "check": {
            "q": "She ___ swim very well.",
            "options": ["can", "cans", "can to"],
            "correct": 0,
        },
    },
    {
        "id": "imperative",
        "week": 7,
        "title": "Повелительное наклонение: делай / не делай",
        "body": (
            "Просьба и команда - просто глагол без подлежащего:\n"
            "Open the door. Come here. Please, sit down.\n"
            "Отрицание: Don't + глагол: Don't worry. Don't be late.\n"
            "Вежливость добавляет please в начало или конец.\n"
            "Let's + глагол = «давай»: Let's go! Let's have lunch."
        ),
        "examples": [
            ("Please, close the window.", "Пожалуйста, закройте окно."),
            ("Don't be afraid.", "Не бойся."),
            ("Let's go to the park.", "Давай пойдём в парк."),
        ],
        "tip": "Let's = let us - «давай(те)».",
        "check": {
            "q": "Как сказать «Не опаздывай»?",
            "options": ["Not late.", "Don't be late.", "No late."],
            "correct": 1,
        },
    },
    {
        "id": "polite_requests",
        "week": 7,
        "title": "Вежливые просьбы и покупки",
        "body": (
            "Can I have ... ? - Можно мне ... ?\n"
            "Could you ... , please? - Не могли бы вы ... ?\n"
            "I would like (I'd like) ... - Я хотел бы ... (самый вежливый вариант)\n"
            "How much is it? - Сколько это стоит?\n"
            "В магазине: I'm just looking. - Я просто смотрю. Do you have this in size 42? - У вас есть это 42-го размера?"
        ),
        "examples": [
            ("I'd like a cup of tea, please.", "Я хотел бы чашку чая, пожалуйста."),
            ("Could you help me, please?", "Не могли бы вы мне помочь?"),
            ("How much is this bag?", "Сколько стоит эта сумка?"),
        ],
        "tip": "I'd like звучит вежливее, чем I want.",
        "check": {
            "q": "Самый вежливый вариант в кафе:",
            "options": ["I want tea.", "I'd like tea, please.", "Give me tea."],
            "correct": 1,
        },
    },
    {
        "id": "present_continuous",
        "week": 8,
        "title": "Present Continuous: сейчас, в этот момент",
        "body": (
            "Формула: am / is / are + глагол-ing.\n"
            "I am reading. She is cooking. They are working.\n"
            "Отрицание: I am not reading. He isn't working.\n"
            "Вопрос: Are you listening? What is she doing?\n"
            "Маркеры: now, at the moment, Look!, Listen!"
        ),
        "examples": [
            ("I am learning English now.", "Я сейчас учу английский."),
            ("What are you doing?", "Что ты делаешь?"),
            ("It is raining.", "Идёт дождь."),
        ],
        "tip": "есть -ing - значит «прямо сейчас».",
        "check": {
            "q": "Listen! She ___ a song.",
            "options": ["sings", "is singing", "sing"],
            "correct": 1,
        },
    },
    {
        "id": "ps_vs_pc",
        "week": 8,
        "title": "Present Simple или Continuous?",
        "body": (
            "Present Simple - всегда, обычно, каждый день:\n"
            "I drink coffee every morning.\n"
            "Present Continuous - прямо сейчас, временно:\n"
            "I am drinking coffee now (в руке чашка).\n"
            "Сравни: She works in a bank (вообще). She is working at home today (сегодня, временно).\n"
            "Глаголы чувств (like, love, want, know, understand) в Continuous не ставят: I want, не I am wanting."
        ),
        "examples": [
            ("I usually get up at seven.", "Я обычно встаю в семь."),
            ("I am getting up now.", "Я сейчас встаю."),
            ("He likes tea.", "Он любит чай."),
        ],
        "tip": "usually/every day → Simple, now/at the moment → Continuous.",
        "check": {
            "q": "I ___ TV every evening.",
            "options": ["watch", "am watching", "watches"],
            "correct": 0,
        },
    },
    {
        "id": "like_ing",
        "week": 9,
        "title": "like + ing: о вкусах и хобби",
        "body": (
            "После like, love, hate, enjoy глагол идёт с -ing:\n"
            "I like reading. She loves swimming. He hates cooking.\n"
            "Степени: I like it. I really like it. I love it. I don't like it at all.\n"
            "Спросить: Do you like ...? What do you like doing?\n"
            "Разница: I like reading (нравится процесс) - I'd like to read (хочу сейчас)."
        ),
        "examples": [
            ("I like playing football.", "Мне нравится играть в футбол."),
            ("Do you like cooking?", "Тебе нравится готовить?"),
            ("I love listening to music.", "Я обожаю слушать музыку."),
        ],
        "tip": "like/hate/love + ...ing.",
        "check": {
            "q": "I like ___ films in the evening.",
            "options": ["watch", "watching", "to watching"],
            "correct": 1,
        },
    },
    {
        "id": "comparatives",
        "week": 9,
        "title": "Сравнение: big - bigger - the biggest",
        "body": (
            "Короткие слова: +er / +est: small - smaller - the smallest; big - bigger - the biggest.\n"
            "Длинные слова: more / the most: expensive - more expensive - the most expensive.\n"
            "Исключения: good - better - the best; bad - worse - the worst.\n"
            "Сравнение: ... than: Moscow is bigger than Tula. / not as ... as: He is not as tall as his brother."
        ),
        "examples": [
            ("This book is cheaper than that one.", "Эта книга дешевле той."),
            ("English is easier than Chinese.", "Английский легче китайского."),
            ("It is the best film of the year.", "Это лучший фильм года."),
        ],
        "tip": "er/est - для коротких, more/most - для длинных.",
        "check": {
            "q": "This car is ___ than my car.",
            "options": ["expensive", "more expensive", "most expensive"],
            "correct": 1,
        },
    },
    {
        "id": "was_were",
        "week": 9,
        "title": "was / were - «был, было»",
        "body": (
            "Прошлое глагола to be:\n"
            "I / he / she / it was - был, была, было\n"
            "you / we / they were - были\n"
            "Отрицание: wasn't, weren't. Вопрос: Was he at work? Were you at home?\n"
            "Погода и состояние: It was cold yesterday. I was tired."
        ),
        "examples": [
            ("I was at work yesterday.", "Вчера я был на работе."),
            ("They were at home in the evening.", "Вечером они были дома."),
            ("It was a good day.", "Это был хороший день."),
        ],
        "tip": "you всегда were, даже когда «ты» один.",
        "check": {
            "q": "We ___ at the cinema on Sunday.",
            "options": ["was", "were", "are"],
            "correct": 1,
        },
    },
    {
        "id": "past_regular",
        "week": 10,
        "title": "Past Simple: правильные глаголы (-ed)",
        "body": (
            "Простое прошедшее: к глаголу добавляем -ed.\n"
            "work - worked, live - lived, play - played, start - started.\n"
            "Форма одна для всех лиц: I worked, she worked, they worked.\n"
            "Отрицание и вопрос - через did (тогда -ed исчезает):\n"
            "I didn't work. Did you work?\n"
            "Маркеры: yesterday, last week, two days ago, in 2020."
        ),
        "examples": [
            ("I worked at home yesterday.", "Вчера я работал дома."),
            ("She watched a film last night.", "Вчера вечером она смотрела фильм."),
        ],
        "tip": "did уже показывает прошлое - глагол без -ed.",
        "check": {
            "q": "We ___ TV yesterday evening.",
            "options": ["watch", "watched", "watching"],
            "correct": 1,
        },
    },
    {
        "id": "past_irregular",
        "week": 10,
        "title": "Past Simple: 12 главных неправильных глаголов",
        "body": (
            "Их не объяснить - только запомнить (форма для всех лиц одна):\n"
            "be - was/were | have - had | do - did | go - went | come - came | get - got\n"
            "make - made | take - took | give - gave | see - saw | eat - ate | say - said\n"
            "Часто используем с yesterday: I went to the shop. She had a meeting."
        ),
        "examples": [
            ("I went to the shop yesterday.", "Вчера я ходил в магазин."),
            ("We had lunch at two.", "Мы обедали в два."),
            ("He came home late.", "Он пришёл домой поздно."),
        ],
        "tip": "Учи неправильные глаголы по 3-4 в день вместе со словами урока.",
        "check": {
            "q": "I ___ to the park yesterday.",
            "options": ["goed", "went", "gone"],
            "correct": 1,
        },
    },
    {
        "id": "past_questions",
        "week": 10,
        "title": "Past Simple: вопрос и отрицание (did)",
        "body": (
            "Вопрос: Did + подлежащее + глагол? Did you go to work yesterday?\n"
            "Отрицание: didn't + глагол. I didn't see him.\n"
            "После did/didn't глагол всегда в начальной форме: Did you go? (не went)\n"
            "Специальные вопросы: Where did you go? What did she say? Why did he come?"
        ),
        "examples": [
            ("Did you like the film?", "Тебе понравился фильм?"),
            ("I didn't have time yesterday.", "Вчера у меня не было времени."),
            ("Where did you work before?", "Где вы работали раньше?"),
        ],
        "tip": "did + базовый глагол: did you go, did you see.",
        "check": {
            "q": "Как правильно?",
            "options": ["Did you went there?", "Did you go there?", "Do you went there?"],
            "correct": 1,
        },
    },
    {
        "id": "going_to",
        "week": 11,
        "title": "Планы: going to",
        "body": (
            "Формула: am / is / are + going to + глагол.\n"
            "I am going to study English. We are going to travel in July.\n"
            "Это про уже принятое решение или видимый признак:\n"
            "Look at the sky - it is going to rain.\n"
            "Отрицание: I'm not going to work tomorrow."
        ),
        "examples": [
            ("I am going to buy a new phone.", "Я собираюсь купить новый телефон."),
            ("What are you going to do tomorrow?", "Что ты собираешься делать завтра?"),
        ],
        "tip": "going to - «уже решил и планирую».",
        "check": {
            "q": "She ___ to visit her parents on Sunday.",
            "options": ["is going", "goes to", "going"],
            "correct": 0,
        },
    },
    {
        "id": "will",
        "week": 11,
        "title": "Будущее: will",
        "body": (
            "will + глагол, одинаково для всех лиц: I will call you. She will come.\n"
            "Сокращение: I'll, you'll, he'll; отрицание won't.\n"
            "Когда используем will: обещания, решения «на ходу», прогнозы:\n"
            "I will help you. OK, I will take a taxi. It will be cold tomorrow.\n"
            "will и going to взаимозаменяемы в быту, но going to - про план, will - про решение и прогноз."
        ),
        "examples": [
            ("I will call you in the evening.", "Я позвоню тебе вечером."),
            ("It will rain tomorrow.", "Завтра будет дождь."),
            ("I won't be late.", "Я не опоздаю."),
        ],
        "tip": "will не меняется: he will, she will, they will.",
        "check": {
            "q": "I think it ___ be cold tomorrow.",
            "options": ["will", "am", "going"],
            "correct": 0,
        },
    },
    {
        "id": "wh_questions",
        "week": 11,
        "title": "Вопросы: what, where, when, why, how, who",
        "body": (
            "Схема: вопросительное слово + вспомогательный глагол + подлежащее + глагол.\n"
            "What do you do? Where do you live? When did you come? Why are you tired? How much is it?\n"
            "who часто без вспомогательного: Who is it? Who works here?\n"
            "Полезные связки: How old are you? How long? How often? What time?"
        ),
        "examples": [
            ("Where do you work?", "Где вы работаете?"),
            ("What time is it?", "Который час?"),
            ("How often do you study English?", "Как часто вы учите английский?"),
        ],
        "tip": "Порядок: вопрос-слово → помощник → кто → что делает.",
        "check": {
            "q": "___ do you live?",
            "options": ["What", "Where", "Who"],
            "correct": 1,
        },
    },
    {
        "id": "must_should",
        "week": 12,
        "title": "must / should / have to - должен и стоит",
        "body": (
            "must - строго должен (правило, сам решил): You must stop here.\n"
            "have to - приходится (внешние обстоятельства): I have to work on Saturday.\n"
            "should - совет: You should rest. You shouldn't eat so much sugar.\n"
            "mustn't - нельзя; don't have to - не обязан (не то же самое!).\n"
            "Вопрос-совет: Should I call the doctor?"
        ),
        "examples": [
            ("You must see this film!", "Ты обязательно должен посмотреть этот фильм!"),
            ("I have to get up early.", "Мне приходится вставать рано."),
            ("You should drink more water.", "Тебе стоит пить больше воды."),
        ],
        "tip": "should - «стоит», must - «обязан», have to - «приходится».",
        "check": {
            "q": "Тебе стоит отдохнуть. - You ___ rest.",
            "options": ["should", "must", "have to"],
            "correct": 0,
        },
    },
    {
        "id": "course_map",
        "week": 12,
        "title": "Карта времён: что вы уже знаете",
        "body": (
            "Настоящее: I work (Present Simple) / I am working (Continuous)\n"
            "Прошлое: I worked / I went (Past Simple); I was (to be)\n"
            "Будущее: I am going to work / I will work\n"
            "Модальные: can, must, should + глагол без to\n"
            "Каркас английского предложения: КТО + ГЛАГОЛ + остальное + время/место.\n"
            "Этого достаточно для уровня A1: знакомство, магазин, кафе, дорога, работа, рассказ о себе и о прошлом."
        ),
        "examples": [
            ("Yesterday I worked, today I am resting, tomorrow I will study.", "Вчера я работал, сегодня отдыхаю, завтра буду учиться."),
        ],
        "tip": "Дальше по курсу A2: Present Perfect, условия, фразовые глаголы.",
        "check": {
            "q": "Какая фраза про будущее?",
            "options": ["I worked yesterday.", "I will call you.", "I am working now."],
            "correct": 1,
        },
    },
]
