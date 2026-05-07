# 🚀 Xray Telegram Bot - Готов к деплою!

## ✅ Что сделано

Проект полностью готов к деплою одной кнопкой через Docker!

### Добавленные файлы:

#### Docker инфраструктура
- **Dockerfile** - образ с Python 3.11 + Xray
- **docker-compose.yml** - оркестрация с healthcheck и volumes
- **.dockerignore** - оптимизация сборки образа

#### Скрипты деплоя
- **deploy.sh** - автоматический деплой (Linux/Mac)
- **deploy.bat** - автоматический деплой (Windows)
- **update.sh** - обновление бота (Linux/Mac)
- **update.bat** - обновление бота (Windows)

#### Документация
- **DOCKER.md** - подробная документация по Docker
- **DOCKER_QUICKSTART.md** - быстрый старт
- **README.md** - обновлен с Docker секцией
- **.env.docker** - пример конфигурации для Docker

## 🎯 Как использовать

### Вариант 1: Деплой одной командой (рекомендуется)

**Windows:**
```cmd
deploy.bat
```

**Linux/Mac:**
```bash
chmod +x deploy.sh
./deploy.sh
```

### Вариант 2: Вручную через Docker Compose

```bash
# 1. Создайте .env файл
cp .env.example .env
# Отредактируйте .env

# 2. Запустите
docker compose up -d --build

# 3. Проверьте логи
docker compose logs -f
```

## 📋 Что делает deploy скрипт

1. ✅ Проверяет наличие Docker
2. ✅ Создает `.env` из примера (если нет)
3. ✅ Создает необходимые директории
4. ✅ Останавливает старые контейнеры
5. ✅ Собирает Docker образ
6. ✅ Запускает контейнеры
7. ✅ Показывает статус и полезные команды

## 🔧 Управление

```bash
# Логи
docker compose logs -f

# Остановка
docker compose down

# Перезапуск
docker compose restart

# Обновление
./update.sh  # или update.bat на Windows
```

## 📦 Персистентные данные

Все данные сохраняются между перезапусками:
- `./xray-config/` - конфигурация Xray
- `./data/` - данные бота
- `./temp_users.json` - временные пользователи

## 🔐 Настройка .env

Перед первым запуском отредактируйте `.env`:

```env
BOT_TOKEN=your_bot_token_from_botfather
ADMIN_ID=your_telegram_id
DOMAIN=your_domain.com
PUBLIC_KEY=your_reality_public_key
SHORT_ID=your_short_id
```

### Где взять данные:
- **BOT_TOKEN**: [@BotFather](https://t.me/BotFather)
- **ADMIN_ID**: [@getmyid_bot](https://t.me/getmyid_bot)
- **PUBLIC_KEY, SHORT_ID**: из конфигурации Xray Reality

## 🎉 Преимущества Docker версии

| Характеристика | Docker | Классическая установка |
|----------------|--------|------------------------|
| Установка | ✅ 1 команда | ⚠️ 5+ шагов |
| Изоляция | ✅ Полная | ❌ Нет |
| Портативность | ✅ Любая ОС | ⚠️ Зависит от ОС |
| Обновление | ✅ `./update.sh` | ⚠️ Несколько команд |
| Откат | ✅ Простой | ⚠️ Сложный |
| Конфликты | ✅ Нет | ⚠️ Возможны |

## 📚 Документация

- [README.md](README.md) - основная документация
- [DOCKER.md](DOCKER.md) - подробно про Docker
- [DOCKER_QUICKSTART.md](DOCKER_QUICKSTART.md) - быстрый старт

## 🐛 Troubleshooting

### Контейнер не запускается
```bash
docker compose logs xray-bot
```

### Порт 443 занят
```bash
# Linux/Mac
sudo lsof -i :443

# Windows
netstat -ano | findstr :443
```

### Пересоздать с нуля
```bash
docker compose down -v
docker compose up -d --build
```

## 📝 Коммит

Все изменения закоммичены:
```
commit 9135c6b
Add Docker support for one-click deployment
```

Готово к push в репозиторий! 🚀

---

**Следующий шаг:** `git push` для отправки в удаленный репозиторий
