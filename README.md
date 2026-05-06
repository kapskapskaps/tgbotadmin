# Xray Telegram Bot

Telegram бот для управления Xray VPN сервером с поддержкой VLESS-Reality-xHTTP протокола.

## Возможности

- 📊 Мониторинг системы (CPU, RAM, диск)
- ➕ Добавление пользователей (постоянных и временных)
- 🔑 Генерация VLESS-ключей
- 🗑️ Удаление пользователей
- 📝 Просмотр логов Xray
- ⚠️ Отслеживание ошибок и блокировок
- 📤 Экспорт конфигурации Xray
- 🔄 Перезапуск Xray сервера
- ℹ️ Информация о боте и сервере
- 🖥️ **Режим терминала** - удаленное выполнение Bash-команд
- 🔒 Защита от несанкционированного доступа (только для администратора)
- 🐳 Деплой одной кнопкой через Docker

## Быстрый старт (Docker) 🚀

### Требования

- Docker и Docker Compose
- Telegram Bot Token (получите у [@BotFather](https://t.me/BotFather))
- Ваш Telegram ID (узнайте через [@getmyid_bot](https://t.me/getmyid_bot))

### Деплой одной командой

**Linux/Mac:**
```bash
chmod +x deploy.sh
./deploy.sh
```

Скрипт автоматически:
1. Проверит наличие Docker
2. Создаст `.env` файл из примера (если его нет)
3. Создаст необходимые директории
4. Соберет Docker образ
5. Запустит контейнеры
6. Покажет статус и полезные команды

### Настройка

После первого запуска отредактируйте `.env` файл:

```env
BOT_TOKEN=your_bot_token_from_botfather
ADMIN_ID=your_telegram_id
DOMAIN=your_domain.com
PUBLIC_KEY=your_reality_public_key
SHORT_ID=your_short_id
```

Затем перезапустите:
```bash
docker compose restart
```

### Управление контейнерами

```bash
# Просмотр логов
docker compose logs -f

# Остановка
docker compose down

# Перезапуск
docker compose restart

# Статус
docker compose ps

# Обновление после изменения кода
./update.sh  # Linux/Mac
```

Подробная документация по Docker: [DOCKER.md](DOCKER.md)

---

## Установка без Docker (классический способ)

1. Клонируйте репозиторий:
```bash
git clone https://github.com/kapskapskaps/tgbotadmin.git
cd tgbotadmin
```

2. Создайте виртуальное окружение:
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# или
venv\Scripts\activate  # Windows
```

3. Установите зависимости:
```bash
pip install -r requirements.txt
```

4. Создайте файл `.env` на основе `.env.example`:
```bash
cp .env.example .env
```

5. Заполните `.env` своими данными:
```env
BOT_TOKEN=your_bot_token_from_botfather
ADMIN_ID=your_telegram_id
XRAY_CONFIG=/usr/local/etc/xray/config.json
DOMAIN=your_domain.com
PUBLIC_KEY=your_reality_public_key
SHORT_ID=your_short_id
```

### Как получить необходимые данные:

- **BOT_TOKEN**: Создайте бота через [@BotFather](https://t.me/BotFather)
- **ADMIN_ID**: Узнайте свой ID через [@getmyid_bot](https://t.me/getmyid_bot)
- **PUBLIC_KEY**: Из конфигурации Xray Reality
- **SHORT_ID**: Из конфигурации Xray Reality

## Запуск

```bash
python main.py
```

### Запуск как systemd сервис (рекомендуется для Linux)

1. Скопируйте файл службы:
```bash
sudo cp xray-bot.service /etc/systemd/system/
```

2. Отредактируйте пути в файле службы под вашу систему:
```bash
sudo nano /etc/systemd/system/xray-bot.service
```

3. Запустите сервис:
```bash
sudo systemctl daemon-reload
sudo systemctl enable xray-bot
sudo systemctl start xray-bot
```

4. Проверьте статус:
```bash
sudo systemctl status xray-bot
```

5. Просмотр логов:
```bash
sudo journalctl -u xray-bot -f
```

6. Перезапуск после обновления кода:
```bash
cd /root/tgbotadmin
git pull
sudo systemctl restart xray-bot
```

## Команды бота

| Команда | Описание | Пример |
|---------|----------|--------|
| `/help` | Показать список команд | `/help` |
| `/stats` | Статистика системы | `/stats` |
| `/add <email>` | Добавить постоянного пользователя | `/add brother` |
| `/addtemp <email> <hours>` | Добавить временного пользователя | `/addtemp guest 24` |
| `/key <email>` | Получить VLESS-ключ | `/key maman` |
| `/del <email>` | Удалить пользователя | `/del doshik` |
| `/logs [15\|30\|60]` | Логи за N минут | `/logs 30` |
| `/errors` | Ошибки за сегодня | `/errors` |
| `/ping` | Проверить доступность сервера | `/ping` |
| `/export` | Экспорт конфигурации Xray | `/export` |
| `/restart` | Перезапуск Xray сервера | `/restart` |
| `/info` | Информация о боте и сервере | `/info` |

### Режим терминала 🖥️

Бот поддерживает два режима работы:

- **💬 Режим чата** (по умолчанию) - работают все команды бота
- **🖥️ Режим терминала** - любой текст выполняется как Bash-команда на сервере

**Переключение режимов:**
1. Нажми кнопку **"🖥 Режим терминала"** внизу экрана (Reply-кнопка)
2. Теперь любой текст будет выполняться как команда
3. Для возврата нажми **"💬 Режим чата"**

**Примеры команд в режиме терминала:**
```bash
ls -la
df -h
systemctl status xray
journalctl -u xray --since "10 min ago"
ps aux | grep python
```

**Безопасность:**
- Только администратор может использовать режим терминала
- Таймаут выполнения: 30 секунд
- Вывод ограничен 4000 символами

### Новые команды

- **`/addtemp <email> <hours>`** - Добавляет временного пользователя, который автоматически удалится через указанное количество часов
- **`/ping`** - Проверяет доступность сервера (DNS резолв, TCP подключение к порту 443)
- **`/export`** - Экспортирует текущую конфигурацию Xray в JSON файл и отправляет его в чат
- **`/restart`** - Перезапускает Xray сервер (использует `systemctl restart xray`)
- **`/info`** - Показывает информацию о боте, версии Python, uptime сервера и статус Xray

## Особенности работы с пользователями

- При добавлении нового пользователя автоматически устанавливается параметр `flow: "xtls-rprx-vision"` для поддержки VLESS-Reality-xHTTP
- Все новые пользователи получают уникальный UUID
- **Временные пользователи** (`/addtemp`) автоматически удаляются через указанное количество часов
- Бот проверяет временных пользователей каждые 10 минут и удаляет истекших

## Безопасность

- Бот отвечает только администратору (указанному в `ADMIN_ID`)
- Не храните `.env` файл в публичных репозиториях
- Используйте права доступа для конфигурационных файлов Xray
- `.bat` файлы для Windows исключены из репозитория (только для локальной разработки)

## Структура проекта

```
tgbotadmin/
├── main.py                 # Основной файл бота
├── requirements.txt        # Зависимости Python
├── .env                    # Переменные окружения (не в git)
├── .env.example            # Пример конфигурации
├── .env.docker             # Пример для Docker
├── Dockerfile              # Docker образ
├── docker-compose.yml      # Docker Compose конфигурация
├── .dockerignore           # Исключения для Docker
├── deploy.sh               # Скрипт деплоя (Linux/Mac)
├── update.sh               # Скрипт обновления (Linux/Mac)
├── xray-bot.service        # Systemd сервис
├── .gitignore              # Игнорируемые файлы
├── DOCKER.md               # Подробная документация по Docker
├── DOCKER_QUICKSTART.md    # Быстрый старт с Docker
└── README.md               # Документация
```

## Docker vs Классическая установка

| Характеристика | Docker | Классическая |
|----------------|--------|--------------|
| Простота установки | ✅ Одна команда | ⚠️ Несколько шагов |
| Изоляция | ✅ Полная | ❌ Нет |
| Портативность | ✅ Работает везде | ⚠️ Зависит от ОС |
| Обновление | ✅ `./update.sh` | ⚠️ `git pull` + restart |
| Откат версии | ✅ Простой | ⚠️ Сложный |
| Ресурсы | ⚠️ Немного больше | ✅ Минимальные |
| Конфликты зависимостей | ✅ Нет | ⚠️ Возможны |

**Рекомендация:** Используйте Docker для продакшена, классическую установку для разработки.

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

### Пересоздать контейнеры с нуля
```bash
docker compose down -v
docker compose up -d --build
```

### Проблемы с Markdown в сообщениях бота
Бот использует HTML parse mode для всех сообщений, чтобы избежать проблем с экранированием специальных символов Markdown.

## Последние обновления

- ✅ Добавлен режим терминала для удаленного выполнения Bash-команд
- ✅ Добавлена Reply-кнопка для переключения между режимами
- ✅ Добавлена поддержка Docker с деплоем одной командой
- ✅ Добавлены команды `/export`, `/restart`, `/info`
- ✅ Исправлены проблемы с парсингом Markdown
- ✅ Добавлен параметр `flow` для новых пользователей
- ✅ Улучшена обработка перезапуска Xray (restart вместо reload)

## Лицензия

MIT
