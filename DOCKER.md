# Xray Telegram Bot - Docker Quick Start

Этот файл содержит инструкции для быстрого деплоя через Docker.

## Предварительные требования

1. **Docker** - [Установить Docker](https://docs.docker.com/get-docker/)
2. **Docker Compose** - обычно идет вместе с Docker Desktop
3. **Telegram Bot Token** - получите у [@BotFather](https://t.me/BotFather)
4. **Ваш Telegram ID** - узнайте через [@getmyid_bot](https://t.me/getmyid_bot)

## Быстрый старт

### 1. Клонируйте репозиторий

```bash
git clone <your-repo-url>
cd tgbot
```

### 2. Настройте переменные окружения

Создайте файл `.env` на основе `.env.example`:

```bash
cp .env.example .env
```

Отредактируйте `.env` и укажите свои данные:

```env
BOT_TOKEN=1234567890:ABCdefGHIjklMNOpqrsTUVwxyz
ADMIN_ID=123456789
DOMAIN=vpn.example.com
PUBLIC_KEY=your_reality_public_key
SHORT_ID=your_short_id
```

### 3. Запустите деплой

**Linux/Mac:**
```bash
chmod +x deploy.sh
./deploy.sh
```

**Windows:**
```cmd
deploy.bat
```

**Или вручную:**
```bash
docker compose up -d --build
```

## Управление

### Просмотр логов
```bash
docker compose logs -f
```

### Остановка
```bash
docker compose down
```

### Перезапуск
```bash
docker compose restart
```

### Обновление после изменения кода
```bash
git pull
docker compose up -d --build
```

### Проверка статуса
```bash
docker compose ps
```

## Структура volumes

- `./xray-config` - конфигурация Xray (персистентная)
- `./data` - данные бота (персистентная)
- `./temp_users.json` - временные пользователи (персистентная)

## Troubleshooting

### Бот не запускается

1. Проверьте логи:
```bash
docker compose logs xray-bot
```

2. Убедитесь, что `.env` файл заполнен корректно

3. Проверьте, что порт 443 не занят:
```bash
# Linux/Mac
sudo lsof -i :443

# Windows
netstat -ano | findstr :443
```

### Ошибка "permission denied"

На Linux может потребоваться запуск с sudo:
```bash
sudo docker compose up -d
```

### Контейнер постоянно перезапускается

Проверьте переменные окружения в `.env` - скорее всего не указан `BOT_TOKEN` или `ADMIN_ID`.

## Безопасность

- Никогда не коммитьте `.env` файл в git
- Используйте сильные пароли и токены
- Регулярно обновляйте Docker образы
- Ограничьте доступ к серверу через firewall

## Backup

### Создание backup

```bash
# Backup конфигурации Xray
docker compose exec xray-bot cat /usr/local/etc/xray/config.json > backup_config.json

# Backup временных пользователей
cp temp_users.json backup_temp_users.json
```

### Восстановление из backup

```bash
# Восстановление конфигурации
docker compose cp backup_config.json xray-bot:/usr/local/etc/xray/config.json

# Восстановление временных пользователей
cp backup_temp_users.json temp_users.json

# Перезапуск
docker compose restart
```

## Мониторинг

### Использование ресурсов

```bash
docker stats xray-telegram-bot
```

### Healthcheck

```bash
docker inspect --format='{{.State.Health.Status}}' xray-telegram-bot
```

## Дополнительная информация

Полная документация доступна в [README.md](README.md)
