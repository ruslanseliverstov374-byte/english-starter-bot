# -*- coding: utf-8 -*-
"""Тренажёр конструкций, часть 2 (недели 7-12). Формат см. drills1.py."""

DRILLS = {
    "can": {
        "items": [
            {"q": "She ___ swim very well.", "options": ["can", "cans", "can to"], "correct": 0},
            {"q": "I ___ come today. (не могу)", "options": ["can't", "don't can", "not can"], "correct": 0},
            {"q": "___ you help me, please?", "options": ["Can", "Do can", "Are"], "correct": 0},
            {"q": "Как попросить ручку?", "options": ["Can I take your pen?", "I can take your pen?", "Can I to take your pen?"], "correct": 0},
            {"q": "После can глагол идёт...", "options": ["без to и без -s", "с to", "с -ing"], "correct": 0},
            {"q": "Напишите по-английски: «Я немного говорю по-английски»",
             "answer": "I can speak a little English", "accept": ["I can speak a little English."]},
        ],
    },
    "imperative": {
        "items": [
            {"q": "Как сказать «Закройте окно, пожалуйста»?",
             "options": ["Close the window, please.", "You close the window.", "Closing the window."], "correct": 0},
            {"q": "Как сказать «Не опаздывай»?", "options": ["Don't be late.", "Not late.", "No late."], "correct": 0},
            {"q": "«Давай пойдём в парк» -",
             "options": ["Let's go to the park.", "Let's to go to the park.", "We go to the park, let."], "correct": 0},
            {"q": "«Не волнуйся» -", "options": ["Don't worry.", "Not worry.", "No worry."], "correct": 0},
            {"q": "Вежливое слово в просьбе:", "options": ["please", "thank you", "sorry"], "correct": 0},
        ],
    },
    "polite_requests": {
        "items": [
            {"q": "Самый вежливый заказ в кафе:",
             "options": ["I'd like a cup of tea, please.", "I want tea.", "Give me tea."], "correct": 0},
            {"q": "«Сколько это стоит?» -", "options": ["How much is it?", "How many is it?", "What cost it?"], "correct": 0},
            {"q": "«Не могли бы вы помочь?» -",
             "options": ["Could you help me, please?", "Can you helping me?", "You could help me?"], "correct": 0},
            {"q": "«У вас есть это 42-го размера?» -",
             "options": ["Do you have this in size 42?", "Do you have this size 42?", "You have size 42 this?"], "correct": 0},
            {"q": "Если вы просто смотрите в магазине:",
             "options": ["I'm just looking.", "I look only.", "Just looking I'm."], "correct": 0},
        ],
    },
    "present_continuous": {
        "items": [
            {"q": "Listen! She ___ a song.", "options": ["sings", "is singing", "sing"], "correct": 1},
            {"q": "I ___ English now.", "options": ["learn", "am learning", "learns"], "correct": 1},
            {"q": "What ___ you doing?", "options": ["is", "are", "do"], "correct": 1},
            {"q": "It ___ raining.", "options": ["is", "are", "does"], "correct": 0},
            {"q": "They ___ working at the moment.", "options": ["is", "are", "am"], "correct": 1},
            {"q": "Формула Present Continuous:",
             "options": ["am/is/are + глагол-ing", "do/does + глагол", "глагол + -ed"], "correct": 0},
        ],
    },
    "ps_vs_pc": {
        "items": [
            {"q": "I ___ TV every evening.", "options": ["watch", "am watching", "watches"], "correct": 0},
            {"q": "I ___ TV now.", "options": ["watch", "am watching", "watches"], "correct": 1},
            {"q": "She usually ___ at seven. (встаёт)", "options": ["gets up", "is getting up", "get up"], "correct": 0},
            {"q": "«Он любит чай» -", "options": ["He likes tea.", "He is liking tea.", "He like tea."], "correct": 0},
            {"q": "Какой маркер у Present Continuous?", "options": ["now", "every day", "usually"], "correct": 0},
            {"q": "Какой маркер у Present Simple?", "options": ["every day", "at the moment", "now"], "correct": 0},
        ],
    },
    "like_ing": {
        "items": [
            {"q": "I like ___ films in the evening.", "options": ["watch", "watching", "to watching"], "correct": 1},
            {"q": "She loves ___ .", "options": ["swim", "swimming", "to swimming"], "correct": 1},
            {"q": "He ___ cooking. (не любит)", "options": ["doesn't like", "don't like", "isn't like"], "correct": 0},
            {"q": "«Тебе нравится готовить?» -", "options": ["Do you like cooking?", "Do you like cook?", "Are you like cooking?"], "correct": 0},
            {"q": "После like/love/hate глагол идёт...", "options": ["с -ing", "без изменений", "с -ed"], "correct": 0},
        ],
    },
    "comparatives": {
        "items": [
            {"q": "This car is ___ than my car.", "options": ["expensive", "more expensive", "most expensive"], "correct": 1},
            {"q": "Сравнительная степень от big:", "options": ["bigger", "more big", "biggest"], "correct": 0},
            {"q": "Превосходная степень от good:", "options": ["better", "the best", "goodest"], "correct": 1},
            {"q": "Moscow is ___ than Tula.", "options": ["bigger", "more big", "the biggest"], "correct": 0},
            {"q": "Сравнительная степень от bad:", "options": ["worse", "badder", "more bad"], "correct": 0},
            {"q": "Напишите по-английски: «Английский легче китайского»",
             "answer": "English is easier than Chinese", "accept": ["English is easier than Chinese."]},
        ],
    },
    "was_were": {
        "items": [
            {"q": "I ___ at work yesterday.", "options": ["was", "were", "am"], "correct": 0},
            {"q": "They ___ at home in the evening.", "options": ["was", "were", "are"], "correct": 1},
            {"q": "We ___ at the cinema on Sunday.", "options": ["was", "were", "is"], "correct": 1},
            {"q": "She ___ tired yesterday.", "options": ["was", "were", "is"], "correct": 0},
            {"q": "It ___ cold last week.", "options": ["was", "were", "be"], "correct": 0},
            {"q": "Отрицание: He ___ at school yesterday.", "options": ["wasn't", "weren't", "didn't be"], "correct": 0},
        ],
    },
    "past_regular": {
        "items": [
            {"q": "We ___ TV yesterday evening.", "options": ["watch", "watched", "watching"], "correct": 1},
            {"q": "I ___ at home yesterday. (работал)", "options": ["worked", "work", "working"], "correct": 0},
            {"q": "She ___ a film last night. (смотрела)", "options": ["watched", "watchs", "watching"], "correct": 0},
            {"q": "Отрицание: I ___ work yesterday.", "options": ["didn't", "don't", "wasn't"], "correct": 0},
            {"q": "Маркер Past Simple:", "options": ["yesterday", "now", "every day"], "correct": 0},
            {"q": "Напишите по-английски: «Вчера я работал дома»",
             "answer": "Yesterday I worked at home", "accept": ["I worked at home yesterday"]},
        ],
    },
    "past_irregular": {
        "items": [
            {"q": "I ___ to the park yesterday.", "options": ["goed", "went", "gone"], "correct": 1},
            {"q": "We ___ lunch at two. (had)", "options": ["haved", "had", "have"], "correct": 1},
            {"q": "She ___ a good film. (saw)", "options": ["saw", "seed", "seen"], "correct": 0},
            {"q": "He ___ home late. (came)", "options": ["came", "comed", "come"], "correct": 0},
            {"q": "I ___ a new phone. (got)", "options": ["got", "getted", "get"], "correct": 0},
            {"q": "Прошедшая форма от take:", "options": ["took", "taked", "taken"], "correct": 0},
        ],
    },
    "past_questions": {
        "items": [
            {"q": "Как правильно?", "options": ["Did you went there?", "Did you go there?", "Do you went there?"], "correct": 1},
            {"q": "Отрицание: I ___ see him.", "options": ["didn't", "don't", "wasn't"], "correct": 0},
            {"q": "Where ___ you work before?", "options": ["did", "do", "was"], "correct": 0},
            {"q": "Did you like the film? - Yes, I ___.", "options": ["did", "do", "liked"], "correct": 0},
            {"q": "После did глагол идёт...", "options": ["в начальной форме", "в прошедшей форме", "с -ing"], "correct": 0},
        ],
    },
    "going_to": {
        "items": [
            {"q": "She ___ to visit her parents on Sunday.", "options": ["is going", "goes to", "going"], "correct": 0},
            {"q": "I ___ buy a new phone.", "options": ["am going to", "going to", "go to"], "correct": 0},
            {"q": "Look at the sky! It ___ rain.", "options": ["is going to", "goes to", "will to"], "correct": 0},
            {"q": "Отрицание: I ___ work tomorrow.", "options": ["am not going to", "not going to", "don't going to"], "correct": 0},
            {"q": "Как спросить о планах?", "options": ["What are you going to do?", "What you going to do?", "What do you going to do?"], "correct": 0},
        ],
    },
    "will": {
        "items": [
            {"q": "I think it ___ be cold tomorrow.", "options": ["will", "am", "going"], "correct": 0},
            {"q": "I ___ call you in the evening. (обещание)", "options": ["will", "am", "do"], "correct": 0},
            {"q": "Сокращение will not:", "options": ["won't", "willn't", "don't will"], "correct": 0},
            {"q": "She ___ come tomorrow.", "options": ["will", "wills", "is will"], "correct": 0},
            {"q": "will меняется по лицам?", "options": ["нет, форма одна", "да, he wills", "только в вопросах"], "correct": 0},
        ],
    },
    "wh_questions": {
        "items": [
            {"q": "___ do you live?", "options": ["What", "Where", "Who"], "correct": 1},
            {"q": "___ do you work? (где)", "options": ["Where", "When", "Why"], "correct": 0},
            {"q": "___ time is it?", "options": ["What", "How", "Which"], "correct": 0},
            {"q": "___ old are you?", "options": ["How", "What", "Who"], "correct": 0},
            {"q": "___ do you study English? (как часто)", "options": ["How often", "How many", "How much"], "correct": 0},
            {"q": "Напишите по-английски: «Где вы работаете?»",
             "answer": "Where do you work", "accept": ["Where do you work?", "Where do you work at?"]},
        ],
    },
    "must_should": {
        "items": [
            {"q": "Тебе стоит отдохнуть. - You ___ rest.", "options": ["should", "must", "have to"], "correct": 0},
            {"q": "Мне приходится вставать рано. - I ___ get up early.", "options": ["have to", "should", "must to"], "correct": 0},
            {"q": "Строгое правило: You ___ stop here.", "options": ["must", "should", "can"], "correct": 0},
            {"q": "«Нельзя» (запрет): You ___ smoke here.", "options": ["mustn't", "don't have to", "shouldn't"], "correct": 0},
            {"q": "Совет: You ___ drink more water.", "options": ["should", "must", "have to"], "correct": 0},
        ],
    },
}
