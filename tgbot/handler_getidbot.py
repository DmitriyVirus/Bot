from aiogram import types, Router
from aiogram.filters import Command
import logging

# Настройка логирования
logging.basicConfig(level=logging.DEBUG)

router = Router()

# Хендлер для команды /getidbot
@router.message(Command(commands=["getidbot"]))
async def send_message_with_id(message: types.Message):
    try:
        # Отправляем начальное сообщение
        sent_message = await message.answer("Получаю id.")
        
        # Извлекаем ID отправленного сообщения
        message_id = sent_message.message_id
        
        # Редактируем это сообщение, добавляя его ID в текст
        updated_text = f"ID этого сообщения: {message_id}"
        await sent_message.edit_text(updated_text)
        
        logging.info(f"Текст обновлен. ID сообщения: {message_id}")  # Логируем ID сообщения
    except Exception as e:
        logging.error(f"Ошибка при отправке или редактировании сообщения: {e}")
        await message.answer("Произошла ошибка. Попробуйте снова.")
