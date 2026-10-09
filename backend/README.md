# Backend Meal Planner

FastAPI работает с PostgreSQL схемы, поставляемой в `data/seed.sql`. Снимок создаётся скриптом `data/create_database.py`. API не создаёт и не мигрирует таблицы при запуске: сначала создайте базу из снимка. Не запускайте прежнюю миграцию создания таблиц; единственная текущая миграция расширяет допустимое значение слота рациона и запускается вручную по инструкции ниже.

## Windows: запуск через Docker Desktop (рекомендуется)

Нужны Git, Docker Desktop с включённым Linux containers и Node.js LTS. Для генерации рациона также нужен ключ OpenRouter. Команды выполняются в PowerShell из корня репозитория.

Создайте локальный файл настроек из шаблона, если его ещё нет, и внесите в `backend/.env` свои значения `OPENROUTER_API_KEY`, `SECRET_KEY`, `ACCESS_TOKEN_EXPIRE_MINUTES`, `REFRESH_TOKEN_EXPIRE_DAYS` и `DATABASE_URL`:

```powershell
if (!(Test-Path backend\.env)) { Copy-Item backend\.env.example backend\.env }
notepad backend\.env
```

Контейнер API получает настройки через `env_file: .env`. Значение `DATABASE_URL` внутри контейнера автоматически заменяется адресом сервиса PostgreSQL `db`; остальные настройки берутся из файла.

1. Запустите PostgreSQL с установленным pgvector:

   ```powershell
   cd backend
   docker compose up -d db
   ```

2. Соберите образ API и установите снимок базы данных:

   ```powershell
   docker compose build api
   docker compose run --rm api python data/create_database.py
   ```

   Команда создаёт базу `Meal_planner` и загружает `data/seed.sql`. Скрипт проверяет наличие расширений и целевой базы, поэтому повторное выполнение для уже созданной базы завершится сообщением о том, что база существует. Для пересоздания базы удалите volume `backend_postgres_data` командой `docker compose down -v` — это удалит данные PostgreSQL.

   Примените миграцию, которая добавляет отдельный слот второго завтрака к существующему ограничению БД (таблицы и их связи не меняются):

   ```powershell
   docker compose run --rm api alembic upgrade head
   ```

3. Запустите API:

   ```powershell
   docker compose up api
   ```

   API доступен на `http://localhost:8000`, документация — `http://localhost:8000/docs`, проверка — `http://localhost:8000/health`.

4. В другом окне PowerShell запустите фронтенд:

   ```powershell
   cd frontend
   npm ci
   npm start
   ```

   Откройте `http://localhost:3000`. Адрес API по умолчанию уже настроен на `http://localhost:8000/api/v1`.

При первом старте зарегистрируйте пользователя через интерфейс. В снимке разрешены только роли `user` и `admin`; для работы с созданием рецептов назначьте нужному пользователю роль администратора SQL-командой из psql:

```sql
UPDATE users SET role = 'admin' WHERE email = 'ваш-email@example.com';
```

В Docker psql можно открыть так (из каталога `backend`):

```powershell
docker compose exec db psql -U postgres -d Meal_planner
```

## Windows: запуск API локально

Для нативного запуска установите Python 3.11 или 3.12 и PostgreSQL 16 с серверными расширениями `pgcrypto` и `vector` (pgvector). Установка `sentence-transformers` скачивает PyTorch и модель эмбеддингов; первый запуск генерации дополнительно скачает `paraphrase-multilingual-MiniLM-L12-v2`. Создайте базу именно через снимок, а не через `alembic upgrade`.

Из корня проекта:

```powershell
cd backend
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

Если PowerShell запрещает активацию окружения, разрешите скрипты только для текущего окна:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

Задайте параметры, совпадающие с PostgreSQL-пользователем, и установите снимок. Значения по умолчанию скрипта — `localhost:5432`, пользователь и пароль `postgres`, база `Meal_planner`:

```powershell
$env:PGHOST = "localhost"
$env:PGPORT = "5432"
$env:PGUSER = "postgres"
$env:PGPASSWORD = "ваш-пароль"
$env:PGDATABASE = "Meal_planner"
python data/create_database.py
alembic upgrade head
```

Сначала загружается снимок исходной схемы, затем вручную применяется миграция слота второго завтрака. Приложение читает `DATABASE_URL`, `SECRET_KEY`, сроки токенов и `OPENROUTER_API_KEY` непосредственно из `backend/.env`. Проверьте, что в файле указан URL локальной базы (`localhost`), затем запустите сервер:

```powershell
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Откройте `http://localhost:8000/docs`. Для остановки сервера нажмите `Ctrl+C`; для выхода из виртуального окружения выполните `deactivate`.

## Настройки

- `DATABASE_URL` — async SQLAlchemy URL, например `postgresql+asyncpg://postgres:password@localhost:5432/Meal_planner`.
- `SECRET_KEY` — секрет для JWT; задайте свой для локального и производственного запуска.
- `ACCESS_TOKEN_EXPIRE_MINUTES` — срок access-токена (по умолчанию 30 минут).
- `REFRESH_TOKEN_EXPIRE_DAYS` — срок refresh-токена (по умолчанию 7 дней).
- `DEBUG` — включает SQL-логирование при значении `true`.
- `OPENROUTER_API_KEY` — обязательный ключ OpenRouter для `/api/v1/rations/generate`.
- `OPENROUTER_MODEL` — модель по умолчанию `apodex/apodex-1.1-mini:free`; запрос может передать другую модель.
- `EMBEDDING_MODEL` — модель поиска по векторным эмбеддингам; по умолчанию `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`.
- `OPENROUTER_TIMEOUT_SECONDS` — таймаут запроса модели (по умолчанию 120 секунд).
- `PGHOST`, `PGPORT`, `PGUSER`, `PGPASSWORD`, `PGDATABASE` — настройки скрипта создания базы.

`POST /api/v1/rations/generate` требует авторизацию и `OPENROUTER_API_KEY`. Тело запроса:

```json
{
  "period_days": 7,
  "tags": ["Больше белка"],
  "extra_request": "Простые блюда из доступных продуктов",
  "model": "apodex/apodex-1.1-mini:free"
}
```

Поле `model` можно опустить — тогда используется `OPENROUTER_MODEL`. Ответ генерации содержит запись рациона; план блюд возвращается через `GET /api/v1/rations/{id}/plan`. Число блюд может различаться по дням. Профиль поддерживает от 3 до 5 приёмов пищи; для второго завтрака применяется отдельный слот `second_breakfast`, а блюда для обоих завтраков выбираются из одного набора кандидатов `breakfast`.

Схема базы остаётся определённой файлами в `data/`; запуск приложения не создаёт дополнительные таблицы. Текущие маршруты: `/api/v1/auth`, `/api/v1/users/me/profile`, `/api/v1/dishes`, `/api/v1/recipes`, `/api/v1/rations`, `/api/v1/diary` и `/api/v1/moderator/recipes`.
