import asyncio
import json
import subprocess
import uuid
import psutil
import os
import logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command, CommandObject
from aiogram.types import FSInputFile
from dotenv import load_dotenv

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Загрузка переменных окружения
load_dotenv()
logger.info("Переменные окружения загружены")

# --- НАСТРОЙКИ ---
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = os.getenv("ADMIN_ID")
XRAY_CONFIG = os.getenv("XRAY_CONFIG", "/usr/local/etc/xray/config.json")
DOMAIN = os.getenv("DOMAIN")
PUBLIC_KEY = os.getenv("PUBLIC_KEY")
SHORT_ID = os.getenv("SHORT_ID")

# Проверка обязательных переменных
if not BOT_TOKEN:
    logger.error("❌ BOT_TOKEN не найден в .env файле!")
    exit(1)
if not ADMIN_ID:
    logger.error("❌ ADMIN_ID не найден в .env файле!")
    exit(1)

try:
    ADMIN_ID = int(ADMIN_ID)
    logger.info(f"✅ ADMIN_ID установлен: {ADMIN_ID}")
except ValueError:
    logger.error("❌ ADMIN_ID должен быть числом!")
    exit(1)

if not DOMAIN:
    logger.warning("⚠️ DOMAIN не установлен - команда /key может не работать")
if not PUBLIC_KEY:
    logger.warning("⚠️ PUBLIC_KEY не установлен - команда /key может не работать")
if not SHORT_ID:
    logger.warning("⚠️ SHORT_ID не установлен - команда /key может не работать")

logger.info(f"✅ Конфигурация Xray: {XRAY_CONFIG}")
logger.info(f"✅ Домен: {DOMAIN}")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
logger.info("✅ Bot и Dispatcher инициализированы")

# Фильтр для защиты бота (отвечает только тебе)
def is_admin(message: types.Message) -> bool:
    user_id = message.from_user.id
    is_allowed = user_id == ADMIN_ID
    logger.info(f"Проверка доступа: user_id={user_id}, admin_id={ADMIN_ID}, разрешено={is_allowed}")
    if not is_allowed:
        logger.warning(f"⚠️ Отклонено сообщение от неавторизованного пользователя {user_id}")
    return is_allowed

# Обработчик для всех сообщений от неавторизованных пользователей
@dp.message(~F.func(is_admin))
async def unauthorized_handler(message: types.Message):
    logger.warning(f"❌ Неавторизованная попытка доступа от {message.from_user.id} (@{message.from_user.username})")
    await message.answer("⛔️ У вас нет доступа к этому боту.")

# --- КОМАНДА START ---
@dp.message(Command("start"), F.func(is_admin))
async def cmd_start(message: types.Message):
    logger.info(f"✅ Команда /start от администратора {message.from_user.id}")
    start_text = (
        f"👋 Привет, {message.from_user.first_name}!\n\n"
        "Я бот для управления Xray VPN сервером.\n\n"
        "🔧 **Мои возможности:**\n"
        "• Мониторинг системы (CPU, RAM, диск)\n"
        "• Управление пользователями VPN\n"
        "• Генерация VLESS-ключей\n"
        "• Просмотр логов и ошибок\n\n"
        "Используй /help для списка всех команд."
    )
    await message.answer(start_text, parse_mode="Markdown")

# --- КОМАНДА HELP ---
@dp.message(Command("help"), F.func(is_admin))
async def cmd_help(message: types.Message):
    logger.info(f"✅ Команда /help от администратора {message.from_user.id}")
    help_text = (
        "🤖 **Доступные команды:**\n\n"
        "/help - Показать это сообщение\n"
        "/stats - Статистика системы (CPU, RAM, диск)\n"
        "/add <email> - Добавить нового пользователя\n"
        "/key <email> - Получить VLESS-ключ пользователя\n"
        "/del <email> - Удалить пользователя\n"
        "/logs [15|30|60] - Логи Xray за N минут (по умолчанию 15)\n"
        "/errors - Ошибки и блокировки за сегодня\n\n"
        "**Примеры:**\n"
        "`/add brother`\n"
        "`/key maman`\n"
        "`/del doshik`\n"
        "`/logs 30`"
    )
    await message.answer(help_text, parse_mode="Markdown")

# --- 1. СТАТИСТИКА СИСТЕМЫ И ДИСКА ---
@dp.message(Command("stats"), F.func(is_admin))
async def cmd_stats(message: types.Message):
    cpu = psutil.cpu_percent(interval=1)
    ram = psutil.virtual_memory()
    disk = psutil.disk_usage('/')
    
    text = (
        f"🖥 **Система (Ryzen 9):**\n"
        f"CPU: {cpu}%\n"
        f"RAM: {ram.percent}% ({ram.used // (1024**2)}MB / {ram.total // (1024**2)}MB)\n\n"
        f"💾 **SSD (Корень):**\n"
        f"Занято: {disk.percent}% ({disk.used // (1024**3)}GB / {disk.total // (1024**3)}GB)"
    )
    await message.answer(text, parse_mode="Markdown")

# --- 2. ДОБАВЛЕНИЕ ПОЛЬЗОВАТЕЛЯ ---
@dp.message(Command("add"), F.func(is_admin))
async def cmd_add(message: types.Message, command: CommandObject):
    if not command.args:
        return await message.answer("Укажи email. Пример: /add brother")

    email = command.args.strip()
    new_uuid = str(uuid.uuid4())

    with open(XRAY_CONFIG, 'r') as f:
        config = json.load(f)

    clients = config['inbounds'][0]['settings']['clients']

    # Проверяем дубликаты без учета регистра
    existing_emails = [c['email'].lower() for c in clients]
    if email.lower() in existing_emails:
        existing_email = next(c['email'] for c in clients if c['email'].lower() == email.lower())
        logger.warning(f"Попытка создать дубликат: {email} (существует: {existing_email})")

        # Находим UUID существующего пользователя
        existing_client = next(c for c in clients if c['email'].lower() == email.lower())
        vless_link = f"vless://{existing_client['id']}@{DOMAIN}:443?type=xhttp&security=reality&pbk={PUBLIC_KEY}&sni=github.com&fp=chrome&sid={SHORT_ID}&spx=%2F#{existing_email}"

        return await message.answer(
            f"❌ Пользователь с таким именем уже существует: **{existing_email}**\n\n"
            f"Xray не различает регистр, поэтому '{email}' и '{existing_email}' - это один и тот же пользователь.\n\n"
            f"🔑 Ключ для {existing_email}:\n\n`{vless_link}`",
            parse_mode="Markdown"
        )

    clients.append({"email": email, "id": new_uuid})

    with open(XRAY_CONFIG, 'w') as f:
        json.dump(config, f, indent=2)

    subprocess.run(["systemctl", "reload", "xray"])
    logger.info(f"✅ Добавлен пользователь: {email} (UUID: {new_uuid})")

    # Генерируем VLESS-ключ для нового пользователя
    vless_link = f"vless://{new_uuid}@{DOMAIN}:443?type=xhttp&security=reality&pbk={PUBLIC_KEY}&sni=github.com&fp=chrome&sid={SHORT_ID}&spx=%2F#{email}"

    await message.answer(
        f"✅ Пользователь **{email}** добавлен! Конфигурация обновлена.\n\n"
        f"🔑 Ключ для {email}:\n\n`{vless_link}`",
        parse_mode="Markdown"
    )

# --- 3. ПРОСМОТР КЛЮЧА ---
@dp.message(Command("key"), F.func(is_admin))
async def cmd_key(message: types.Message, command: CommandObject):
    if not command.args:
        return await message.answer("Укажи email. Пример: /key maman")
        
    email = command.args.strip()
    with open(XRAY_CONFIG, 'r') as f:
        config = json.load(f)
        
    client = next((c for c in config['inbounds'][0]['settings']['clients'] if c['email'] == email), None)
    
    if not client:
        return await message.answer("Пользователь не найден.")
        
    # Генерируем VLESS-Reality-xHTTP ссылку
    vless_link = f"vless://{client['id']}@{DOMAIN}:443?type=xhttp&security=reality&pbk={PUBLIC_KEY}&sni=github.com&fp=chrome&sid={SHORT_ID}&spx=%2F#{email}"
    
    await message.answer(f"🔑 Ключ для {email}:\n\n`{vless_link}`", parse_mode="Markdown")

# --- 4. УДАЛЕНИЕ ПОЛЬЗОВАТЕЛЯ ---
@dp.message(Command("del"), F.func(is_admin))
async def cmd_del(message: types.Message, command: CommandObject):
    if not command.args:
        return await message.answer("Укажи email. Пример: /del doshik")
        
    email = command.args.strip()
    with open(XRAY_CONFIG, 'r') as f:
        config = json.load(f)
        
    clients = config['inbounds'][0]['settings']['clients']
    new_clients = [c for c in clients if c['email'] != email]
    
    if len(clients) == len(new_clients):
        return await message.answer("Пользователь не найден.")
        
    config['inbounds'][0]['settings']['clients'] = new_clients
    
    with open(XRAY_CONFIG, 'w') as f:
        json.dump(config, f, indent=2)

    subprocess.run(["systemctl", "reload", "xray"])
    await message.answer(f"🗑 Пользователь {email} удален. Конфигурация обновлена.")

# --- 5. ПРОСМОТР ЛОГОВ (Отправка файлом) ---
@dp.message(Command("logs"), F.func(is_admin))
async def cmd_logs(message: types.Message, command: CommandObject):
    times = {"15": "15 min ago", "30": "30 min ago", "60": "1 hour ago"}
    time_key = command.args.strip() if command.args else "15"
    
    if time_key not in times:
        return await message.answer("Выбери: 15, 30 или 60")
        
    # Записываем логи во временный файл
    log_file = f"logs_{time_key}m.txt"
    cmd = f"journalctl -u xray --since '{times[time_key]}' --no-pager > {log_file}"
    subprocess.run(cmd, shell=True)
    
    if os.path.getsize(log_file) == 0:
        await message.answer("Логи за это время пусты.")
    else:
        await message.answer_document(FSInputFile(log_file))
    
    os.remove(log_file) # Подчищаем за собой

# --- 6. ОШИБКИ И БЛОКИРОВКИ ---
@dp.message(Command("errors"), F.func(is_admin))
async def cmd_errors(message: types.Message):
    # Ищем warning, error или block в логах за сегодня
    cmd = "journalctl -u xray --since today --no-pager | grep -iE 'warning|error|block' | tail -n 50 > temp_err.txt"
    subprocess.run(cmd, shell=True)
    
    if os.path.getsize("temp_err.txt") == 0:
        await message.answer("Ошибок за сегодня нет! 🎉")
    else:
        await message.answer_document(FSInputFile("temp_err.txt"), caption="Последние 50 ошибок/блокировок за сегодня")
        
    os.remove("temp_err.txt")

async def main():
    logger.info("=" * 50)
    logger.info("🤖 Бот запущен и готов к работе!")
    logger.info(f"👤 Администратор ID: {ADMIN_ID}")
    logger.info(f"📡 Ожидание сообщений от Telegram...")
    logger.info("=" * 50)
    try:
        await dp.start_polling(bot)
    except Exception as e:
        logger.error(f"❌ Ошибка при запуске polling: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(main())