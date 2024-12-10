from aiogram import types, Router
from aiogram.filters import Command
from aiogram.types import Message
import logging

# Настройка логирования
logging.basicConfig(level=logging.DEBUG)

router = Router()

# Указываем ID чата и ID закрепленного сообщения, которое будем обновлять
CHAT_ID = -1002388880478  # Замените на ID вашего чата
MESSAGE_ID = 3686  # Замените на ID закрепленного сообщения

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

@router.message()
async def update_message_text(message: types.Message):
    """Обновляет текст НЕ закрепленного сообщения с id и именами пользователей"""
    try:
        # Извлекаем информацию о пользователе
        user_id = message.from_user.id
        user_name = message.from_user.full_name

        # Формируем строку для добавления в сообщение
        user_info = f"{user_id} - {user_name}"

        # Получаем текущее сообщение
        current_message = await message.bot.get_message(chat_id=CHAT_ID, message_id=MESSAGE_ID)
        current_text = current_message.text if current_message else ""

        # Проверяем, был ли уже этот пользователь добавлен в сообщение
        if user_info not in current_text:
            # Формируем обновленный текст
            updated_text = f"{current_text}\n{user_info}"
            # Редактируем текст сообщения
            await message.bot.edit_message_text(
                chat_id=CHAT_ID,  # ID чата, где сообщение
                message_id=MESSAGE_ID,  # ID сообщения, которое нужно обновить
                text=updated_text  # Новый текст
            )
            logging.info(f"Текст сообщения с ID {MESSAGE_ID} обновлен.")
        else:
            logging.info(f"Пользователь {user_info} уже был добавлен. Обновление не требуется.")
    
    except Exception as e:
        logging.error(f"Ошибка при обновлении сообщения: {type(e).__name__}: {e}")
