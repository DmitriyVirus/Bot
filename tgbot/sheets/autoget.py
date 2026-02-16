import logging
import asyncio
from aiogram import Router, types
from aiogram.filters import Command
from tgbot.sheets.take_from_sheet import add_user_to_sheet_safe

# Настроим логирование
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Инициализация роутера
router = Router()

# ==========================
# Хендлер сообщений
# ==========================
@router.message(~Command())
async def handle_message(message: types.Message):
    """
    При получении любого сообщения пытаемся добавить пользователя в Google Sheets.
    """
    user_id = message.from_user.id
    username = message.from_user.username or "Unknown"
    first_name = message.from_user.first_name or "Unknown"
    last_name = message.from_user.last_name or "Unknown"

    logging.info(f"Обрабатываем сообщение от {username} ({user_id})")

    # Вызываем блокирующую функцию в отдельном потоке
    await asyncio.to_thread(add_user_to_sheet_safe, user_id, username, first_name, last_name)
