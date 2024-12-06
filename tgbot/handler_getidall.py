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
        sent_message = await message.answer("Получаю id.")
        message_id = sent_message.message_id
        updated_text = f"ID этого сообщения: {message_id}"
        await sent_message.edit_text(updated_text)
        logging.info(f"Текст обновлен. ID сообщения: {message_id}")
    except Exception as e:
        logging.error(f"Ошибка при отправке или редактировании сообщения: {type(e).__name__}: {e}")
        await message.answer("Произошла ошибка. Попробуйте снова.")

@router.message()
async def update_message_text(message: types.Message):
    """Обновляет текст закрепленного сообщения, добавляя новых пользователей, и сохраняет заголовок"""
    try:
        # Извлекаем ID и имя пользователя
        user_id = message.from_user.id
        user_name = message.from_user.full_name
        user_info = f"{user_id} - {user_name}"

        # Получаем текущее закрепленное сообщение
        pinned_message = await message.bot.get_chat(CHAT_ID)
        pinned_message_text = ""
        
        if pinned_message.pinned_message:
            pinned_message_text = pinned_message.pinned_message.text or ""

        # Заголовок для списка участников
        header = "Айди участников:\n\n"

        # Проверяем, содержит ли сообщение заголовок
        if not pinned_message_text.startswith(header):
            # Если заголовка нет, начинаем с чистого заголовка
            current_list = []
        else:
            # Извлекаем существующий список участников, удаляя заголовок
            current_list = pinned_message_text[len(header):].strip().split("\n")
        
        # Проверяем, есть ли уже информация о пользователе
        if user_info not in current_list:
            current_list.append(user_info)  # Добавляем нового участника
        else:
            logging.info(f"Пользователь {user_info} уже есть в списке. Обновление не требуется.")
            return
        
        # Формируем обновленный текст
        updated_text = f"{header}{'\n'.join(current_list)}"

        # Проверяем длину текста
        if len(updated_text) > 4096:
            logging.warning("Текст слишком длинный для обновления сообщения.")
            return

        # Обновляем текст закрепленного сообщения
        await message.bot.edit_message_text(
            chat_id=CHAT_ID,
            message_id=PINNED_MESSAGE_ID,
            text=updated_text
        )
        logging.info("Текст закрепленного сообщения успешно обновлен.")

    except Exception as e:
        logging.error(f"Ошибка при обновлении сообщения: {type(e).__name__}: {e}")
