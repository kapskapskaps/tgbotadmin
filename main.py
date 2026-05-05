import asyncio
import json
import subprocess
import uuid
import psutil
import os
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command, CommandObject
from aiogram.types import FSInputFile
from dotenv import load_dotenv

# Загрузка переменных окружения
load_dotenv()

# --- НАСТРОЙКИ ---
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID"))
XRAY_CONFIG = os.getenv("XRAY_CONFIG", "/usr/local/etc/xray/config.json")
DOMAIN = os.getenv("DOMAIN")
PUBLIC_KEY = os.getenv("PUBLIC_KEY")
SHORT_ID = os.getenv("SHORT_ID")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Фильтр для защиты бота (отвечает только тебе)
def is_admin(message: types.Message) -> bool:
    return message.from_user.id == ADMIN_ID

# --- КОМАНДА HELP ---
@dp.message(Command("help"), F.func(is_admin))
async def cmd_help(message: types.Message):
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
        
    # Проверяем, нет ли уже такого
    clients = config['inbounds'][0]['settings']['clients']
    if any(c['email'] == email for c in clients):
        return await message.answer("Пользователь с таким email уже есть!")
        
    clients.append({"email": email, "id": new_uuid})
    
    with open(XRAY_CONFIG, 'w') as f:
        json.dump(config, f, indent=2)
        
    subprocess.run(["systemctl", "restart", "xray"])
    await message.answer(f"✅ Пользователь {email} добавлен! Сервер перезапущен.\nИспользуй /key {email} для получения ссылки.")

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
        
    subprocess.run(["systemctl", "restart", "xray"])
    await message.answer(f"🗑 Пользователь {email} удален. Сервер перезапущен.")

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
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())