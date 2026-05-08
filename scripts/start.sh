#!/bin/bash
echo "=========================================="
echo "  Запуск E-Commerce платформы..."
echo "=========================================="
echo ""

# Проверяем, какая команда доступна (docker compose или docker-compose)
if docker compose version &> /dev/null; then
    DOCKER_CMD="docker compose"
elif docker-compose version &> /dev/null; then
    DOCKER_CMD="docker-compose"
else
    echo "❌ Ошибка: Docker Compose не установлен!"
    echo "Установите Docker Compose и попробуйте снова."
    exit 1
fi

echo "✅ Найдено: $DOCKER_CMD"

if ! docker info &> /dev/null; then
    echo "❌ Ошибка: Docker не запущен!"
    echo "Запустите Docker и попробуйте снова."
    exit 1
fi

echo "🔨 Сборка образов..."
$DOCKER_CMD build

echo ""
echo "🚀 Запуск сервисов..."
$DOCKER_CMD -p ecommerce up -d

echo ""
echo "=========================================="
echo "  Сервисы запущены!"
echo "=========================================="
echo ""
echo "📋 Доступные сервисы:"
echo "  API Gateway:       http://localhost:8000"
echo "  Auth Docs:         http://localhost:8000/api/v1/auth/docs"
echo "  Product Docs:      http://localhost:8000/api/v1/products/docs"
echo "  Order Docs:        http://localhost:8000/api/v1/orders/docs"
echo "  Payment Docs:      http://localhost:8000/api/v1/payments/docs"
echo "  RabbitMQ:          http://localhost:15672"
echo "  MailHog:           http://localhost:8025"
echo ""
echo "📊 Статус контейнеров:"
$DOCKER_CMD ps

echo ""
echo "Нажмите любую клавишу для выхода..."
read -n 1
