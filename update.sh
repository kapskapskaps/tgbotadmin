#!/bin/bash

# Скрипт для обновления бота

set -e

echo "🔄 Обновление Xray Telegram Bot..."

# Определение команды docker compose
if docker compose version &> /dev/null; then
    DOCKER_COMPOSE="docker compose"
else
    DOCKER_COMPOSE="docker-compose"
fi

# Получение последних изменений
echo "📥 Получаю последние изменения из git..."
git pull

# Пересборка и перезапуск
echo "🔨 Пересобираю образ..."
$DOCKER_COMPOSE build

echo "🔄 Перезапускаю контейнеры..."
$DOCKER_COMPOSE up -d

echo "✅ Обновление завершено!"
echo ""
echo "📊 Статус:"
$DOCKER_COMPOSE ps

echo ""
echo "📝 Логи:"
$DOCKER_COMPOSE logs --tail=20
