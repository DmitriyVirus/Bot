from aiogram import types, Router
from aiogram.filters import Command
import logging

# Настройка логирования
logging.basicConfig(level=logging.DEBUG)

router = Router()

# Указываем ID чата и ID закрепленного сообщения, которое будем обновлять
CHAT_ID = -1002388880478  # Замените на ID вашего чата
TARGET_MESSAGE_ID = 3665  # Замените на ID закрепленного сообщения

from aiogram import types
import logging

@router.message()
async def update_message_text(message: types.Message):
    """Обновляет текст указанного сообщения с id и именами пользователей, не добавляя повторений"""
    try:
        # Извлекаем информацию о пользователе
        user_id = message.from_user.id
        user_name = message.from_user.full_name

        # Формируем строку для добавления в сообщение
        user_info = f"{user_id} - {user_name}"

        # Получаем сообщение с указанным ID
        target_message = await message.bot.get_message(chat_id=CHAT_ID, message_id=TARGET_MESSAGE_ID)
        
        # Извлекаем текст сообщения
        message_text = target_message.text or ""  # Если текст пустой, используем пустую строку

        # Проверяем, не добавлен ли этот пользователь уже в список
        if user_info not in message_text:
            # Добавляем пользователя в текущий текст
            updated_text = f"{message_text}\n{user_info}"
        else:
            # Если пользователь уже добавлен, оставляем текст без изменений
            updated_text = message_text

        # Проверяем, изменился ли текст
        if updated_text != message_text:
            # Обновляем текст сообщения
            await message.bot.edit_message_text(
                chat_id=CHAT_ID,
                message_id=TARGET_MESSAGE_ID,
                text=updated_text
            )
            logging.info("Текст сообщения обновлен.")
        else:
            logging.info("Текст сообщения не изменился. Обновление не требуется.")

    except Exception as e:
        logging.error(f"Ошибка при обновлении сообщения: {type(e).__name__}: {e}")

@router.message(Command(commands=["getidbot"]))
async def send_message_with_id(message: types.Message):
    try:
        # Указываем ID пользователя, который может вызвать команду
        allowed_user_id = 559273200  # Замените на нужный ID

        # Проверяем, является ли ID пользователя допустимым
        if message.from_user.id != allowed_user_id:
            # Если это не тот пользователь, игнорируем команду или отправляем сообщение
            return
        # Если это тот пользователь, выполняем команду
        sent_message = await message.answer("Получаю id.")
        message_id = sent_message.message_id
        updated_text = f"ID этого сообщения: {message_id}"
        await sent_message.edit_text(updated_text)
        logging.info(f"Текст обновлен. ID сообщения: {message_id}")

    except Exception as e:
        logging.error(f"Ошибка при отправке или редактировании сообщения: {e}")
        await message.answer("Произошла ошибка. Попробуйте снова.")
