# Xray Telegram Bot - Docker Edition

## Что нового?

Теперь проект можно задеплоить **одной кнопкой** через Docker! 🚀

## Быстрый старт

### Windows
```cmd
deploy.bat
```

### Linux/Mac
```bash
chmod +x deploy.sh
./deploy.sh
```

## Что включено?

- ✅ **Dockerfile** - образ с Python 3.11 и Xray
- ✅ **docker-compose.yml** - оркестрация контейнеров
- ✅ **deploy.sh / deploy.bat** - скрипты для автоматического деплоя
- ✅ **update.sh / update.bat** - скрипты для обновления
- ✅ **Healthcheck** - автоматическая проверка здоровья контейнера
- ✅ **Volumes** - персистентное хранение данных
- ✅ **Логирование** - ротация логов (max 10MB × 3 файла)

## Преимущества Docker-версии

1. **Изоляция** - бот работает в изолированном окружении
2. **Портативность** - работает на любой ОС с Docker
3. **Простота** - один скрипт для деплоя
4. **Безопасность** - нет конфликтов с системными пакетами
5. **Масштабируемость** - легко запустить несколько инстансов

## Структура файлов

```
tgbot/
├── Dockerfile              # Образ контейнера
├── docker-compose.yml      # Конфигурация сервисов
├── .dockerignore          # Исключения для Docker
├── deploy.sh              # Деплой (Linux/Mac)
├── deploy.bat             # Деплой (Windows)
├── update.sh              # Обновление (Linux/Mac)
├── update.bat             # Обновление (Windows)
├── DOCKER.md              # Подробная документация
└── README.md              # Основная документация
```

## Команды

| Действие | Linux/Mac | Windows |
|----------|-----------|---------|
| Деплой | `./deploy.sh` | `deploy.bat` |
| Обновление | `./update.sh` | `update.bat` |
| Логи | `docker compose logs -f` | `docker compose logs -f` |
| Остановка | `docker compose down` | `docker compose down` |
| Перезапуск | `docker compose restart` | `docker compose restart` |

## Volumes (персистентные данные)

- `./xray-config/` - конфигурация Xray
- `./data/` - данные бота
- `./temp_users.json` - временные пользователи

Эти директории сохраняются между перезапусками контейнера.

## Порты

- **443** - Xray VPN сервер

## Переменные окружения

Все настройки берутся из файла `.env`:

```env
BOT_TOKEN=your_token
ADMIN_ID=your_id
DOMAIN=your_domain.com
PUBLIC_KEY=your_key
SHORT_ID=your_short_id
```

## Мониторинг

### Проверка статуса
```bash
docker compose ps
```

### Использование ресурсов
```bash
docker stats xray-telegram-bot
```

### Healthcheck
```bash
docker inspect --format='{{.State.Health.Status}}' xray-telegram-bot
```

## Troubleshooting

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

### Пересоздать контейнер с нуля
```bash
docker compose down -v
docker compose up -d --build
```

## Миграция с классической установки

1. Остановите systemd сервис:
```bash
sudo systemctl stop xray-bot
sudo systemctl disable xray-bot
```

2. Скопируйте данные:
```bash
cp temp_users.json ./
```

3. Запустите Docker версию:
```bash
./deploy.sh
```

## Безопасность

- Контейнер работает с привилегиями для управления Xray
- `.env` файл не попадает в образ (указан в `.dockerignore`)
- Логи ротируются автоматически
- Healthcheck следит за доступностью сервиса

## Дополнительная информация

Подробная документация: [DOCKER.md](DOCKER.md)
Основной README: [README.md](README.md)

---

**Автор:** kapskapskaps  
**Лицензия:** MIT
