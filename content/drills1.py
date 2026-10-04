# -*- coding: utf-8 -*-
"""Тренажёр конструкций, часть 1 (недели 1-6).

Формат: DRILLS[card_id]["items"] - список заданий.
  {"q": "...", "options": [...], "correct": N}      - выбрать вариант
  {"q": "...", "answer": "...", "accept": [...]}    - написать ответ текстом
card_id совпадает с id грамматической карточки из grammar.py.
"""

DRILLS = {
    "reading_basics": {
        "items": [
            {"q": "Как читается слово name?", "options": ["[нэйм]", "[намэ]", "[нэм]"], "correct": 0},
            {"q": "Как читается слово cat?", "options": ["[кэйт]", "[кэт]", "[сат]"], "correct": 1},
            {"q": "Какая буква НЕ читается в слове like?", "options": ["l", "i", "e"], "correct": 2},
            {"q": "Где ударение в слове teacher?", "options": ["TEA-cher", "tea-CHER"], "correct": 0},
            {"q": "Как читается двойная согласная в слове letter?", "options": ["как одна [т]", "как две [тт]"], "correct": 0},
            {"q": "Как читается слово home?", "options": ["[хоум]", "[хом]", "[хомэ]"], "correct": 0},
        ],
    },
    "syllables": {
        "items": [
            {"q": "Чем отличается hat от hate?", "options": ["hate - долгий [эй]", "hat - долгий [эй]", "разницы нет"], "correct": 0},
            {"q": "Как читается note?", "options": ["[ноут]", "[нот]", "[нотэ]"], "correct": 0},
            {"q": "Как читается kit?", "options": ["[кайт]", "[кит]", "[китэ]"], "correct": 1},
            {"q": "В слове bite гласная i читается как...", "options": ["[ай] - открытый слог", "[и] - закрытый слог"], "correct": 0},
            {"q": "В слове not гласная o читается как...", "options": ["[оу]", "[о] - закрытый слог"], "correct": 1},
        ],
    },
    "digraphs": {
        "items": [
            {"q": "ph в слове phone читается как...", "options": ["[ф]", "[п]", "[пх]"], "correct": 0},
            {"q": "th в слове think читается как...", "options": ["[с] (язык между зубами)", "[т]", "[ф]"], "correct": 0},
            {"q": "sh в слове shop читается как...", "options": ["[ш]", "[с]", "[ч]"], "correct": 0},
            {"q": "ch в слове chair читается как...", "options": ["[ч]", "[к]", "[ш]"], "correct": 0},
            {"q": "ee в слове green читается как...", "options": ["[и:] - долгий", "[э]", "[эй]"], "correct": 0},
            {"q": "oo в слове book читается как...", "options": ["[у] - короткий", "[оу]", "[ю:]"], "correct": 0},
        ],
    },
    "word_order": {
        "items": [
            {"q": "Выбери правильный порядок слов:",
             "options": ["I drink coffee in the morning.", "Coffee I drink in the morning.", "Drink I coffee in the morning."], "correct": 0},
            {"q": "Выбери правильный порядок слов:",
             "options": ["She works in a bank.", "In a bank she works.", "Works she in a bank."], "correct": 0},
            {"q": "Где стоит подлежащее в английском предложении?",
             "options": ["перед глаголом", "после глагола", "где угодно"], "correct": 0},
            {"q": "«Я читаю книги дома» -",
             "options": ["I read books at home.", "I books read at home.", "Read I books at home."], "correct": 0},
        ],
    },
    "to_be": {
        "items": [
            {"q": "I ___ a student.", "options": ["am", "is", "are"], "correct": 0},
            {"q": "She ___ my sister.", "options": ["am", "is", "are"], "correct": 1},
            {"q": "They ___ from London.", "options": ["am", "is", "are"], "correct": 2},
            {"q": "It ___ cold today.", "options": ["am", "is", "are"], "correct": 1},
            {"q": "We ___ at home now.", "options": ["am", "is", "are"], "correct": 2},
            {"q": "Напишите по-английски: «Я устал»", "answer": "I am tired", "accept": ["I'm tired"]},
        ],
    },
    "to_be_neg": {
        "items": [
            {"q": "I ___ busy today. (отрицание)", "options": ["am not", "is not", "are not"], "correct": 0},
            {"q": "He ___ at work. (отрицание)", "options": ["am not", "isn't", "aren't"], "correct": 1},
            {"q": "Как спросить «Ты устал?»", "options": ["Are you tired?", "You are tired?", "Do you tired?"], "correct": 0},
            {"q": "Короткий ответ на «Is she a doctor?» (да)",
             "options": ["Yes, she is.", "Yes, she does.", "Yes, she are."], "correct": 0},
            {"q": "___ they from Russia?", "options": ["Is", "Are", "Am"], "correct": 1},
            {"q": "Напишите по-английски: «Это не мой телефон»", "answer": "It is not my phone",
             "accept": ["It isn't my phone", "It's not my phone"]},
        ],
    },
    "pronouns": {
        "items": [
            {"q": "Это мой телефон. - This is ___ phone.", "options": ["I", "my", "me"], "correct": 1},
            {"q": "Её зовут Анна. - ___ name is Anna.", "options": ["Her", "She", "His"], "correct": 0},
            {"q": "Их дом большой. - ___ house is big.", "options": ["They", "Their", "Them"], "correct": 1},
            {"q": "Мы семья. - ___ are a family.", "options": ["We", "Our", "Us"], "correct": 0},
            {"q": "Он врач. - ___ is a doctor.", "options": ["He", "His", "Him"], "correct": 0},
            {"q": "Напишите по-английски: «Наш учитель говорит по-английски»",
             "answer": "Our teacher speaks English", "accept": ["Our teacher speaks English."]},
        ],
    },
    "articles_plural": {
        "items": [
            {"q": "Выбери правильный вариант:", "options": ["a apple", "an apple", "an apples"], "correct": 1},
            {"q": "Выбери правильный вариант:", "options": ["a hour", "an hour", "an hours"], "correct": 1},
            {"q": "Множественное число слова bus:", "options": ["buss", "buses", "busies"], "correct": 1},
            {"q": "Множественное число слова box:", "options": ["boxs", "boxes", "box"], "correct": 1},
            {"q": "Множественное число слова child:", "options": ["childs", "children", "childes"], "correct": 1},
            {"q": "Множественное число слова man:", "options": ["mans", "men", "mens"], "correct": 1},
        ],
    },
    "this_that": {
        "items": [
            {"q": "___ is my book. (книга рядом)", "options": ["This", "These", "Those"], "correct": 0},
            {"q": "___ are my keys. (ключи рядом)", "options": ["This", "These", "That"], "correct": 1},
            {"q": "___ house is old. (дом далеко)", "options": ["This", "That", "These"], "correct": 1},
            {"q": "___ people are my friends. (люди далеко)", "options": ["That", "This", "Those"], "correct": 2},
            {"q": "Как сказать «Это мои друзья» (рядом)?",
             "options": ["These are my friends.", "This is my friends.", "Those are my friends."], "correct": 0},
        ],
    },
    "there_is": {
        "items": [
            {"q": "___ a park near my house.", "options": ["There is", "There are", "It is"], "correct": 0},
            {"q": "___ two cats on the sofa.", "options": ["There is", "There are", "It is"], "correct": 1},
            {"q": "Отрицание: ___ a shop in my street.", "options": ["There isn't", "There aren't", "There not is"], "correct": 0},
            {"q": "Вопрос: ___ a bank near here?", "options": ["Is there", "Are there", "There is"], "correct": 0},
            {"q": "«У меня есть машина» -",
             "options": ["I have a car.", "There is a car at me.", "I am a car."], "correct": 0},
        ],
    },
    "present_simple": {
        "items": [
            {"q": "She ___ in an office.", "options": ["work", "works", "working"], "correct": 1},
            {"q": "I ___ up at seven.", "options": ["get", "gets", "getting"], "correct": 0},
            {"q": "He ___ English every day.", "options": ["study", "studies", "studys"], "correct": 1},
            {"q": "We ___ TV in the evening.", "options": ["watch", "watches", "watching"], "correct": 0},
            {"q": "My brother ___ to school.", "options": ["go", "goes", "going"], "correct": 1},
            {"q": "Напишите по-английски: «Она работает в банке»",
             "answer": "She works in a bank", "accept": ["She works at a bank"]},
        ],
    },
    "present_simple_q": {
        "items": [
            {"q": "Как правильно?", "options": ["Does he works here?", "Does he work here?", "Do he work here?"], "correct": 1},
            {"q": "___ you speak English?", "options": ["Do", "Does", "Are"], "correct": 0},
            {"q": "She ___ like coffee.", "options": ["don't", "doesn't", "isn't"], "correct": 1},
            {"q": "Вопрос к «He lives in Moscow»:",
             "options": ["Does he live in Moscow?", "Does he lives in Moscow?", "Do he live in Moscow?"], "correct": 0},
            {"q": "Отрицание: I ___ eat meat.", "options": ["doesn't", "don't", "am not"], "correct": 1},
            {"q": "Напишите по-английски: «Ты работаешь в офисе?»",
             "answer": "Do you work in an office", "accept": ["Do you work in an office?", "Do you work in the office?"]},
        ],
    },
    "adverbs_freq": {
        "items": [
            {"q": "Выбери правильный порядок:", "options": ["I always drink tea.", "I drink always tea.", "Always I drink tea."], "correct": 0},
            {"q": "He ___ late. (никогда)", "options": ["is never", "never is", "isn't never"], "correct": 0},
            {"q": "«Иногда» по-английски:", "options": ["sometimes", "usually", "always"], "correct": 0},
            {"q": "«Редко» по-английски:", "options": ["rarely", "always", "often"], "correct": 0},
            {"q": "We ___ watch TV. (никогда - правильная форма)",
             "options": ["never", "don't never", "not never"], "correct": 0},
        ],
    },
    "prepositions_time": {
        "items": [
            {"q": "The lesson starts ___ nine.", "options": ["at", "on", "in"], "correct": 0},
            {"q": "My birthday is ___ May.", "options": ["at", "on", "in"], "correct": 2},
            {"q": "I work ___ Monday.", "options": ["at", "on", "in"], "correct": 1},
            {"q": "We rest ___ summer.", "options": ["at", "on", "in"], "correct": 2},
            {"q": "I read ___ the evening.", "options": ["at", "on", "in"], "correct": 2},
            {"q": "It is dark ___ night.", "options": ["at", "on", "in"], "correct": 0},
        ],
    },
    "possessive": {
        "items": [
            {"q": "Машина моего брата:", "options": ["my brother's car", "my brothers car", "the car of my brother"], "correct": 0},
            {"q": "Комната моей сестры:", "options": ["my sister's room", "my sisters room", "room my sister"], "correct": 0},
            {"q": "Как сказать «Как называется эта улица?»",
             "options": ["What is the name of this street?", "What is this street's name?", "How name this street?"], "correct": 0},
            {"q": "Дом моих родителей:", "options": ["my parents' house", "my parents's house", "my parent's houses"], "correct": 0},
            {"q": "Телефон Анны:", "options": ["Anna's phone", "Phone Anna", "Annas' phone"], "correct": 0},
        ],
    },
    "prepositions_place": {
        "items": [
            {"q": "The phone is ___ my bag.", "options": ["on", "in", "at"], "correct": 1},
            {"q": "The keys are ___ the table.", "options": ["in", "on", "under"], "correct": 1},
            {"q": "The cat is ___ the chair. (под стулом)", "options": ["on", "under", "in"], "correct": 1},
            {"q": "The bank is ___ to the shop.", "options": ["next", "near", "between"], "correct": 0},
            {"q": "The cafe is ___ the bank and the shop.", "options": ["between", "under", "on"], "correct": 0},
            {"q": "«за домом»:", "options": ["behind the house", "under the house", "on the house"], "correct": 0},
        ],
    },
    "some_any": {
        "items": [
            {"q": "I need ___ bread.", "options": ["some", "any", "a"], "correct": 0},
            {"q": "Do you have ___ questions?", "options": ["some", "any", "much"], "correct": 1},
            {"q": "I don't have ___ money.", "options": ["some", "any", "a"], "correct": 1},
            {"q": "Вежливое предложение: Would you like ___ tea?",
             "options": ["some", "any", "many"], "correct": 0},
            {"q": "There aren't ___ shops here.", "options": ["some", "any", "a"], "correct": 1},
        ],
    },
    "much_many": {
        "items": [
            {"q": "How ___ money do you need?", "options": ["many", "much", "a lot"], "correct": 1},
            {"q": "How ___ brothers do you have?", "options": ["many", "much", "a lot"], "correct": 0},
            {"q": "I have ___ of work today.", "options": ["many", "much", "a lot"], "correct": 2},
            {"q": "How ___ does it cost?", "options": ["many", "much", "a lot"], "correct": 1},
            {"q": "___ people speak English.", "options": ["Much", "Many", "A lot"], "correct": 1},
        ],
    },
}
