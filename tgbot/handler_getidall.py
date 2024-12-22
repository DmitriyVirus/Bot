import re
import logging
from aiogram.types import Message
from aiogram import types, Router
from aiogram.filters import Command
from aiogram.exceptions import TelegramBadRequest


# Настройка логирования
logging.basicConfig(level=logging.DEBUG)

router = Router()

CHAT_ID = -1001408912941  # Замените на ID вашего чата
PINNED_MESSAGE_ID = 280567  # Замените на ID закрепленного сообщения

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
        
@router.message()
async def update_message_text(message: types.Message):
    try:
        user_id = message.from_user.id
        user_name = message.from_user.full_name
        user_info = f"{user_id} - {user_name}"

        # Получаем текст сообщения
        current_text = await get_message_text(message.bot, CHAT_ID, PINNED_MESSAGE_ID)

        # Используем регулярное выражение для анализа текущего текста
        user_pattern = re.compile(r"\d+ - .+")
        users_in_message = user_pattern.findall(current_text)

        # Проверяем, есть ли пользователь в тексте
        if user_info not in users_in_message:
            updated_text = f"{current_text}\n{user_info}".strip()

            # Обновляем сообщение только если текст изменился
            await message.bot.edit_message_text(
                chat_id=CHAT_ID,
                message_id=PINNED_MESSAGE_ID,
                text=updated_text
            )
            logging.info("Текст сообщения обновлен.")
        else:
            logging.info("Информация уже есть в сообщении. Обновление не требуется.")

    except TelegramBadRequest as e:
        logging.error(f"Ошибка Telegram: {e}")
    except Exception as e:
        logging.error(f"Ошибка при обновлении сообщения: {type(e).__name__}: {e}")


async def get_message_text(bot, chat_id, message_id):
    """
    Получает текущий текст сообщения с использованием edit_message_text,
    но не изменяет фактически текст.
    """
    try:
        # Получаем текст сообщения, временно изменяя его
        placeholder = "placeholder"
        response = await bot.edit_message_text(chat_id=chat_id, message_id=message_id, text=placeholder)
        # Восстанавливаем оригинальный текст
        await bot.edit_message_text(chat_id=chat_id, message_id=message_id, text=response.text)
        return response.text
    except TelegramBadRequest:
        logging.error("Не удалось получить текст сообщения.")
        return ""
