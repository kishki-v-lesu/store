# Contributing

## Как работать с проектом

### 1. Клонирование и запуск

```bash
git clone <repo>
cd проект
docker-compose up --build
```

### 2. Разработка

```bash
# Python linting
ruff check .

# Python formatting
ruff format .

# Запуск тестов
pytest tests/ -v
```

### 3. Структура коммитов

```
feat: новая фича
fix: исправление бага
refactor: рефакторинг
docs: документация
test: тесты
chore: обновление зависимостей
```

### 4. Pull Request

1. Fork репозиторий
2. Создайте feature branch (`git checkout -b feature/my-feature`)
3. Commit изменения (`git commit -m 'feat: add new feature'`)
4. Push в branch (`git push origin feature/my-feature`)
5. Open Pull Request

### 5. Code Style

Проект использует:
- **Ruff** для линтинга и форматирования
- Тип аннотации для всех функций
- Русские комментарии в коде

### 6. Тестирование

```bash
# Все тесты
pytest tests/ -v

# С покрытием
pytest --cov=app --cov-report=html

# Конкретный файл
pytest tests/test_auth.py -v
```

### 7. Запуск отдельного сервиса

```bash
cd auth-service
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8001
```

### 8. Миграции БД

```bash
cd auth-service
alembic revision --autogenerate -m "description"
alembic upgrade head
```

## Сервисы для разработки

| Сервис | Порт | Описание |
|--------|------|----------|
| Auth | 8001 | `uvicorn app.main:app --port 8001` |
| Product | 8002 | `uvicorn app.main:app --port 8002` |
| Order | 8003 | `uvicorn app.main:app --port 8003` |
| Payment | 8004 | `uvicorn app.main:app --port 8004` |

## Полезные команды

```bash
# Логи контейнера
docker-compose logs -f auth-service

# Перезапуск сервиса
docker-compose restart auth-service

# Очистка и пересборка
docker-compose down -v
docker-compose up --build

# Зайти в контейнер
docker exec -it auth-service bash

# PostgreSQL клиент
docker exec -it auth-db psql -U postgres -d auth_db
```

## Dependencies

Обновление requirements:
```bash
pip list --outdated
pip install --upgrade package-name
pip freeze > requirements.txt
```

## Troubleshooting

### Сервис не запускается
```bash
docker-compose down
docker-compose up --build
```

### Проблемы с БД
```bash
docker-compose exec auth-db psql -U postgres -d auth_db
# \dt - список таблиц
# \d table_name - структура таблицы
```

### Очистка всех данных
```bash
docker-compose down -v
docker-compose up --build
```