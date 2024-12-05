from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram import Router
from decouple import config
import logging

# Указываем ID чата и закрепленного сообщения вручную
CHAT_ID = config('CHAT_ID')  # ID вашего чата
PINNED_MESSAGE_ID = 2719  # ID закрепленного сообщения

# Настройка логирования
logging.basicConfig(level=logging.INFO)

# Создаем роутер для хендлеров
router = Router()

# Команда /getidall для отправки и закрепления сообщения
@router.message(Command("getidall"))
async def send_message_and_pin(message: types.Message, bot: Bot):
    """Изменяет текст указанного сообщения на 'Здесь буду записывать id и имена участников чата:'"""
    try:
        # Получаем сообщение с указанным message_id
        pinned_message = await bot.get_message(chat_id=CHAT_ID, message_id=PINNED_MESSAGE_ID)

        # Проверяем, что сообщение существует
        if pinned_message:
            # Меняем текст сообщения
            updated_text = "Здесь буду записывать id и имена участников чата:"
            await bot.edit_message_text(
                chat_id=CHAT_ID,
                message_id=PINNED_MESSAGE_ID,
                text=updated_text
            )
            logging.info(f"Текст закрепленного сообщения обновлен.")
        else:
            logging.error("Не удалось найти сообщение с таким ID.")
    except Exception as e:
        logging.error(f"Ошибка при обновлении сообщения: {e}")
        await message.answer("Произошла ошибка. Попробуйте снова.")
