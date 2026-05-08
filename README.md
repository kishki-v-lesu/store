# E-Commerce Microservices Platform

Production-ready e-commerce платформа на микросервисной архитектуре.

## Архитектура

```
                    ┌─────────────┐
                    │   Nginx     │
                    │ API Gateway │
                    │  (Port 8000)│
                    └──────┬──────┘
                           │
          ┌────────────────┼────────────────┐
          │                │                │
┌─────────▼─────┐ ┌──────▼──────┐ ┌──────▼──────┐ ┌──────────────┐
│ Auth Service  │ │  Product    │ │   Order     │ │   Payment    │
│   (FastAPI)   │ │  Service    │ │   Service   │ │   Service    │
└───────┬───────┘ └──────┬──────┘ └──────┬──────┘ └──────┬───────┘
        │               │               │               │
  ┌─────▼──────┐   ┌────▼─────┐   ┌────▼─────┐   ┌─────▼──────┐
  │ PostgreSQL│   │PostgreSQL│   │PostgreSQL│   │ PostgreSQL │
  │   + Redis │   │+ Elastic │   │  + Redis  │   │            │
  └───────────┘   └──────────┘   └──────────┘   └────────────┘
                                                    │
                                           ┌────────▼────────┐
                                           │    RabbitMQ     │
                                           │  (Message Bus)  │
                                           └────────┬────────┘
                                                    │
                                           ┌────────▼────────┐
                                           │  Notification   │
                                           │    Service     │
                                           │ (Email/SMS)    │
                                           └────────────────┘
```

## Сервисы

| Сервис | Описание | Порт |
|--------|----------|------|
| **API Gateway** | Nginx reverse proxy с rate limiting | 8000 |
| **Auth Service** | Регистрация, JWT аутентификация, refresh tokens | 8001 |
| **Product Service** | Каталог товаров, Elasticsearch поиск | 8002 |
| **Order Service** | Управление заказами, stock reservation | 8003 |
| **Payment Service** | Обработка платежей, Stripe интеграция | 8004 |
| **Notification Service** | Email уведомления через RabbitMQ | - |

## Infrastructure

| Компонент | Назначение |
|-----------|------------|
| **PostgreSQL** | Основная БД (отдельная на сервис) |
| **Redis** | Кэш, сессии, token blacklist |
| **Elasticsearch** | Полнотекстовый поиск товаров |
| **RabbitMQ** | Асинхронное взаимодействие сервисов |
| **Prometheus** | Сбор метрик |
| **Grafana** | Визуализация дашбордов |
| **MailHog** | Тестирование email (порт 8025) |

## Tech Stack

- **Python 3.12** — асинхронное программирование
- **FastAPI** — high-performance web framework
- **SQLAlchemy 2.0** — async ORM
- **Pydantic v2** — валидация данных
- **Docker & Docker Compose** — контейнеризация
- **Nginx** — API Gateway
- **RabbitMQ** — message broker
- **Elasticsearch** — search engine
- **Redis** — in-memory cache
- **Prometheus + Grafana** — мониторинг

## Быстрый старт

### Docker

```bash
# Сборка и запуск всех сервисов
docker-compose up --build

# Запуск в фоне
docker-compose up -d

# Просмотр логов
docker-compose logs -f

# Остановка
docker-compose down

# Остановка с удалением volumes
docker-compose down -v
```

### Локальная разработка

```bash
# Для каждого сервиса
cd auth-service
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

## Доступ к сервисам

| Сервис | URL |
|--------|-----|
| API Gateway | http://localhost:8000 |
| Auth Docs | http://localhost:8000/api/v1/auth/docs |
| Product Docs | http://localhost:8000/api/v1/products/docs |
| Order Docs | http://localhost:8000/api/v1/orders/docs |
| Payment Docs | http://localhost:8000/api/v1/payments/docs |
| RabbitMQ UI | http://localhost:15672 (guest/guest) |
| Grafana | http://localhost:3000 (admin/admin) |
| Prometheus | http://localhost:9090 |
| MailHog UI | http://localhost:8025 |
| Elasticsearch | http://localhost:9200 |

## API Endpoints

### Authentication

```bash
# Регистрация
POST /api/v1/auth/register
{
  "email": "user@example.com",
  "username": "johndoe",
  "password": "securepassword123"
}

# Логин
POST /api/v1/auth/login
{
  "email": "user@example.com",
  "password": "securepassword123"
}

# Refresh token
POST /api/v1/auth/refresh
{
  "refresh_token": "eyJ..."
}

# Logout (инвалидирует token)
POST /api/v1/auth/logout
```

### Products

```bash
# Список товаров (пагинация + поиск)
GET /api/v1/products/?page=1&per_page=20&search=laptop

# Получить товар
GET /api/v1/products/1

# Создать товар (требует авторизации)
POST /api/v1/products/
{
  "name": "Laptop Pro",
  "description": "High-performance laptop",
  "price": 999.99,
  "sku": "LAPTOP-PRO-001",
  "stock_quantity": 50
}

# Обновить товар
PATCH /api/v1/products/1
{
  "price": 899.99
}

# Удалить товар
DELETE /api/v1/products/1
```

### Orders

```bash
# Создать заказ (с reserve stock)
POST /api/v1/orders/
{
  "items": [
    {"product_id": 1, "quantity": 2}
  ],
  "shipping_address": "123 Main St, City"
}

# Получить заказ
GET /api/v1/orders/1

# Обновить статус
PATCH /api/v1/orders/1/status?status=confirmed
```

### Payments

```bash
# Создать платеж (Stripe интеграция)
POST /api/v1/payments/
{
  "order_id": 1,
  "amount": 1999.98,
  "payment_method": "card"
}

# Webhook для Stripe
POST /api/v1/payments/webhook
```

## Тесты

```bash
pytest tests/ -v
pytest --cov=app --cov-report=html
```

## CI/CD

GitHub Actions workflows:
- `.github/workflows/ci.yml` — lint, test, build, security scan
- `.github/workflows/deploy.yml` — deploy to production

## Структура проекта

```
проект/
├── docker-compose.yml          # Оркестрация инфраструктуры
├── api-gateway/
│   ├── Dockerfile
│   └── nginx.conf              # Reverse proxy, rate limiting
├── auth-service/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── alembic/                # Миграции БД
│   └── app/
│       ├── main.py             # FastAPI app
│       ├── api/auth.py         # Auth endpoints
│       ├── core/
│       │   ├── config.py       # Settings
│       │   ├── database.py    # Async SQLAlchemy
│       │   ├── security.py     # JWT, password hashing
│       │   ├── auth_deps.py   # Dependencies
│       │   └── redis.py       # Token blacklist
│       ├── models/user.py
│       ├── schemas/auth.py
│       └── services/auth.py
├── product-service/
│   ├── Dockerfile
│   └── app/
│       ├── api/products.py     # Product endpoints + ES search
│       ├── core/
│       │   ├── elasticsearch.py  # Elasticsearch integration
│       │   └── auth_deps.py
│       ├── models/product.py
│       └── schemas/product.py
├── order-service/
│   ├── Dockerfile
│   └── app/
│       ├── api/orders.py       # Order endpoints
│       ├── core/
│       │   ├── event_publisher.py  # RabbitMQ publisher
│       │   └── auth_deps.py
│       ├── models/order.py
│       └── schemas/order.py
├── payment-service/
│   ├── Dockerfile
│   └── app/
│       ├── api/payments.py     # Stripe integration
│       ├── core/event_publisher.py
│       ├── models/payment.py
│       └── schemas/payment.py
├── notification-service/
│   ├── Dockerfile
│   └── app/
│       ├── main.py             # Worker entry point
│       ├── workers/notification.py  # RabbitMQ consumer + DLQ
│       └── core/config.py
├── infrastructure/
│   ├── prometheus/prometheus.yml
│   └── grafana/
│       ├── provisioning/datasources/
│       ├── provisioning/dashboards/
│       └── dashboards/
├── tests/                      # Unit тесты
│   ├── conftest.py
│   ├── test_auth.py
│   ├── test_orders.py
│   ├── test_products.py
│   ├── test_payments.py
│   └── test_validation.py
└── .github/workflows/
    ├── ci.yml
    └── deploy.yml
```

## Реализованные фичи

- [x] API Gateway с rate limiting (30r/s, burst=50)
- [x] JWT Authentication с access/refresh tokens
- [x] Token blacklist в Redis (logout работает)
- [x] Product CRUD с пагинацией
- [x] Elasticsearch полнотекстовый поиск
- [x] Order management со stock reservation
- [x] Race condition protection с rollback
- [x] Payment Service со Stripe интеграцией
- [x] Idempotency keys для Stripe
- [x] Notification Service с RabbitMQ
- [x] Dead Letter Queue для failed messages
- [x] Exponential backoff для RabbitMQ
- [x] Graceful shutdown всех сервисов
- [x] Connection pooling для БД (pool_size=10)
- [x] Health checks для всех сервисов
- [x] Prometheus metrics (/metrics endpoint)
- [x] Grafana dashboards
- [x] Unit тесты
- [x] CI/CD pipeline
- [x] Alembic migrations
- [x] Decimal для денежных сумм (точность)
- [x] Tracing middleware (X-Request-ID)