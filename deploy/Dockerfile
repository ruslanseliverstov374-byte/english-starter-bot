# English Starter — образ для запуска бота 24/7.
# Сборка из корня проекта:  docker build -t english-bot -f deploy/Dockerfile .

FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    DB_PATH=/data/bot.db

WORKDIR /app

COPY *.py ./
COPY content/ ./content/
COPY tools/ ./tools/

# Прогресс учеников хранится в томе /data
RUN mkdir -p /data
VOLUME ["/data"]

# Порт нужен только в режиме webhook (облако). В режиме long polling не используется.
EXPOSE 8080

# BOT_TOKEN - обязательная переменная окружения.
# Если задан WEBHOOK_URL - бот поднимет HTTP-сервер и встанет на webhook,
# иначе будет работать через long polling.
CMD ["python", "bot.py"]
