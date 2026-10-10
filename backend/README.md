# Backend Meal Planner

Бэкенд — FastAPI с PostgreSQL и pgvector. Готовая схема и данные находятся в `data/seed.sql`; база создаётся скриптом `data/create_database.py`. API не создаёт таблицы при старте. Для генерации рациона нужен ключ OpenRouter в `backend/.env`.

## Рекомендуемый запуск на macOS (Docker только для PostgreSQL)

Используйте этот вариант для текущей версии проекта. Не запускайте одновременно
`docker compose up api` и локальный Uvicorn: оба процесса используют порт `8000`.

### 1. Запустить PostgreSQL

Из корня проекта:

```bash
cd /Users/artem/PycharmProjects/Meal_planner/backend
docker compose up -d db
docker compose ps
```

Контейнер `backend-db-1` должен иметь статус `Up` или `healthy`.

### 2. Применить миграции

```bash
DATABASE_URL='postgresql+asyncpg://postgres:postgres@127.0.0.1:55432/Meal_planner' \
.venv/bin/alembic upgrade head
```

### 3. Запустить backend

Оставьте этот терминал открытым:

```bash
DATABASE_URL='postgresql+asyncpg://postgres:postgres@127.0.0.1:55432/Meal_planner' \
.venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

Проверка во втором терминале:

```bash
curl http://127.0.0.1:8000/health
```

Ожидаемый ответ: `{"status":"ok"}`.

### 4. Запустить frontend

В третьем терминале:

```bash
cd /Users/artem/PycharmProjects/Meal_planner/frontend
npm start
```

Откройте `http://localhost:3000`. Backend Swagger доступен по адресу
`http://127.0.0.1:8000/docs`.

Если появляется `Failed to fetch`, сначала проверьте `/health`, затем убедитесь,
что frontend и backend запущены одновременно. Для CORS разрешены `localhost` и
`127.0.0.1` на портах `3000` и `5173`.

Если порт занят, найдите конкретный процесс и остановите его:

```bash
lsof -nP -iTCP:8000 -sTCP:LISTEN
kill <PID>
```

Не используйте `kill` без PID и не запускайте второй backend поверх работающего.

### 5. Если браузер показывает старую версию

В DevTools откройте Console и выполните:

```js
localStorage.clear()
location.href = "/"
```

Без токена гостю доступна только главная страница, а переходы на защищённые
страницы перенаправляют на `/login`.

## macOS: запуск через Docker Desktop

Это рекомендуемый способ для macOS: PostgreSQL и pgvector запускаются в контейнере, поэтому устанавливать их отдельно через Homebrew не нужно.

### 1. Установите необходимое ПО

- Docker Desktop для Mac и запустите его. Дождитесь статуса **Docker Desktop is running**.
- Node.js LTS с npm для фронтенда.
- Git (обычно уже установлен вместе с Command Line Tools).

Проверьте доступность команд в Terminal:

```bash
docker --version
docker compose version
node --version
npm --version
```

### 2. Создайте `backend/.env`

Откройте Terminal в корне проекта и скопируйте шаблон:

```bash
cp backend/.env.example backend/.env
```

Откройте файл в редакторе, например:

```bash
open -e backend/.env
```

Заполните его в таком формате:

```dotenv
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/Meal_planner
SECRET_KEY=замените-на-длинную-случайную-строку
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7
DEBUG=false
OPENROUTER_API_KEY=sk-or-v1-ваш-ключ
OPENROUTER_TIMEOUT_SECONDS=120
EMBEDDING_MODEL=sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2
OPENROUTER_MODEL=apodex/apodex-1.1-mini:free
```

Сгенерировать случайный секрет можно командой `openssl rand -hex 32`; вставьте её результат вместо значения `SECRET_KEY`. Получите API-ключ OpenRouter в своём аккаунте и замените пример `OPENROUTER_API_KEY` на настоящий ключ. Не добавляйте `backend/.env` в Git.

При запуске через Docker Compose значение `DATABASE_URL` внутри контейнера API автоматически заменяется адресом контейнера БД (`db`). Указанный в файле адрес `localhost` пригодится при локальном запуске API без Docker.

### 3. Создайте базу из снимка проекта

Перейдите в каталог `backend` и запустите PostgreSQL:

```bash
cd backend
docker compose up -d db
```

Соберите API-образ и загрузите схему с данными:

```bash
docker compose build api
docker compose run --rm api python data/create_database.py
```

Скрипт создаёт базу `Meal_planner` и загружает `data/seed.sql`. В снимке уже разрешён слот `second_breakfast`, поэтому для новой базы отдельная Alembic-миграция не требуется. Скрипт намеренно откажется перезаписывать существующую базу.

### 4. Запустите API

В каталоге `backend` выполните:

```bash
docker compose up api
```

Оставьте это окно Terminal открытым. API будет доступен по адресам:

- `http://localhost:8000/health` — проверка доступности;
- `http://localhost:8000/docs` — интерактивная документация API.

### 5. Запустите фронтенд

Откройте второе окно Terminal, перейдите в корень проекта и запустите React-приложение:

```bash
cd путь/к/Meal_planner/frontend
npm ci
npm start
```

Откройте `http://localhost:3000`. Фронтенд уже настроен на API `http://localhost:8000/api/v1`. Зарегистрируйте пользователя и войдите. Настройте профиль; для генерации рациона должен быть задан рабочий `OPENROUTER_API_KEY`.

### Остановка и пересоздание базы

Остановите API сочетанием `Ctrl+C`. В каталоге `backend` остановить контейнеры можно командой:

```bash
docker compose down
```

Если нужно полностью удалить базу и создать её заново, удалите Docker volume (это удалит все данные в этой базе), затем повторите шаги создания БД:

```bash
docker compose down -v
docker compose up -d db
docker compose run --rm api python data/create_database.py
```

### Полезные команды

Открыть `psql` внутри контейнера PostgreSQL:

```bash
docker compose exec db psql -U postgres -d Meal_planner
```

Посмотреть логи API:

```bash
docker compose logs -f api
```

## Windows: запуск через Docker Desktop

Установите Docker Desktop и Node.js LTS. Из PowerShell в корне проекта создайте настройки:

```powershell
if (!(Test-Path backend\.env)) { Copy-Item backend\.env.example backend\.env }
notepad backend\.env
```

Заполните `OPENROUTER_API_KEY` и `SECRET_KEY`, затем запустите команды:

```powershell
cd backend
docker compose up -d db
docker compose build api
docker compose run --rm api python data/create_database.py
docker compose up api
```

В новом окне PowerShell из корня проекта запустите фронтенд:

```powershell
cd frontend
npm ci
npm start
```

Откройте `http://localhost:3000`. Для проверки API используйте `http://localhost:8000/health` и `http://localhost:8000/docs`.

### Если `create_database.py` сообщает `password authentication failed`

Docker хранит данные PostgreSQL в volume. Переменная `POSTGRES_PASSWORD` задаёт пароль только при первом создании этого volume; изменение `docker-compose.yml` или `.env` не меняет пароль в уже инициализированной базе. Чтобы сохранить данные, из каталога `backend` поменяйте пароль роли на тот, который использует Compose:

```powershell
docker compose exec db psql -U postgres -d postgres -c "ALTER ROLE postgres WITH PASSWORD 'postgres';"
```

Затем повторите создание базы:

```powershell
docker compose run --rm api python data/create_database.py
```

Если PostgreSQL-контейнер не позволяет выполнить команду или данные в volume не нужны, можно пересоздать volume. **Это удалит все базы и данные в нём.** Из `backend` выполните:

```powershell
docker compose down -v
docker compose up -d db
docker compose run --rm api python data/create_database.py
```

## Windows: локальный запуск API

Для запуска без Docker установите Python 3.11 или 3.12, PostgreSQL 16 с серверным расширением pgvector и Node.js LTS. Убедитесь, что PostgreSQL доступен на `localhost:5432`, а роль, указанная в `PGUSER`, может создавать базы данных и расширения.

В PowerShell из корня репозитория подготовьте окружение и настройки:

```powershell
cd backend
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
if (!(Test-Path .env)) { Copy-Item .env.example .env }
notepad .env
```

Укажите в `.env` URL вашей локальной базы и настоящий `OPENROUTER_API_KEY`. Задайте параметры подключения для скрипта снимка (пример ниже использует пользователя `postgres`):

```powershell
$env:PGHOST = "localhost"
$env:PGPORT = "5432"
$env:PGUSER = "postgres"
$env:PGPASSWORD = "ваш-пароль"
$env:PGDATABASE = "Meal_planner"
python data/create_database.py
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Откройте второе окно PowerShell для фронтенда:

```powershell
cd путь\к\Meal_planner\frontend
npm ci
npm start
```

Откройте `http://localhost:3000`. Если PowerShell запрещает активацию виртуального окружения, выполните `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass` в этом окне и активируйте `.venv` снова.

## Настройки

- `DATABASE_URL` — URL PostgreSQL для API. В Docker Compose он переопределяется на внутренний адрес контейнера базы.
- `SECRET_KEY` — секрет для подписи JWT; используйте длинное случайное значение.
- `ACCESS_TOKEN_EXPIRE_MINUTES` и `REFRESH_TOKEN_EXPIRE_DAYS` — сроки действия токенов.
- `OPENROUTER_API_KEY` — ключ, необходимый для генерации рациона.
- `OPENROUTER_MODEL` — модель по умолчанию: `apodex/apodex-1.1-mini:free`; запрос генерации может указать другую модель.
- `OPENROUTER_TIMEOUT_SECONDS` — таймаут запроса к модели.
- `EMBEDDING_MODEL` — модель эмбеддингов для поиска блюд.
- `DEBUG` — включает SQL-логирование при `true`.

Скрипт создания базы использует переменные `PGHOST`, `PGPORT`, `PGUSER`, `PGPASSWORD` и `PGDATABASE`. В Docker Compose они уже настроены на PostgreSQL-контейнер.

## Основные API-маршруты

- `/api/v1/auth` — регистрация, вход и авторизация;
- `/api/v1/users/me/profile` — профиль и настройки питания;
- `/api/v1/dishes` и `/api/v1/recipes` — каталог блюд и рецепты;
- `/api/v1/rations` — генерация и просмотр сохранённых рационов;
- `/api/v1/diary` — трекинг приёмов пищи;
- `/api/v1/moderator/recipes` — управление рецептами модератором.
