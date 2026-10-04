# -*- coding: utf-8 -*-
"""Диалоги и фразы дня.

Формат:
    id, week, title, lines: [(кто, реплика), ...], note, quiz: [ {q, options, correct} ]
"""

DIALOGUES = [
    {
        "id": "first_hello",
        "week": 1,
        "title": "Первое hello",
        "lines": [
            ("A", "Hello!"),
            ("B", "Hi! How are you?"),
            ("A", "I am fine, thanks. And you?"),
            ("B", "I am fine too. Goodbye!"),
            ("A", "Bye! See you later."),
        ],
        "note": "Пять фраз - уже маленький разговор. Проговорите его вслух два раза.",
        "quiz": [
            {
                "q": "Что ответить на «How are you?»",
                "options": ["I am fine, thanks.", "My name is Anna.", "Goodbye!"],
                "correct": 0,
            }
        ],
    },
    {
        "id": "meeting",
        "week": 2,
        "title": "Знакомство",
        "lines": [
            ("A", "Hello! My name is Anna. What is your name?"),
            ("B", "Hi, Anna! I am Oleg. Nice to meet you."),
            ("A", "Nice to meet you too. Where are you from?"),
            ("B", "I am from Russia. And you?"),
            ("A", "I am from Russia too. See you!"),
        ],
        "note": "«Nice to meet you» - при знакомстве, «Nice to see you» - при встрече знакомых.",
        "quiz": [
            {
                "q": "Как ответить на «Nice to meet you»?",
                "options": ["Nice to meet you too.", "I am from Russia.", "Thank you very much."],
                "correct": 0,
            }
        ],
    },
    {
        "id": "small_talk",
        "week": 4,
        "title": "Как дела: короткий разговор",
        "lines": [
            ("A", "Good morning, Kate!"),
            ("B", "Good morning! How are you today?"),
            ("A", "I am a little tired, but fine. And you?"),
            ("B", "I am fine, thanks. Have a nice day!"),
            ("A", "You too! Bye!"),
        ],
        "note": "«You too!» - универсальный ответ на пожелание. «Have a nice day!» - хорошего дня.",
        "quiz": [
            {
                "q": "Что значит «Have a nice day!»",
                "options": ["Хорошего дня!", "Как дела?", "До завтра!"],
                "correct": 0,
            }
        ],
    },
    {
        "id": "cafe",
        "week": 3,
        "title": "В кафе",
        "lines": [
            ("Waiter", "Good afternoon! Can I help you?"),
            ("You", "Yes, I would like a cup of tea and a sandwich, please."),
            ("Waiter", "Anything else?"),
            ("You", "No, thank you. How much is it?"),
            ("Waiter", "That is five dollars."),
            ("You", "Here you are. Thank you!"),
        ],
        "note": "«Anything else?» - «Что-нибудь ещё?» «Here you are» - «Вот, пожалуйста».",
        "quiz": [
            {
                "q": "Как заказать чай вежливо?",
                "options": ["Give me tea.", "I would like a cup of tea, please.", "I want tea now."],
                "correct": 1,
            }
        ],
    },
    {
        "id": "my_day",
        "week": 5,
        "title": "Мой день",
        "lines": [
            ("A", "What time do you get up?"),
            ("B", "I get up at seven and have breakfast at half past seven."),
            ("A", "When do you go to work?"),
            ("B", "I go to work at eight. I come home at six."),
            ("A", "And what do you do in the evening?"),
            ("B", "I read or watch films. I go to bed at eleven."),
        ],
        "note": "«half past seven» - половина восьмого (7:30). «at» - перед временем.",
        "quiz": [
            {
                "q": "«half past seven» - это",
                "options": ["7:30", "6:30", "7:15"],
                "correct": 0,
            }
        ],
    },
    {
        "id": "in_the_city",
        "week": 6,
        "title": "Как пройти",
        "lines": [
            ("You", "Excuse me, where is the metro station?"),
            ("Man", "Go straight and turn left at the corner."),
            ("You", "Is it far from here?"),
            ("Man", "No, it is near. About five minutes."),
            ("You", "Thank you very much!"),
            ("Man", "You are welcome."),
        ],
        "note": "«You are welcome» - «пожалуйста» в ответ на спасибо.",
        "quiz": [
            {
                "q": "«Turn left at the corner» значит",
                "options": ["Поверните налево на углу", "Идите прямо до угла", "Поверните направо"],
                "correct": 0,
            }
        ],
    },
    {
        "id": "shopping",
        "week": 7,
        "title": "В магазине",
        "lines": [
            ("You", "Excuse me, how much is this T-shirt?"),
            ("Seller", "It is twenty dollars."),
            ("You", "Do you have it in size forty-two?"),
            ("Seller", "Yes, here you are."),
            ("You", "Great. Can I pay by card?"),
            ("Seller", "Of course."),
        ],
        "note": "«Do you have it in size ...?» - универсальная фраза о размере.",
        "quiz": [
            {
                "q": "Как спросить цену?",
                "options": ["How much is it?", "How many is it?", "What is it?"],
                "correct": 0,
            }
        ],
    },
    {
        "id": "doctor",
        "week": 8,
        "title": "У врача",
        "lines": [
            ("Doctor", "Good morning! What is the problem?"),
            ("You", "I have a headache and I feel tired."),
            ("Doctor", "Do you have a temperature?"),
            ("You", "Yes, thirty-eight."),
            ("Doctor", "You should rest and take this medicine twice a day."),
            ("You", "Thank you, doctor."),
        ],
        "note": "«I have a headache» - «у меня болит голова». Боль: I have a pain in my leg.",
        "quiz": [
            {
                "q": "«У меня болит голова» -",
                "options": ["I have a headache.", "My head is headache.", "I am head pain."],
                "correct": 0,
            }
        ],
    },
    {
        "id": "weather_chat",
        "week": 8,
        "title": "Разговор о погоде",
        "lines": [
            ("A", "It is a lovely day today, isn't it?"),
            ("B", "Yes, it is warm and sunny. But it will rain tomorrow."),
            ("A", "Really? I don't like rain."),
            ("B", "Me too. Let's go to the park now."),
            ("A", "Good idea!"),
        ],
        "note": "Погода - самая безопасная тема small talk. «isn't it?» - «не так ли?»",
        "quiz": [
            {
                "q": "«It will rain» - это",
                "options": ["Будет дождь", "Сейчас дождь", "Вчера был дождь"],
                "correct": 0,
            }
        ],
    },
    {
        "id": "work_meeting",
        "week": 9,
        "title": "На работе",
        "lines": [
            ("Boss", "Good morning! Do you have five minutes?"),
            ("You", "Of course. What can I do?"),
            ("Boss", "We have a meeting at two. Can you prepare the report?"),
            ("You", "Yes, I can. I will send it before the meeting."),
            ("Boss", "Great, thank you."),
        ],
        "note": "«Do you have five minutes?» - вежливое начало разговора на работе.",
        "quiz": [
            {
                "q": "«I will send it» значит",
                "options": ["Я отправлю это", "Я отправил это", "Я отправляю это сейчас"],
                "correct": 0,
            }
        ],
    },
    {
        "id": "phone",
        "week": 9,
        "title": "Телефонный звонок",
        "lines": [
            ("A", "Hello, this is Anna speaking."),
            ("B", "Hello, Anna! This is Oleg. Can you talk now?"),
            ("A", "Sorry, I am busy at the moment. Can I call you back?"),
            ("B", "Of course. Call me in an hour."),
            ("A", "OK, thank you. Bye!"),
        ],
        "note": "По телефону о себе говорят «This is ... speaking», а не «I am ...».",
        "quiz": [
            {
                "q": "Как представиться по телефону?",
                "options": ["This is Anna speaking.", "I am Anna speaking you.", "My name Anna."],
                "correct": 0,
            }
        ],
    },
    {
        "id": "hotel",
        "week": 10,
        "title": "В отеле",
        "lines": [
            ("You", "Good evening! I have a booking for two nights."),
            ("Receptionist", "What is your name, please?"),
            ("You", "Ivan Petrov."),
            ("Receptionist", "Yes, room three hundred and five. Here is your key."),
            ("You", "What time is breakfast?"),
            ("Receptionist", "From seven to ten. Have a nice stay!"),
        ],
        "note": "«I have a booking» - «у меня бронь». Номер комнаты читают по цифрам.",
        "quiz": [
            {
                "q": "«I have a booking for two nights» значит",
                "options": ["У меня бронь на две ночи", "Я хочу забронировать номер", "Я живу здесь две недели"],
                "correct": 0,
            }
        ],
    },
    {
        "id": "airport",
        "week": 11,
        "title": "В аэропорту",
        "lines": [
            ("You", "Excuse me, where is the check-in for flight four one two?"),
            ("Staff", "It is over there, next to the cafe."),
            ("You", "Thank you. And what time does the plane leave?"),
            ("Staff", "At six thirty. Please, show your passport."),
            ("You", "Here it is."),
        ],
        "note": "«check-in» - регистрация на рейс, «flight» - рейс.",
        "quiz": [
            {
                "q": "«Where is the check-in?» - вопрос про",
                "options": ["регистрацию на рейс", "выход к самолёту", "багаж"],
                "correct": 0,
            }
        ],
    },
    {
        "id": "weekend_invite",
        "week": 12,
        "title": "Приглашение на выходные",
        "lines": [
            ("A", "What are you going to do at the weekend?"),
            ("B", "I am going to visit my parents. And you?"),
            ("A", "We are going to have a picnic in the park. Would you like to come?"),
            ("B", "I would love to! What time?"),
            ("A", "At twelve, on Sunday."),
            ("B", "Great, see you there!"),
        ],
        "note": "«Would you like to come?» - приглашение. Ответ: «I would love to!» (С радостью!)",
        "quiz": [
            {
                "q": "Как пригласить друга?",
                "options": ["Would you like to come?", "You come to park.", "Do you come?"],
                "correct": 0,
            }
        ],
    },
]
