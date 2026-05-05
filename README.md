# Xray Telegram Bot

Telegram бот для управления Xray VPN сервером с поддержкой VLESS-Reality-xHTTP протокола.

## Возможности

- 📊 Мониторинг системы (CPU, RAM, диск)
- ➕ Добавление пользователей
- 🔑 Генерация VLESS-ключей
- 🗑️ Удаление пользователей
- 📝 Просмотр логов Xray
- ⚠️ Отслеживание ошибок и блокировок
- 🔒 Защита от несанкционированного доступа (только для администратора)

## Требования

- Python 3.8+
- Xray-core установленный на сервере
- Systemd для управления Xray

## Установка

1. Клонируйте репозиторий:
```bash
git clone <your-repo-url>
cd tgbot
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

### Запуск как systemd сервис (рекомендуется)

1. Скопируйте файл службы:
```bash
sudo cp xray-bot.service /etc/systemd/system/
```

2. Запустите сервис:
```bash
sudo systemctl daemon-reload
sudo systemctl enable xray-bot
sudo systemctl start xray-bot
```

3. Проверьте статус:
```bash
sudo systemctl status xray-bot
```

4. Просмотр логов:
```bash
sudo journalctl -u xray-bot -f
```

5. Перезапуск после обновления кода:
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
| `/add <email>` | Добавить пользователя | `/add brother` |
| `/key <email>` | Получить VLESS-ключ | `/key maman` |
| `/del <email>` | Удалить пользователя | `/del doshik` |
| `/logs [15\|30\|60]` | Логи за N минут | `/logs 30` |
| `/errors` | Ошибки за сегодня | `/errors` |

## Безопасность

- Бот отвечает только администратору (указанному в `ADMIN_ID`)
- Не храните `.env` файл в публичных репозиториях
- Используйте права доступа для конфигурационных файлов Xray

## Структура проекта

```
tgbot/
├── main.py              # Основной файл бота
├── .env                 # Переменные окружения (не в git)
├── .env.example         # Пример конфигурации
├── .gitignore          # Игнорируемые файлы
├── requirements.txt     # Зависимости Python
└── README.md           # Документация
```

## Лицензия

MIT
