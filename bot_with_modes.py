import asyncio
import subprocess
import os
import logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from dotenv import load_dotenv

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Загрузка переменных окружения
load_dotenv()

# --- НАСТРОЙКИ ---
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = os.getenv("ADMIN_ID")

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

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# --- РЕЖИМЫ РАБОТЫ ---
CHAT_MODE = "chat"
TERMINAL_MODE = "terminal"

# Хранилище текущего режима (в продакшене лучше использовать Redis/БД)
user_modes = {}

# --- КЛАВИАТУРЫ ---
def get_keyboard(current_mode):
    """Создает клавиатуру с кнопкой переключения режима"""
    if current_mode == CHAT_MODE:
        button_text = "🖥 Режим терминала"
    else:
        button_text = "💬 Режим чата"

    keyboard = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=button_text)]],
        resize_keyboard=True
    )
    return keyboard

# --- ФИЛЬТР БЕЗОПАСНОСТИ ---
def is_admin(message: types.Message) -> bool:
    user_id = message.from_user.id
    is_allowed = user_id == ADMIN_ID
    if not is_allowed:
        logger.warning(f"⚠️ Отклонено сообщение от неавторизованного пользователя {user_id}")
    return is_allowed

# --- ОБРАБОТЧИК ДЛЯ НЕАВТОРИЗОВАННЫХ ПОЛЬЗОВАТЕЛЕЙ ---
@dp.message(~F.func(is_admin))
async def unauthorized_handler(message: types.Message):
    logger.warning(f"❌ Неавторизованная попытка доступа от {message.from_user.id} (@{message.from_user.username})")
    await message.answer("⛔️ У вас нет доступа к этому боту.")

# --- КОМАНДА START ---
@dp.message(Command("start"), F.func(is_admin))
async def cmd_start(message: types.Message):
    user_id = message.from_user.id
    # По умолчанию устанавливаем режим чата
    user_modes[user_id] = CHAT_MODE

    logger.info(f"✅ Команда /start от администратора {user_id}")

    start_text = (
        f"👋 Привет, {message.from_user.first_name}!\n\n"
        "Я бот с двумя режимами работы:\n\n"
        "💬 **Режим чата** - обычное общение\n"
        "🖥 **Режим терминала** - выполнение команд на сервере\n\n"
        "Используй кнопку ниже для переключения режимов.\n"
        f"Текущий режим: **{CHAT_MODE.upper()}**"
    )

    await message.answer(
        start_text,
        parse_mode="Markdown",
        reply_markup=get_keyboard(CHAT_MODE)
    )

# --- ОБРАБОТЧИК ПЕРЕКЛЮЧЕНИЯ РЕЖИМОВ ---
@dp.message(F.text.in_(["🖥 Режим терминала", "💬 Режим чата"]), F.func(is_admin))
async def toggle_mode(message: types.Message):
    user_id = message.from_user.id
    current_mode = user_modes.get(user_id, CHAT_MODE)

    # Переключаем режим
    if current_mode == CHAT_MODE:
        new_mode = TERMINAL_MODE
        mode_text = "🖥 **Режим терминала активирован**\n\nТеперь все твои сообщения будут выполняться как Bash-команды на сервере."
    else:
        new_mode = CHAT_MODE
        mode_text = "💬 **Режим чата активирован**\n\nТеперь я просто отвечаю на твои сообщения."

    user_modes[user_id] = new_mode
    logger.info(f"🔄 Пользователь {user_id} переключился на режим: {new_mode}")

    await message.answer(
        mode_text,
        parse_mode="Markdown",
        reply_markup=get_keyboard(new_mode)
    )

# --- ОБРАБОТЧИК ТЕКСТОВЫХ СООБЩЕНИЙ ---
@dp.message(F.text, F.func(is_admin))
async def handle_text(message: types.Message):
    user_id = message.from_user.id
    current_mode = user_modes.get(user_id, CHAT_MODE)

    if current_mode == TERMINAL_MODE:
        # Режим терминала - выполняем команду
        command = message.text
        logger.info(f"🖥 Выполнение команды от {user_id}: {command}")

        await message.answer(f"⚙️ Выполняю команду:\n`{command}`", parse_mode="Markdown")

        try:
            # Выполняем команду через subprocess
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=30  # Таймаут 30 секунд
            )

            # Формируем ответ
            output = result.stdout if result.stdout else "(пусто)"
            error = result.stderr if result.stderr else "(нет ошибок)"

            response = (
                f"✅ **Команда выполнена**\n\n"
                f"**Код возврата:** `{result.returncode}`\n\n"
                f"**STDOUT:**\n```\n{output[:3000]}\n```\n\n"
                f"**STDERR:**\n```\n{error[:1000]}\n```"
            )

            # Если вывод слишком длинный, обрезаем
            if len(response) > 4000:
                response = response[:4000] + "\n\n... (вывод обрезан)"

            await message.answer(response, parse_mode="Markdown")

        except subprocess.TimeoutExpired:
            await message.answer("⏱ Команда превысила таймаут (30 секунд)")
        except Exception as e:
            logger.error(f"❌ Ошибка при выполнении команды: {e}")
            await message.answer(f"❌ Ошибка при выполнении:\n`{str(e)}`", parse_mode="Markdown")

    else:
        # Режим чата - просто отвечаем
        logger.info(f"💬 Сообщение в режиме чата от {user_id}: {message.text}")
        await message.answer(
            "💬 Я в режиме диалога, команды сервера не выполняются.\n\n"
            "Используй кнопку ниже, чтобы переключиться в режим терминала.",
            reply_markup=get_keyboard(CHAT_MODE)
        )

async def main():
    logger.info("=" * 50)
    logger.info("🤖 Бот с переключением режимов запущен!")
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
