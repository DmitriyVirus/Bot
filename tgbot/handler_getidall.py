import logging
from aiogram.types import Message
from aiogram import types, Router
from aiogram.filters import Command

# Настройка логирования
logging.basicConfig(level=logging.DEBUG)

router = Router()

CHAT_ID = -1001408912941  # Замените на ID вашего чата
PINNED_MESSAGE_ID = 280471  # Замените на ID закрепленного сообщения

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
        
        chat = await message.bot.get_chat(CHAT_ID)
        
        if chat.pinned_message:
            pinned_message_text = chat.pinned_message.text or ""
        else:
            pinned_message_text = ""
            
        if user_info not in pinned_message_text:
            updated_text = f"{pinned_message_text}\n{user_info}"
        else:
            updated_text = pinned_message_text
        if updated_text != pinned_message_text:
            await message.bot.edit_message_text(
                chat_id=CHAT_ID,
                message_id=PINNED_MESSAGE_ID,
                text=updated_text
            )
            logging.info("Текст закрепленного сообщения обновлен.")
        else:
            logging.info("Текст закрепленного сообщения не изменился. Обновление не требуется.")

    except Exception as e:
        logging.error(f"Ошибка при обновлении сообщения: {type(e).__name__}: {e}")
