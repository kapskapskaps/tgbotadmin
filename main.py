import asyncio
import json
import subprocess
import uuid
import psutil
import os
import logging
import socket
import time
from datetime import datetime, timedelta
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command, CommandObject
from aiogram.types import FSInputFile
from dotenv import load_dotenv
from apscheduler.schedulers.asyncio import AsyncIOScheduler

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
scheduler = AsyncIOScheduler()
logger.info("✅ Bot и Dispatcher инициализированы")

# Файл для хранения временных пользователей
TEMP_USERS_FILE = "temp_users.json"

# Загрузка временных пользователей
def load_temp_users():
    if os.path.exists(TEMP_USERS_FILE):
        try:
            with open(TEMP_USERS_FILE, 'r') as f:
                data = json.load(f)
                logger.info(f"✅ Загружено {len(data)} временных пользователей")
                return data
        except Exception as e:
            logger.error(f"❌ Ошибка при загрузке temp_users.json: {e}")
            return {}
    else:
        logger.info("📝 Файл temp_users.json не найден, создаю новый")
        save_temp_users({})
        return {}

def save_temp_users(temp_users):
    try:
        with open(TEMP_USERS_FILE, 'w') as f:
            json.dump(temp_users, f, indent=2)
        logger.info(f"💾 Сохранено {len(temp_users)} временных пользователей")
    except Exception as e:
        logger.error(f"❌ Ошибка при сохранении temp_users.json: {e}")

temp_users = load_temp_users()

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
        "🤖 <b>Доступные команды:</b>\n\n"
        "/help - Показать это сообщение\n"
        "/stats - Статистика системы (CPU, RAM, диск)\n"
        "/add &lt;email&gt; - Добавить нового пользователя\n"
        "/addtemp &lt;email&gt; &lt;hours&gt; - Добавить временного пользователя\n"
        "/key &lt;email&gt; - Получить VLESS-ключ пользователя\n"
        "/del &lt;email&gt; - Удалить пользователя\n"
        "/logs [15|30|60] - Логи Xray за N минут (по умолчанию 15)\n"
        "/errors - Ошибки и блокировки за сегодня\n"
        "/ping - Проверить доступность сервера\n"
        "/export - Экспортировать backup конфигурации\n"
        "/restart - Перезагрузить Xray\n"
        "/restart_confirm - Подтвердить перезагрузку Xray\n"
        "/info - Информация о системе и версиях\n\n"
        "<b>Примеры:</b>\n"
        "<code>/add brother</code>\n"
        "<code>/addtemp guest 24</code>\n"
        "<code>/key maman</code>\n"
        "<code>/del doshik</code>\n"
        "<code>/logs 30</code>"
    )
    await message.answer(help_text, parse_mode="HTML")

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

    clients.append({"email": email, "id": new_uuid, "flow": "xtls-rprx-vision"})

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

# --- 7. ПРОВЕРКА ДОСТУПНОСТИ СЕРВЕРА ---
@dp.message(Command("ping"), F.func(is_admin))
async def cmd_ping(message: types.Message):
    logger.info(f"✅ Команда /ping от администратора {message.from_user.id}")

    if not DOMAIN:
        return await message.answer("❌ DOMAIN не настроен в .env файле")

    await message.answer(f"🔍 Проверяю доступность {DOMAIN}:443...")

    try:
        # Проверка DNS резолва
        start_dns = time.time()
        ip = socket.gethostbyname(DOMAIN)
        dns_time = (time.time() - start_dns) * 1000

        # Проверка TCP подключения к порту 443
        start_tcp = time.time()
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        result = sock.connect_ex((DOMAIN, 443))
        tcp_time = (time.time() - start_tcp) * 1000
        sock.close()

        if result == 0:
            response = (
                f"✅ **Сервер доступен!**\n\n"
                f"🌐 Домен: {DOMAIN}\n"
                f"📍 IP: {ip}\n"
                f"⚡️ DNS резолв: {dns_time:.0f}ms\n"
                f"⚡️ TCP подключение: {tcp_time:.0f}ms\n"
                f"🔌 Порт 443: Открыт"
            )
        else:
            response = (
                f"❌ **Сервер недоступен!**\n\n"
                f"🌐 Домен: {DOMAIN}\n"
                f"📍 IP: {ip}\n"
                f"⚡️ DNS резолв: {dns_time:.0f}ms\n"
                f"🔌 Порт 443: Закрыт или недоступен"
            )

        await message.answer(response, parse_mode="Markdown")

    except socket.gaierror:
        await message.answer(f"❌ Не удалось разрешить домен {DOMAIN}\n\nПроверьте DNS записи.")
    except socket.timeout:
        await message.answer(f"⏱ Превышено время ожидания при подключении к {DOMAIN}:443")
    except Exception as e:
        logger.error(f"Ошибка при проверке доступности: {e}")
        await message.answer(f"❌ Ошибка при проверке: {str(e)}")

# --- 8. ДОБАВЛЕНИЕ ВРЕМЕННОГО ПОЛЬЗОВАТЕЛЯ ---
@dp.message(Command("addtemp"), F.func(is_admin))
async def cmd_addtemp(message: types.Message, command: CommandObject):
    if not command.args:
        return await message.answer("Укажи email и часы. Пример: /addtemp guest 24")

    args = command.args.strip().split()
    if len(args) != 2:
        return await message.answer("Неверный формат. Пример: /addtemp guest 24")

    email, hours_str = args

    try:
        hours = int(hours_str)
        if hours <= 0:
            return await message.answer("Количество часов должно быть больше 0")
    except ValueError:
        return await message.answer("Количество часов должно быть числом")

    new_uuid = str(uuid.uuid4())

    with open(XRAY_CONFIG, 'r') as f:
        config = json.load(f)

    clients = config['inbounds'][0]['settings']['clients']

    # Проверяем дубликаты без учета регистра
    existing_emails = [c['email'].lower() for c in clients]
    if email.lower() in existing_emails:
        existing_email = next(c['email'] for c in clients if c['email'].lower() == email.lower())
        logger.warning(f"Попытка создать дубликат: {email} (существует: {existing_email})")
        return await message.answer(f"❌ Пользователь с таким именем уже существует: {existing_email}")

    clients.append({"email": email, "id": new_uuid, "flow": "xtls-rprx-vision"})

    with open(XRAY_CONFIG, 'w') as f:
        json.dump(config, f, indent=2)

    subprocess.run(["systemctl", "reload", "xray"])

    # Сохраняем информацию о временном пользователе
    expiry_time = datetime.now() + timedelta(hours=hours)
    temp_users[email] = {
        "uuid": new_uuid,
        "expiry": expiry_time.isoformat(),
        "hours": hours
    }
    save_temp_users(temp_users)

    logger.info(f"✅ Добавлен временный пользователь: {email} (UUID: {new_uuid}, истекает: {expiry_time})")

    # Генерируем VLESS-ключ
    vless_link = f"vless://{new_uuid}@{DOMAIN}:443?type=xhttp&security=reality&pbk={PUBLIC_KEY}&sni=github.com&fp=chrome&sid={SHORT_ID}&spx=%2F#{email}"

    expiry_str = expiry_time.strftime("%Y-%m-%d %H:%M:%S")

    await message.answer(
        f"✅ Временный пользователь **{email}** добавлен!\n\n"
        f"⏰ Доступ на {hours} ч.\n"
        f"🕐 Истекает: {expiry_str}\n\n"
        f"🔑 Ключ:\n\n`{vless_link}`",
        parse_mode="Markdown"
    )

# Функция для удаления истекших пользователей
async def cleanup_expired_users():
    logger.info("🔍 Проверка истекших временных пользователей...")
    logger.info(f"📊 Всего временных пользователей: {len(temp_users)}")
    now = datetime.now()
    expired = []

    for email, data in list(temp_users.items()):
        expiry = datetime.fromisoformat(data['expiry'])
        logger.info(f"  • {email}: истекает {expiry}, осталось {(expiry - now).total_seconds() / 3600:.1f} ч.")
        if now >= expiry:
            expired.append(email)
            logger.info(f"    ⏰ ИСТЕК!")

    if not expired:
        logger.info("✅ Истекших пользователей нет")
        return

    # Удаляем из конфига Xray
    with open(XRAY_CONFIG, 'r') as f:
        config = json.load(f)

    clients = config['inbounds'][0]['settings']['clients']
    original_count = len(clients)

    clients = [c for c in clients if c['email'] not in expired]
    config['inbounds'][0]['settings']['clients'] = clients

    with open(XRAY_CONFIG, 'w') as f:
        json.dump(config, f, indent=2)

    # Удаляем из списка временных пользователей
    for email in expired:
        del temp_users[email]

    save_temp_users(temp_users)

    if len(clients) != original_count:
        subprocess.run(["systemctl", "reload", "xray"])
        logger.info(f"✅ Удалены истекшие пользователи: {', '.join(expired)}")

        # Уведомляем администратора
        try:
            await bot.send_message(
                ADMIN_ID,
                f"🕐 Автоматически удалены истекшие пользователи:\n" + "\n".join(f"• {e}" for e in expired)
            )
        except Exception as e:
            logger.error(f"Не удалось отправить уведомление: {e}")

# --- 9. ЭКСПОРТ КОНФИГУРАЦИИ ---
@dp.message(Command("export"), F.func(is_admin))
async def cmd_export(message: types.Message):
    logger.info(f"✅ Команда /export от администратора {message.from_user.id}")

    try:
        if not os.path.exists(XRAY_CONFIG):
            return await message.answer(f"❌ Файл конфигурации не найден: {XRAY_CONFIG}")

        # Создаем имя файла с датой
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_filename = f"xray_config_backup_{timestamp}.json"

        await message.answer("📦 Создаю backup конфигурации...")
        await message.answer_document(
            FSInputFile(XRAY_CONFIG, filename=backup_filename),
            caption=f"🔐 Backup конфигурации Xray\n📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        )
        logger.info(f"✅ Конфигурация экспортирована: {backup_filename}")

    except Exception as e:
        logger.error(f"Ошибка при экспорте конфигурации: {e}")
        await message.answer(f"❌ Ошибка при экспорте: {str(e)}")

# --- 10. ПЕРЕЗАГРУЗКА XRAY ---
@dp.message(Command("restart"), F.func(is_admin))
async def cmd_restart(message: types.Message):
    logger.info(f"✅ Команда /restart от администратора {message.from_user.id}")

    await message.answer(
        "⚠️ <b>ВНИМАНИЕ!</b>\n\n"
        "Перезагрузка Xray разорвет все активные VPN-соединения.\n"
        "Пользователям придется переподключиться.\n\n"
        "Используй команду <code>/restart_confirm</code> для подтверждения.",
        parse_mode="HTML"
    )

@dp.message(Command("restart_confirm"), F.func(is_admin))
async def cmd_restart_confirm(message: types.Message):
    logger.info(f"✅ Подтверждение перезагрузки от администратора {message.from_user.id}")

    await message.answer("🔄 Перезагружаю Xray...")
    result = subprocess.run(["systemctl", "restart", "xray"], capture_output=True, text=True)

    if result.returncode == 0:
        logger.info("✅ Xray успешно перезапущен")
        await message.answer("✅ Xray успешно перезапущен!")
    else:
        logger.error(f"Ошибка при перезапуске Xray: {result.stderr}")
        await message.answer(f"❌ Ошибка при перезапуске:\n<pre>{result.stderr}</pre>", parse_mode="HTML")

# --- 11. ИНФОРМАЦИЯ О СИСТЕМЕ ---
@dp.message(Command("info"), F.func(is_admin))
async def cmd_info(message: types.Message):
    logger.info(f"✅ Команда /info от администратора {message.from_user.id}")

    try:
        # Версия Xray
        xray_version_result = subprocess.run(["xray", "version"], capture_output=True, text=True)
        xray_version = "Неизвестно"
        if xray_version_result.returncode == 0:
            # Парсим первую строку с версией
            first_line = xray_version_result.stdout.split('\n')[0]
            xray_version = first_line.strip()

        # Uptime сервера
        uptime_result = subprocess.run(["uptime", "-p"], capture_output=True, text=True)
        uptime = uptime_result.stdout.strip() if uptime_result.returncode == 0 else "Неизвестно"

        # Статус Xray
        xray_status_result = subprocess.run(
            ["systemctl", "is-active", "xray"],
            capture_output=True,
            text=True
        )
        xray_status = xray_status_result.stdout.strip()
        xray_status_emoji = "✅" if xray_status == "active" else "❌"

        # Время последнего запуска Xray
        xray_start_result = subprocess.run(
            ["systemctl", "show", "xray", "--property=ActiveEnterTimestamp"],
            capture_output=True,
            text=True
        )
        xray_start_time = "Неизвестно"
        if xray_start_result.returncode == 0:
            timestamp_line = xray_start_result.stdout.strip()
            if "=" in timestamp_line:
                xray_start_time = timestamp_line.split("=", 1)[1]

        # Версия бота
        bot_version = "1.0.0"

        # Количество пользователей
        with open(XRAY_CONFIG, 'r') as f:
            config = json.load(f)
        total_users = len(config['inbounds'][0]['settings']['clients'])
        temp_users_count = len(temp_users)
        permanent_users = total_users - temp_users_count

        info_text = (
            f"ℹ️ <b>Информация о системе</b>\n\n"
            f"<b>Xray:</b>\n"
            f"├ Версия: {xray_version}\n"
            f"├ Статус: {xray_status_emoji} {xray_status}\n"
            f"└ Запущен: {xray_start_time}\n\n"
            f"<b>Сервер:</b>\n"
            f"├ Uptime: {uptime}\n"
            f"└ Домен: {DOMAIN}\n\n"
            f"<b>Бот:</b>\n"
            f"└ Версия: {bot_version}\n\n"
            f"<b>Пользователи:</b>\n"
            f"├ Всего: {total_users}\n"
            f"├ Постоянных: {permanent_users}\n"
            f"└ Временных: {temp_users_count}"
        )

        await message.answer(info_text, parse_mode="HTML")

    except Exception as e:
        logger.error(f"Ошибка при получении информации: {e}")
        await message.answer(f"❌ Ошибка при получении информации: {str(e)}")

# --- 12. ОБРАБОТЧИК НЕИЗВЕСТНЫХ СООБЩЕНИЙ ---
@dp.message(F.func(is_admin))
async def unknown_message_handler(message: types.Message):
    logger.info(f"Неизвестное сообщение от администратора: {message.text}")
    await message.answer(
        "🤔 Я тебя не понимаю.\n\n"
        "Введи /help чтобы узнать, что я умею."
    )

async def main():
    logger.info("=" * 50)
    logger.info("🤖 Бот запущен и готов к работе!")
    logger.info(f"👤 Администратор ID: {ADMIN_ID}")
    logger.info(f"📡 Ожидание сообщений от Telegram...")
    logger.info("=" * 50)

    # Запускаем планировщик для проверки истекших пользователей
    scheduler.add_job(cleanup_expired_users, 'interval', minutes=10)
    scheduler.start()
    logger.info("✅ Планировщик запущен (проверка каждые 10 минут)")

    # Выполняем первую проверку сразу при запуске
    await cleanup_expired_users()

    try:
        await dp.start_polling(bot)
    except Exception as e:
        logger.error(f"❌ Ошибка при запуске polling: {e}")
        raise
    finally:
        scheduler.shutdown()

if __name__ == "__main__":
    asyncio.run(main())