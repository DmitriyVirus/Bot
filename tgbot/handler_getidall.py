from aiogram import types, Router
from aiogram.filters import Command
import logging

# Настройка логирования
logging.basicConfig(level=logging.DEBUG)

# Указываем ID чата и закрепленного сообщения вручную
CHAT_ID = 123456789  # Замените на ID вашего чата
PINNED_MESSAGE_ID = 2719  # ID закрепленного сообщения

# Создаем роутер для хендлеров
router = Router()

# Хендлер для команды /inst
@router.message(Command(commands=["getidall"]))
async def update_message_text(message: types.Message):
    """Меняет текст закрепленного сообщения на 'Здесь буду записывать id и имена участников чата:'"""
    try:
        # Получаем информацию о чате и сообщение
        pinned_message = await message.bot.get_message(chat_id=CHAT_ID, message_id=PINNED_MESSAGE_ID)
        
        # Обновляем текст закрепленного сообщения
        updated_text = "Здесь буду записывать id и имена участников чата:"
        await message.bot.edit_message_text(
            chat_id=CHAT_ID,
            message_id=PINNED_MESSAGE_ID,
            text=updated_text
        )
        logging.info(f"Текст закрепленного сообщения обновлен.")
    except Exception as e:
        logging.error(f"Ошибка при обновлении сообщения: {e}")
        await message.answer("Произошла ошибка. Попробуйте снова.")
