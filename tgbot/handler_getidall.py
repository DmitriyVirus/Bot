from aiogram import types, Router
from aiogram.filters import Command
import logging

# Настройка логирования
logging.basicConfig(level=logging.DEBUG)

router = Router()

# Указываем ID чата и ID закрепленного сообщения, которое будем обновлять
CHAT_ID = -1002388880478  # Замените на ID вашего чата
PINNED_MESSAGE_ID = 2743  # Замените на ID закрепленного сообщения

# Хендлер для команды /getidall
@router.message(Command(commands=["getidall"]))
async def update_message_text(message: types.Message):
    """Меняет текст закрепленного сообщения на 'Тут список id и имен людей в чате:'"""
    try:
        # Ответим пользователю, что обновляем текст
        await message.answer("Обновляю текст закрепленного сообщения...")

        # Считываем информацию о пользователе, отправившем сообщение
        user_id = message.from_user.id
        user_name = message.from_user.full_name

        # Формируем информацию, которую будем добавлять в текст закрепленного сообщения
        user_info = f"{user_id} - {user_name}"

        # Обновляем текст закрепленного сообщения
        updated_text = f"Тут список id и имен людей в чате:\n\n{user_info}"

        # Обновляем текст закрепленного сообщения
        await message.bot.edit_message_text(
            chat_id=CHAT_ID,
            message_id=PINNED_MESSAGE_ID,
            text=updated_text
        )

        logging.info(f"Текст закрепленного сообщения обновлен: {user_info}")
    except Exception as e:
        logging.error(f"Ошибка при обновлении сообщения: {e}")
        await message.answer("Произошла ошибка. Попробуйте снова.")
