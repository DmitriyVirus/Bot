from aiogram import types, Router
from aiogram.filters import Command
import logging

# Настройка логирования
logging.basicConfig(level=logging.DEBUG)

router = Router()

# Указываем ID чата и ID закрепленного сообщения, которое будем обновлять
CHAT_ID = -1002388880478  # Замените на ID вашего чата
PINNED_MESSAGE_ID = 2743  # Замените на ID закрепленного сообщения

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
        
@router.message()
async def update_message_text(message: types.Message):
    """Обновляет текст закрепленного сообщения с id и именами пользователей, не добавляя повторений"""
    try:
        # Извлекаем информацию о пользователе
        user_id = message.from_user.id
        user_name = message.from_user.full_name

        # Формируем строку для добавления в сообщение
        user_info = f"{user_id} - {user_name}"

        # Получаем текущее закрепленное сообщение
        pinned_message = await message.bot.get_chat(CHAT_ID)
        pinned_message_text = pinned_message.pinned_message.text if pinned_message.pinned_message else ""

        # Проверяем, не добавлен ли этот пользователь уже в список
        if user_info not in pinned_message_text:
            # Добавляем пользователя в текущий текст
            updated_text = f"{pinned_message_text}\n{user_info}"
        else:
            # Если пользователь уже добавлен, оставляем текст без изменений
            updated_text = pinned_message_text

       # Проверяем, изменился ли текст
        if updated_text != pinned_message_text:
            # Обновляем текст закрепленного сообщения
            await message.bot.edit_message_text(
                chat_id=CHAT_ID,
                message_id=PINNED_MESSAGE_ID,
                text=updated_text
            )

            logging.info(f"Текст закрепленного сообщения обновлен.")
        else:
            logging.info(f"Текст закрепленного сообщения не изменился. Обновление не требуется.")

    except Exception as e:
        logging.error(f"Ошибка при обновлении сообщения: {e}")
