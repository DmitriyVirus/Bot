from aiogram import types, Router
from aiogram.filters import Command
import logging

# Настройка логирования
logging.basicConfig(level=logging.DEBUG)

router = Router()

# Указываем ID чата и закрепленного сообщения вручную
CHAT_ID = -1002388880478  # Замените на ID вашего чата
PINNED_MESSAGE_ID = 2719  # Замените на ID закрепленного сообщения

# Хендлер для команды /getidall
@router.message(Command(commands=["getidall"]))
async def update_message_text(message: types.Message):
    """Меняет текст закрепленного сообщения на 'Здесь буду записывать id и имена участников чата:'"""
    try:
        # Ответим пользователю, что обновляем текст
        await message.answer("Обновляю текст закрепленного сообщения...")

        # Обновляем текст закрепленного сообщения
        updated_text = "Здесь буду записывать id и имена участников чата:"
        await message.bot.edit_message_text(
            chat_id=CHAT_ID,
            message_id=PINNED_MESSAGE_ID,
            text=updated_text
        )

        # Логируем ID обновленного сообщения
        logging.info(f"Текст закрепленного сообщения обновлен. ID сообщения: {PINNED_MESSAGE_ID}")
        
        # Отправляем подтверждающее сообщение и логируем его ID
        sent_message = await message.bot.send_message(
            chat_id=CHAT_ID,
            text=f"ID этого сообщения: {PINNED_MESSAGE_ID}"
        )
        logging.info(f"Отправлено новое сообщение с ID: {sent_message.message_id}")

    except Exception as e:
        logging.error(f"Ошибка при обновлении сообщения: {e}")
        await message.answer("Произошла ошибка. Попробуйте снова.")
