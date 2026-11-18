# MusicAccess — ПАСЗИ, лабораторная №4

Музыкальный сервис на React + TypeScript + Vite, FastAPI/Pydantic, PostgreSQL/SQLAlchemy/Alembic. Регистрация, вход и выход, удаление своего аккаунта, поиск с подсказками и URL-фильтрами, HTML5-плеер и серверная мандатная проверка доступа. Исходная тёмная фиолетовая тема сохранена.

## Быстрый запуск

Нужны Docker Desktop с Compose v2 и Python 3.13 для однократной генерации конфигурации. Из корня репозитория:

```powershell
python scripts/init_env.py
docker compose up --build
```

Первый шаг создаёт `.env` со случайными паролями и не перезаписывает существующий файл. Последующие запуски — одной командой `docker compose up --build`. Сайт: **http://localhost:8080**, API: **http://localhost:8080/api/health**. Изменение внешнего порта — `PORT` в `.env`.

Compose ждёт готовности PostgreSQL, backend применяет миграции и создаёт каталог, затем запускается frontend. PostgreSQL и backend не публикуют свои порты на хост. Frontend привязан к loopback. Данные и аудио сохраняются в именованных volumes; обычный `docker compose down` их сохраняет.

```powershell
docker compose ps
docker compose logs backend
python scripts/compose_smoke.py
```

Не добавляйте `.env` в Git. `.env.example` содержит только пустые поля секретов. После создания БД изменение `POSTGRES_PASSWORD` в `.env` само по себе не меняет пароль существующей БД.

## Демонстрационные аккаунты и музыка

`scripts/init_env.py` включает `SEED_DEMO_USERS=true` и генерирует три разных пароля в локальном `.env`:

| Логин | Допуск | Переменная с паролем |
|---|---|---|
| `demo_public` | PUBLIC = 1 | `DEMO_PUBLIC_PASSWORD` |
| `demo_confidential` | CONFIDENTIAL = 2 | `DEMO_CONFIDENTIAL_PASSWORD` |
| `demo_secret` | SECRET = 3 | `DEMO_SECRET_PASSWORD` |

Откройте `.env` локально, чтобы взять пароль для демонстрации. Не фотографируйте этот файл. Seed не сбрасывает пароли существующих пользователей и отказывается повышать допуск уже занятого демонстрационного логина. При ручном запуске создание аккаунтов выполняется только командой `python -m backend.seed --demo-users` с заданными переменными паролей. Обычный `python -m backend.seed` создаёт только треки.

Три композиции по 24 секунды: Night Drive / Electronic Waves (Public), Deep Ocean / Ambient Project (Confidential), Secret Sessions / Studio X (Secret). Это оригинальные синтезированные WAV, создаваемые `backend/seed.py`, без сторонних записей. Для демонстрации лабораторной их можно использовать свободно. Файлы находятся в `backend/media` или `MEDIA_DIR`, никогда в `frontend/public`.

## Мандатная модель

Чтение разрешено, если `user.clearance_level >= track.security_level`. Политика сосредоточена в `backend/access.py`; проверка вызывается перед выдачей каждого аудиопотока, включая Range-запросы. Метки пользователя и трека читаются из БД. Это модель допусков и классификации ресурсов, а не роли и не платная подписка. Лабораторная реализует только чтение; правила записи Bell–LaPadula здесь не заявляются.

| Пользователь → ресурс | Public | Confidential | Secret |
|---|---|---|---|
| Public | разрешено | 403 | 403 |
| Confidential | разрешено | разрешено | 403 |
| Secret | разрешено | разрешено | разрешено |
| Без сессии | 401 | 401 | 401 |

Каталог и метаданные всех треков публичны. Аудио требует входа. Новые пользователи всегда получают PUBLIC; чекбокс музыкального аккаунта — только метаданные. Поля повышения допуска в запросах отклоняются как 422. Общедоступного endpoint изменения допуска нет. Для демонстрации повышенных уровней используется доверенный seed.

## API

Все пути начинаются с `/api`. Запросы изменения данных требуют заголовок `X-MusicAccess: 1`. Для logout и удаления дополнительно нужен `X-CSRF-Token` из `/login` или `/me`.

| Метод и путь | Назначение |
|---|---|
| GET `/health` | Проверка работы процесса API |
| POST `/register` | `login`, `password`; необязательные `email`; 201, 409, 422 |
| POST `/login` | `login`, `password`; устанавливает cookie, возвращает `user` и `csrf_token`; неверный пароль — 401 |
| GET `/me` | Текущий профиль и CSRF-токен; 401 без действующей сессии |
| POST `/logout` | Отзывает текущую сессию; 204 |
| DELETE `/me` | JSON `password`, проверка CSRF; удаляет профиль и все его сессии; 204 |
| GET `/tracks` | Каталог; `q` ищет по названию **или** исполнителю |
| GET `/tracks/search` | Тот же поиск; `title` и `artist` применяются совместно через AND |
| GET `/tracks/{id}` | Публичные метаданные одного трека; 404, если нет |
| GET `/me/tracks` | Серверный список треков, доступных текущему пользователю |
| GET `/tracks/{id}/stream` | Защищённый WAV; 200 или 206; 401/403/404/416 |

Поиск ограничен 100 символами на параметр и 100 результатами каталога; ORM использует параметризованные запросы, `%` и `_` в пользовательском поиске экранируются. URL: `/music?q=Night`, `/music?title=Night&artist=Electronic`. Debounce — 350 мс. Сброс, прямое открытие URL и история браузера поддерживаются.

### Пример curl (Bash / Git Bash)

Пароль вводится локально; значения секретов в репозитории отсутствуют. Для JSON используйте пароль без кавычек и обратной косой черты либо подготовьте JSON безопасным сериализатором.

```bash
BASE=http://localhost:8080
read -s -p 'Пароль (8+ символов, A-z, цифра, спецсимвол): ' PASSWORD; echo
curl -i "$BASE/api/register" -H 'X-MusicAccess: 1' -H 'Content-Type: application/json' \
  --data "{\"login\":\"student\",\"password\":\"$PASSWORD\"}"
curl -c cookies.txt "$BASE/api/login" -H 'X-MusicAccess: 1' -H 'Content-Type: application/json' \
  --data "{\"login\":\"student\",\"password\":\"$PASSWORD\"}"
curl -b cookies.txt "$BASE/api/me"
curl "$BASE/api/tracks?title=Night&artist=Electronic"
curl -i -b cookies.txt -H 'Range: bytes=0-9' "$BASE/api/tracks/1/stream"
curl -i -b cookies.txt "$BASE/api/tracks/2/stream"  # 403 для Public
read -p 'csrf_token из ответа login/me: ' CSRF
curl -i -b cookies.txt -X POST "$BASE/api/logout" -H 'X-MusicAccess: 1' -H "X-CSRF-Token: $CSRF"
unset PASSWORD CSRF
rm cookies.txt
```

В PowerShell используйте `curl.exe`, чтобы избежать алиаса `Invoke-WebRequest`. Cookie-файлы временные и содержат секрет сессии; не добавляйте их в Git.

## Безопасность

- Пароли хранятся только в Argon2id: по умолчанию 3 итерации, 65536 KiB памяти, параллелизм 2; параметры задаются окружением. Длина пароля 8–128, латинские заглавная/строчная буквы, цифра и специальный символ; пробел сам по себе спецсимволом не считается. Логин 3–32 символа, `[A-Za-z0-9._-]`; уникальность без учёта регистра.
- Сессия — случайный 256-битный opaque token. БД хранит SHA-256 токена, пользователя, CSRF-токен и срок 12 часов. Паролей и bearer-токенов в localStorage нет. Вход заменяет прежнюю сессию этого браузера, выход отзывает её; удаление аккаунта отзывает все его сессии.
- Cookie: `HttpOnly`, `SameSite=Lax`, host-only, `Path=/`. В `APP_ENV=production` включён `Secure`: потребуется HTTPS перед Nginx. Локальная демонстрация по HTTP использует `development`. `SECRET_KEY` предусмотрен в конфигурации как резерв; выбранные серверные сессии не подписывают JWT и не зависят от этого ключа.
- Изменяющие запросы требуют нестандартный заголовок, запрещён `Sec-Fetch-Site: cross-site`; CORS не включён. Клиент и API работают с одного origin через Vite/Nginx proxy. Аутентифицированные изменения дополнительно проверяют CSRF-токен сессии. Страница Swagger при ручных POST требует эти же заголовки.
- Поток не имеет публичного статического маршрута, путь проверяется на выход за `MEDIA_DIR`, ответы API не кэшируются. Полученные ранее разрешённые байты невозможно «отозвать» из памяти клиента; новый запрос всегда проверяется заново.
- Логи — JSON с INFO/ERROR: успешные операции, занятый логин, валидация, отказы MAC и внутренние ошибки. Пароли, cookie и CSRF-токены не логируются. Ответ 422 не содержит поле `input` с введёнными секретами.

## База данных и миграции

`users(id, login, email, password_hash, clearance_level, created_at)`, `tracks(id, title, artist, security_level, file_path, duration, created_at)`, `sessions(token_hash, user_id, csrf_token, expires_at)`. Уникальный логин, ограничения меток 1–3, внешний ключ сессий с `ON DELETE CASCADE`.

На старте проверены `main`, `feature/database`, удалённая `feature/DB` и существующие PR: опубликованной схемы БД там не было. Добавлена единая схема в `backend/models.py` и миграция `0001`, без переписывания истории или чужих веток.

```powershell
docker compose exec backend python -m alembic current
docker compose exec backend python -m alembic check
docker compose exec db psql -U musicaccess -d musicaccess -c "SELECT id, login, clearance_level, left(password_hash, 10) AS hash_scheme FROM users;"
docker compose exec db psql -U musicaccess -d musicaccess -c "SELECT id, title, artist, security_level, duration FROM tracks;"
```

## Локальная разработка без Docker

Нужен отдельно запущенный PostgreSQL с созданной БД. Из корня, PowerShell:

```powershell
python -m venv backend/.venv
backend/.venv/Scripts/python.exe -m pip install -r backend/requirements.txt
$env:POSTGRES_USER = 'musicaccess'
$env:POSTGRES_DB = 'musicaccess'
$env:POSTGRES_PASSWORD = Read-Host 'Пароль локальной БД'
backend/.venv/Scripts/python.exe -m alembic upgrade head
backend/.venv/Scripts/python.exe -m backend.seed
backend/.venv/Scripts/python.exe -m uvicorn backend.main:app --reload --port 8000
```

Во втором терминале: `cd frontend`, `npm.cmd ci`, `npm.cmd run dev`. Открыть http://localhost:5173. Backend читает переменные процесса; `.env` автоматически читает только Compose. Полный `DATABASE_URL` имеет приоритет над `POSTGRES_*`. В Linux используйте `backend/.venv/bin/python` и `npm`.

## Проверки

```powershell
backend/.venv/Scripts/python.exe -m pytest -q
cd frontend
npm.cmd run build
$env:PLAYWRIGHT_CHANNEL = 'msedge'
npm.cmd run test:e2e
```

Если Edge отсутствует: `npx.cmd playwright install chromium`, удалите `PLAYWRIGHT_CHANNEL`. Браузерные тесты сами запускают серверы на 8000/5173; эти порты должны быть свободны. Используются временные SQLite/аудиофайлы и случайные тестовые пароли. Основные pytest-тесты по умолчанию используют изолированную SQLite; `TEST_DATABASE_URL` включает PostgreSQL с отдельной случайной схемой на каждый тест. Используйте только выделенную тестовую БД.

