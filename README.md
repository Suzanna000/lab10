# Лабораторная работа №10, вариант 3

ФИО: Буниатян Сюзанна Смбатовна
Группа: 221131

Микросервисы на **Go (Gin)** и **Python (FastAPI)**: валидация входных данных, JWT, проверка токена на стороне Python, HTTP-вызов Go, graceful shutdown, скрипт нагрузочного замера и опциональное сравнение RSS по PID.

## Требования

- **Go** 1.22+ (модули)
- **Python** 3.10+

## Структура репозитория

| Каталог / файл | Назначение |
|----------------|------------|
| `go-service/` | Gin: логин (JWT), защищённые маршруты, валидация JSON, логирование, graceful shutdown |
| `python-service/` | FastAPI: проверка JWT (PyJWT), прокси-вызов Go с тем же Bearer-токеном |
| `perf/bench.py` | Многопоточные запросы к `/health`, расчёт RPS; опционально RSS через `psutil` |

## Переменные окружения

Общие для двух сервисов (одинаковый секрет обязателен для согласованной проверки JWT):

| Переменная | Где | Описание |
|------------|-----|----------|
| `JWT_SECRET` | Go, Python | Секрет HMAC-SHA256. Если не задан, используется dev-значение (в логах Go будет предупреждение) |
| `PORT` | Go | Порт сервера (по умолчанию `8080`, в коде задаётся как `:` + значение) |
| `GO_SERVICE_URL` | Python | Базовый URL Go (по умолчанию `http://127.0.0.1:8080`) |

## Запуск

### 1. Go (Gin)

```powershell
cd go-service
go mod download
go build -o server.exe .
.\server.exe
```

Сервис слушает `http://127.0.0.1:8080` (если не переопределён `PORT`).

Остановка: **Ctrl+C** — выполняется graceful shutdown (до 10 с на завершение активных запросов).

### 2. Python (FastAPI)

```powershell
cd python-service
pip install -r requirements.txt
python -m uvicorn app:app --host 127.0.0.1 --port 8000
```

Остановка: **Ctrl+C** — срабатывает lifespan: закрывается HTTP-клиент к Go.

Сначала должен быть доступен Go, если используются маршруты `/upstream/*`.

## API

### Go (`:8080`)

| Метод | Путь | Описание |
|-------|------|----------|
| GET | `/health` | Проверка живости |
| POST | `/auth/login` | Тело JSON: логин и пароль с валидацией → выдача JWT |
| GET | `/api/protected` | Заголовок `Authorization: Bearer <token>` |
| POST | `/api/profile` | Сложная структура JSON + JWT |

**Валидация логина** (`POST /auth/login`):

- `username`: обязательно, длина 3–32, только буквы и цифры (`alphanum`)
- `password`: обязательно, длина 8–128

### Python (`:8000`)

| Метод | Путь | Описание |
|-------|------|----------|
| GET | `/health` | Статус и указание upstream |
| GET | `/jwt/verify` | Проверка Bearer JWT тем же секретом, что и в Go |
| GET | `/upstream/protected` | Сначала проверка JWT в Python, затем `GET` к Go `/api/protected` с тем же токеном |

## Нагрузочный скрипт

Из корня репозитория, при запущенных обоих сервисах:

```powershell
python perf/bench.py
python perf/bench.py -n 2000 -w 50
python perf/bench.py --go-pid 1234 --py-pid 5678
```

Параметры:

- `-n` / `--requests` — число запросов (по умолчанию 800)
- `-w` / `--workers` — число потоков (по умолчанию 40)
- `--go-url`, `--py-url` — URL для замера (по умолчанию `/health` обоих сервисов)
- `--go-pid`, `--py-pid` — при указании выводится RSS (MiB); нужен пакет `psutil` (уже в `python-service/requirements.txt`)

Для более тяжёлой нагрузки можно дополнительно использовать **wrk** или **Apache Bench (ab)** — они в проект не входят.

## Зависимости Go

Указаны в `go-service/go.mod`: Gin, `github.com/golang-jwt/jwt/v5`. Подтягиваются командой `go mod download`.

## Зависимости Python

Файл `python-service/requirements.txt`: FastAPI, Uvicorn, HTTPX, PyJWT, psutil.
