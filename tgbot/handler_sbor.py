import logging
import re
from aiogram import types, Router
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.filters import Command

# Создаем объект Router
router = Router()

# Хендлер для команды /fix с учетом времени
@router.message(Command(commands=["fix"]))
async def fix_handler(message: types.Message):
    try:
        # Извлекаем время из текста команды
        time_pattern = r"(\d{1,2}:\d{2})"  # Паттерн для времени (например, 19:30)
        match = re.search(time_pattern, message.text)
        time = match.group(1) if match else "когда соберемся"  # Если время указано, берем его, иначе ставим "не указано"

        keyboard = create_keyboard()
        sent_message = await message.answer(f"Я жду {time}...\n\nУчаствуют 0 человек(а):", reply_markup=keyboard)
        await message.chat.pin_message(sent_message.message_id)
        logging.info(f"Сообщение отправлено и закреплено с id: {sent_message.message_id}")
    except Exception as e:
        logging.error(f"Ошибка при обработке команды /fix: {e}")
        await message.answer("Произошла ошибка. Попробуйте снова.")

# Функция для создания клавиатуры
def create_keyboard():
    plus_button = InlineKeyboardButton(text="➕ Присоединиться", callback_data="join_plus")
    minus_button = InlineKeyboardButton(text="➖ Не участвовать", callback_data="join_minus")
    return InlineKeyboardMarkup(inline_keyboard=[[plus_button, minus_button]])

# Функция для парсинга текста и получения списка участников
def filter_participants(text: str):
     excluded_text = r'Я жду\.\.\.\s*Участвуют \d+ человек\(а\):\s*|Когда|соберемся|\d+'
    text = re.sub(excluded_text, '', text)
    return [name.strip() for name in text.split(",") if name.strip()]

# Функция для обновления сообщения
async def update_message(message: types.Message, participants: list, callback: types.CallbackQuery, action_message: str):
    participants_count = len(participants)
    joined_users = ", ".join(participants)
    
    # Делаем проверку на правильность формата времени
    time = message.text.split()[2] if len(message.text.split()) > 2 else "когда соберемся"
    updated_text = f"Я жду {time}...\n\nУчаствуют {participants_count} человек(а): {joined_users}".strip()

    current_text = message.text.strip() if message.text else ""
    if current_text == updated_text:
        await callback.answer(action_message)
        return

    try:
        keyboard = create_keyboard()
        await message.edit_text(updated_text, reply_markup=keyboard)
        await callback.answer(action_message)
        logging.info(f"Сообщение обновлено: {updated_text}")
    except Exception as e:
        logging.error(f"Ошибка при обновлении сообщения: {e}")
        await callback.answer("Не удалось обновить сообщение. Попробуйте снова.")

# Обработчик для нажатия на кнопку "➕ Присоединиться"
@router.callback_query(lambda callback: callback.data == "join_plus")
async def handle_plus_reaction(callback: types.CallbackQuery):
    username = callback.from_user.first_name
    message = callback.message

    participants = filter_participants(message.text)
    if username not in participants:
        participants.append(username)
        action_message = f"Вы присоединились, {username}!"
    else:
        action_message = f"Вы уже участвуете, {username}!"

    await update_message(message, participants, callback, action_message)

# Обработчик для нажатия на кнопку "➖ Не участвовать"
@router.callback_query(lambda callback: callback.data == "join_minus")
async def handle_minus_reaction(callback: types.CallbackQuery):
    username = callback.from_user.first_name
    message = callback.message

    participants = filter_participants(message.text)
    if username in participants:
        participants.remove(username)
        action_message = f"Вы больше не участвуете, {username}."
    else:
        action_message = f"Вы не участвовали."

    await update_message(message, participants, callback, action_message)

