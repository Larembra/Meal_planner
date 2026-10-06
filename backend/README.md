# Backend Meal Planner

Backend построен на FastAPI, PostgreSQL, SQLAlchemy 2.0 с async-подключением,
Alembic, Pydantic v2 и JWT-аутентификацией.

## Локальный запуск без Docker

Установите PostgreSQL и создайте базу:

```bash
brew install postgresql@16
brew services start postgresql@16
createdb meal_planner
```

Перейдите в каталог backend и создайте виртуальное окружение:

```bash
cd /Users/artem/PycharmProjects/Meal_planner/backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Создайте `.env` на основе `.env.example`. Для локального PostgreSQL используйте
адрес `localhost`, а не `db`:

```env
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/meal_planner
SECRET_KEY=change-me-in-production
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7
DEBUG=false
```

Если у локального пользователя PostgreSQL нет пароля, используйте:

```env
DATABASE_URL=postgresql+asyncpg://postgres@localhost:5432/meal_planner
```

Примените миграции и заполните демонстрационные данные:

```bash
alembic upgrade head
python seed.py
```

Запустите приложение:

```bash
uvicorn app.main:app --reload --port 8000
```

Проверка доступности:

```text
http://localhost:8000/health
http://localhost:8000/docs
```

## Запуск через Docker

Из каталога backend:

```bash
docker compose up --build
```

## Тесты

```bash
pytest -q
```

## Основные маршруты

- `/api/v1/auth` — регистрация, вход, refresh, выход и текущий пользователь;
- `/api/v1/users/me/profile` — профиль пользователя;
- `/api/v1/rations` — создание и просмотр рационов;
- `/api/v1/dishes` — публичный каталог блюд;
- `/api/v1/applications` — заявки пользователя;
- `/api/v1/diary` — дневник питания;
- `/api/v1/moderator/recipes` — рецепты модератора.

Тестовые пользователи после запуска `seed.py`:

```text
client@test.ru / password123
moderator@test.ru / password123
```

Файл `.env` содержит локальные настройки и не должен добавляться в Git.
