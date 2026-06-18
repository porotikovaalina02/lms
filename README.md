# LMS Quiz

Тесты в Telegram. Backend на FastAPI, база PostgreSQL.

Бот: [@lms_quiz_bot](https://t.me/lms_quiz_bot)

## Функции

- прохождение тестов через inline-кнопки
- сохранение результатов в базу
- просмотр истории попыток

## Стек

- FastAPI + SQLAlchemy
- PostgreSQL 16
- aiogram 3
- Docker Compose

## Запуск

**1. Бот**

Токен нужно взять у [@BotFather](https://t.me/BotFather) → `/newbot`

**2. Настройка**

```bash
cp .env.example .env
```

В `.env` нужно вставить `BOT_TOKEN=...`

**3. Docker**

```bash
docker compose up --build
```

Поднимутся:
- api — http://localhost:8000
- docs — http://localhost:8000/docs
- postgres (внутри docker-сети)
- telegram-бот

При первом старте в базу заливаются 2 теста (python + sql).

## Бот

| Команда | Описание |
|---------|----------|
| `/start` | меню |
| `/tests` | список тестов |
| `/results` | твои результаты |

## API

```
GET  /api/tests
GET  /api/tests/{id}/public
POST /api/tests/{id}/submit
GET  /api/users/{telegram_id}/attempts
```

## Структура

```
backend/app/   — api, модели, seed
bot/bot.py     — telegram-бот
docker-compose.yml
```

## Остановка

```bash
docker compose down
```

Сбросить базу:

```bash
docker compose down -v
```
