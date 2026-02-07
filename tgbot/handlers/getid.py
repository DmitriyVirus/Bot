import os
import re
import logging
from aiogram.types import Message
from aiogram import types, Router
from aiogram.filters import Command
from aiogram.exceptions import TelegramBadRequest

# Настройка логирования
logging.basicConfig(level=logging.DEBUG)

router = Router()

CHAT_ID = int(os.environ.get("CHAT_ID"))
PINNED_MESSAGE_ID = int(os.environ.get("PINNED_MESSAGE_ID"))

@router.message(Command(commands=["getidbot"]))
async def send_message_with_id(message: types.Message):
    try:
        allowed_user_id = 559273200
        if message.from_user.id != allowed_user_id:
            return
            
        sent_message = await message.answer("Получаю id.")
        message_id = sent_message.message_id
        updated_text = f"ID этого сообщения: {message_id}"
        await sent_message.edit_text(updated_text)
        logging.info(f"Текст обновлен. ID сообщения: {message_id}")

    except Exception as e:
        logging.error(f"Ошибка при отправке или редактировании сообщения: {e}")
        await message.answer("Произошла ошибка. Попробуйте снова.")

# Обработчик команды /getid
@router.message(Command(commands=["getid"]))
async def send_chat_id(message: Message):
    try:
        allowed_user_id = 559273200 
        if message.from_user.id != allowed_user_id:
            return
        chat_id = message.chat.id
        await message.answer(f"Ваш Chat ID: `{chat_id}`", parse_mode="Markdown")
        logging.info(f"Chat ID ({chat_id}) отправлен пользователю {message.from_user.id}")
    except Exception as e:
        logging.error(f"Ошибка при отправке Chat ID: {e}")
        
