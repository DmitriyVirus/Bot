import logging
import asyncio
from aiogram import Bot, Router, types
from aiogram.filters import Command
# Импорт ParseMode больше не нужен
# from aiogram.types import ParseMode

# Настройка логирования
logging.basicConfig(level=logging.DEBUG)

router = Router()

# Укажите ID закрепленного сообщения вручную
PINNED_MESSAGE_ID = 123456789  # Замените на ID сообщения, которое будет использоваться для хранения списка участников

# Обработчик команды /getidall
@router.message(Command("getidall"))
async def send_welcome(message: types.Message):
    """Приветственное сообщение."""
    await message.reply("Я собираю ID участников чата и добавляю их в сообщение!")

# Обработчик любого сообщения
@router.message()
async def collect_user_data(message: types.Message):
    """Собираем данные об участниках и обновляем сообщение."""
    user_id = message.from_user.id
    first_name = message.from_user.first_name
    chat_id = message.chat.id

    try:
        # Получаем информацию о чате
        chat = await bot.get_chat(chat_id)
        pinned_message = chat.pinned_message

        if pinned_message and pinned_message.message_id == PINNED_MESSAGE_ID:
            pinned_message_text = pinned_message.text

            # Проверим, если участник уже есть в списке
            if f'"{first_name}", "{user_id}"' not in pinned_message_text:
                updated_text = pinned_message_text[:-1] + f', "{first_name}", "{user_id}"}}'

                # Обновим закрепленное сообщение
                await bot.edit_message_text(updated_text, chat_id=chat_id, message_id=PINNED_MESSAGE_ID)

    except Exception as e:
        logging.error(f"Ошибка: {e}")
        # Если сообщение не закреплено, создаем новое
        user_list = f'{{"{first_name}", "{user_id}"}}'
        text = f"id участников чата: {user_list}"

        # Отправляем сообщение и закрепляем его
        sent_message = await bot.send_message(chat_id, text, parse_mode="Markdown")
        await bot.pin_chat_message(chat_id=chat_id, message_id=sent_message.message_id)
