#!/bin/bash

# Скрипт для быстрого деплоя Xray Telegram Bot

set -e

echo "🚀 Начинаю деплой Xray Telegram Bot..."

# Проверка наличия .env файла
if [ ! -f .env ]; then
    echo "⚠️  Файл .env не найден!"
    echo "📝 Создаю из .env.example..."
    cp .env.example .env
    echo ""
    echo "❗ ВАЖНО: Отредактируйте файл .env перед запуском!"
    echo "   Необходимо указать:"
    echo "   - BOT_TOKEN (получите у @BotFather)"
    echo "   - ADMIN_ID (ваш Telegram ID)"
    echo "   - DOMAIN (ваш домен)"
    echo "   - PUBLIC_KEY (Reality public key)"
    echo "   - SHORT_ID (Reality short ID)"
    echo ""
    read -p "Нажмите Enter после редактирования .env файла..."
fi

# Создание необходимых директорий
echo "📁 Создаю директории..."
mkdir -p xray-config data

# Проверка наличия Docker
if ! command -v docker &> /dev/null; then
    echo "❌ Docker не установлен!"
    echo "Установите Docker: https://docs.docker.com/get-docker/"
    exit 1
fi

# Проверка наличия Docker Compose
if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    echo "❌ Docker Compose не установлен!"
    echo "Установите Docker Compose: https://docs.docker.com/compose/install/"
    exit 1
fi

# Определение команды docker compose
if docker compose version &> /dev/null; then
    DOCKER_COMPOSE="docker compose"
else
    DOCKER_COMPOSE="docker-compose"
fi

# Остановка старых контейнеров (если есть)
echo "🛑 Останавливаю старые контейнеры..."
$DOCKER_COMPOSE down 2>/dev/null || true

# Сборка образа
echo "🔨 Собираю Docker образ..."
$DOCKER_COMPOSE build

# Запуск контейнеров
echo "▶️  Запускаю контейнеры..."
$DOCKER_COMPOSE up -d

# Проверка статуса
echo ""
echo "✅ Деплой завершен!"
echo ""
echo "📊 Статус контейнеров:"
$DOCKER_COMPOSE ps

echo ""
echo "📝 Полезные команды:"
echo "   Логи:           $DOCKER_COMPOSE logs -f"
echo "   Остановить:     $DOCKER_COMPOSE down"
echo "   Перезапустить:  $DOCKER_COMPOSE restart"
echo "   Статус:         $DOCKER_COMPOSE ps"
echo ""
echo "🎉 Бот запущен и готов к работе!"
