from aiogram import types, Router
from aiogram.filters import Command
from decouple import config
import logging

# Указываем параметры
CHAT_ID = int(config('CHAT_ID'))  # Приводим ID к числу
PINNED_MESSAGE_ID = 2719  # Укажите вручную ID закрепленного сообщения

# Настройка логирования
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Создаем маршрутизатор
router = Router()

@router.message(Command("getidall"))
async def send_message_and_pin(message: types.Message):
    """Отправляет сообщение, закрепляет его и запоминает ID."""
    try:
        text = "Участники чата:\n"
        sent_message = await message.bot.send_message(
            chat_id=CHAT_ID,
            text=text
        )
        await message.bot.pin_chat_message(chat_id=CHAT_ID, message_id=sent_message.message_id)
        logging.info(f"Сообщение отправлено и закреплено с ID: {sent_message.message_id}")
    except Exception as e:
        logging.error(f"Ошибка при отправке и закреплении сообщения: {e}")
        await message.reply("Произошла ошибка. Попробуйте снова.")

@router.message()
async def update_pinned_message(message: types.Message):
    """Обновляет закрепленное сообщение, добавляя имя и ID пользователя."""
    user_id = message.from_user.id
    first_name = message.from_user.first_name

    try:
        # Получаем текст текущего закрепленного сообщения
        pinned_message = await message.bot.get_message(chat_id=CHAT_ID, message_id=PINNED_MESSAGE_ID)
        text = pinned_message.text

        # Проверяем, есть ли пользователь уже в списке
        if f"Имя: {first_name}, ID: {user_id}" not in text:
            text += f"\nИмя: {first_name}, ID: {user_id}"
            await message.bot.edit_message_text(
                chat_id=CHAT_ID,
                message_id=PINNED_MESSAGE_ID,
                text=text
            )
            logging.info(f"Обновлено закрепленное сообщение: добавлен Имя: {first_name}, ID: {user_id}")
    except Exception as e:
        logging.error(f"Ошибка при обновлении сообщения: {e}")
