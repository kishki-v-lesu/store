#!/bin/bash

echo " Пересобираем шлюз..."
docker build -t ecommerce-api-gateway ./api-gateway

echo ""
echo "🗑️  Удаляем старый контейнер..."
docker rm -f my-gateway 2>/dev/null || echo "Старого контейнера нет, пропускаем."

echo ""
echo "🚀 Запускаем новый шлюз..."
docker run -d --name my-gateway -p 8000:80 --network ecommerce_backend ecommerce-api-gateway

echo ""
echo "✅ Готово! Документация доступна:"
echo "   http://localhost:8000/auth/docs"
