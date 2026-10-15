# Crypto Tracker — Deribit Price Collector

Сервис каждую минуту получает index price пар `btc_usd` и `eth_usd` с биржи Deribit,
сохраняет их в PostgreSQL и предоставляет REST API для чтения сохранённых данных.

## Стек

- Python 3.11
- FastAPI + Uvicorn
- SQLAlchemy 2.0 (async) + asyncpg
- aiohttp (клиент Deribit)
- Celery + Redis (периодические задачи)
- PostgreSQL 15
- Docker / Docker Compose
- pytest + pytest-asyncio (тесты)

## Быстрый старт

```bash
cp .env.example .env
docker compose up -d --build
```

API будет доступно по адресу `http://localhost:8000`.
Документация Swagger: `http://localhost:8000/docs`.

## Эндпоинты

Все методы — GET, обязательный query-параметр `ticker` (`BTC` или `ETH`).

| Метод | Путь | Описание |
|-------|------|----------|
| GET | `/api/prices?ticker=BTC` | Все сохранённые данные по тикеру |
| GET | `/api/prices/latest?ticker=ETH` | Последняя цена тикера |
| GET | `/api/prices/filter?ticker=BTC&start=…&end=…` | Цены в диапазоне UNIX timestamp |

## Design decisions

### 1. Слоистая архитектура

Проект разделён на независимые слои:

- **`api/`** — только HTTP-слой: валидация query-параметров, вызов CRUD, формирование ответа.
- **`crud.py`** — доступ к данным. Все SQL-запросы инкапсулированы здесь; роутеры не знают о SQLAlchemy.
- **`services/`** — внешние интеграции. `DeribitClient` полностью изолирует работу с Deribit API.
- **`models.py` / `schemas.py`** — отдельно ORM-модели и Pydantic-схемы, чтобы не смешивать представление БД и API.

Такое разделение упрощает тестирование: клиент Deribit можно замокать, CRUD можно тестировать отдельно от HTTP-слоя.

### 2. Полностью асинхронный стек

FastAPI, SQLAlchemy 2.0 (async), asyncpg и aiohttp работают в едином event loop.
Это позволяет эффективно обрабатывать конкурентные запросы без блокировки потоков.
Для периодической задачи Celery использует `asyncio.run` внутри воркера — это совместимо
с prefork-моделью, но при необходимости легко заменить на отдельный event loop.

### 3. Celery + Redis для периодичности

Celery Beat запускает задачу `fetch_prices` каждые 60 секунд. Redis выбран как брокер
из-за простоты развёртывания в Docker. Задача не хранит состояние между запусками,
поэтому идемпотентность достигается за счёт естественного ключа `(ticker, timestamp)`.

### 4. Хранение времени в UNIX timestamp

Поле `timestamp` — целое число (`BigInteger`). Это удобно для фильтрации по диапазону
(`WHERE timestamp >= start AND timestamp <= end`) и не зависит от часового пояса.
На уровне API клиент передаёт и получает целые числа.

### 5. Отсутствие глобальных переменных

Все зависимости (настройки, сессии, клиенты) передаются явно:

- настройки — через `Settings` (Pydantic Settings);
- сессия БД — через `Depends(get_session)` в FastAPI;
- клиент Deribit — через контекстный менеджер внутри задачи.

Глобальных синглтонов нет, что упрощает тестирование и повторное использование кода.

### 6. Два контейнера для приложения и БД (и Redis)

`docker-compose.yml` поднимает PostgreSQL, Redis, FastAPI и Celery (worker + beat).
Это соответствует необязательному требованию «развернуть приложение в двух контейнерах
для приложения и базы данных»: FastAPI и Celery — контейнеры приложения, PostgreSQL — БД,
Redis — инфраструктурный компонент для очереди задач.

### 7. Обработка ошибок

Если по тикеру нет данных, эндпоинт `/api/prices/latest` возвращает `404`.
Клиент Deribit вызывает `raise_for_status()`, чтобы не сохранять некорректные ответы.
