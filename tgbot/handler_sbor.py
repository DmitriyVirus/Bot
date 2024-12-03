from aiogram import types, Router
from aiogram.filters import Command
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
import re
import logging

router = Router()

# Хендлер для команды /inst
@router.message(Command(commands=["inst"]))
async def fix_handler(message: types.Message):
    try:
        # Попытка извлечь время из текста после команды /inst
        time_match = re.search(r"(\d{1,2}:\d{2})", message.text)
        time = time_match.group(1) if time_match else "когда соберемся"
        # Фото для отправки (замените на свой путь к фото или URL)
        photo_url = "https://battleclub.space/uploads/monthly_2022_07/baylor.jpg.02e0df864753bf47b1ef76303b993a1d.jpg"
        # Создание клавиатуры
        keyboard = create_keyboard()
        # Отправка фото с текстом и клавишами
        sent_message = await message.bot.send_photo(
            chat_id=message.chat.id,
            photo=photo_url,
            caption=(
                f"*Идем в инсты {time}*. Как обычно идут Дмитрий(МакароноВирус), Леонид(ТуманныйТор) и кто-то еще. "
                f"*Нажмите ➕ в сообщении для участия*"
            ),
            parse_mode="Markdown",
            reply_markup=keyboard
        )
        # Закрепляем сообщение с фото
        await message.chat.pin_message(sent_message.message_id)
        logging.info(f"Сообщение отправлено и закреплено с id: {sent_message.message_id}")
    except Exception as e:
        logging.error(f"Ошибка при обработке команды /fix: {e}")
        await message.answer("Произошла ошибка. Попробуйте снова.")

# Функция для парсинга текста и получения списка участников
def filter_participants(caption: str):
    logging.debug(f"Подпись для анализа: {caption}")
    # Регулярное выражение для извлечения списка участников без звёздочек
    match = re.search(r"Желающие \d+ человек: (.+)", caption, flags=re.DOTALL)
    if match:
        participants_text = match.group(1)
        logging.debug(f"Найден текст участников: {participants_text}")
        return [name.strip() for name in participants_text.split(",") if name.strip()]
    logging.debug("Не удалось найти участников в подписи.")
    return []
    
# Функция для извлечения времени из подписи
def extract_time_from_caption(caption: str):
    time_match = re.search(r"Идем в инсты\s*(\d{1,2}:\d{2}|когда соберемся)", caption)
    return time_match.group(1) if time_match else "когда соберемся"

# Функция для обновления подписи к фото
async def update_caption(photo_message: types.Message, participants: list, callback: types.CallbackQuery, action_message: str, time: str, keyboard: InlineKeyboardMarkup):
    participants_count = len(participants)
    joined_users = ", ".join(participants) if participants else ""

    if participants:
        updated_text = (
            f"*Идем в инсты {time}*. Как обычно идут Дмитрий(МакароноВирус), Леонид(ТуманныйТор) и кто-то еще. "
            f"*Нажмите ➕ в сообщении для участия*.\n\nЖелающие {participants_count} человек: *{joined_users}*"
        )
    else:
        updated_text = (
            f"*Идем в инсты {time}*. Как обычно идут Дмитрий(МакароноВирус), Леонид(ТуманныйТор) и кто-то еще. "
            f"*Нажмите ➕ в сообщении для участия*.\n\nЖелающие {participants_count} человек"
        )

    if updated_text == photo_message.caption:
        logging.debug("Подпись не изменилась, обновление не требуется.")
        await callback.answer(action_message)
        return
        
    try:
        await photo_message.edit_caption(caption=updated_text, parse_mode="Markdown", reply_markup=keyboard)
        await callback.answer(action_message)
    except Exception as e:
        logging.error(f"Ошибка при обновлении подписи: {e}")
        await callback.answer("Не удалось обновить подпись. Попробуйте снова.")

# Обработчик для нажатия на кнопку "➕ Присоединиться"
@router.callback_query(lambda callback: callback.data == "join_plus")
async def handle_plus_reaction(callback: types.CallbackQuery):
    username = callback.from_user.first_name
    message = callback.message
    participants = filter_participants(message.caption)

    # Выводим отладочную информацию о текущем списке участников
    logging.debug(f"Текущий список участников перед добавлением: {participants}")

    # Проверка, что имя пользователя еще не в списке
    if username not in participants:
        participants.append(username)
        logging.debug(f"{username} ещё не в списке. Добавляем.")
        action_message = f"Вы присоединились, {username}!"
    else:
        logging.debug(f"{username} уже в списке.")
        action_message = f"Вы уже участвуете, {username}!"

    time = extract_time_from_caption(message.caption)
    keyboard = create_keyboard()  # Создание клавиатуры
    await update_caption(message, participants, callback, action_message, time, keyboard)

    # Выводим отладочную информацию после добавления
    logging.debug(f"Обновленный список участников после добавления: {participants}")

# Обработчик для нажатия на кнопку "➖ Не участвовать"
@router.callback_query(lambda callback: callback.data == "join_minus")
async def handle_minus_reaction(callback: types.CallbackQuery):
    username = callback.from_user.first_name
    message = callback.message
    participants = filter_participants(message.caption)

    # Выводим отладочную информацию о текущем списке участников
    logging.debug(f"Текущий список участников перед удалением: {participants}")
    
    # Проверка, что имя пользователя есть в списке участников
    if username in participants:
        logging.debug(f"{username} найден в списке. Удаляем.")
        participants.remove(username)
        action_message = f"Вы больше не участвуете, {username}."
    else:
        logging.debug(f"{username} не найден в списке.")
        action_message = f"Вы не участвуете."

    time = extract_time_from_caption(message.caption)
    keyboard = create_keyboard()  # Создание клавиатуры
    await update_caption(message, participants, callback, action_message, time, keyboard)
    
    # Выводим отладочную информацию после удаления
    logging.debug(f"Обновленный список участников после удаления: {participants}")

# Функция для создания клавиатуры
def create_keyboard():
    plus_button = InlineKeyboardButton(text="➕ Присоединиться", callback_data="join_plus")
    minus_button = InlineKeyboardButton(text="➖ Не участвовать", callback_data="join_minus")
    return InlineKeyboardMarkup(inline_keyboard=[[plus_button, minus_button]])
