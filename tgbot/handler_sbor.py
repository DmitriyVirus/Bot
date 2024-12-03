import logging
import re
from aiogram import types, Router
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.filters import Command

router = Router()

# Хендлер для команды /fix
@router.message(Command(commands=["fix"]))
async def fix_handler(message: types.Message):
    try:
        # Попытка извлечь время из текста после команды /fix
        time_match = re.search(r"(\d{1,2}:\d{2})", message.text)
        if time_match:
            time = time_match.group(1)
        else:
            time = "сколько угодно"  # Если время не указано

        # Создание клавиатуры
        keyboard = create_keyboard()
        
        # Сообщение с указанием времени
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
    # Извлекаем часть с участниками, оставляя время
    excluded_text = r'Я жду\s*(\d{1,2}:\d{2}|сколько угодно)?\.\.\.\s*Участвуют \d+ человек\(а\):\s*'
    text = re.sub(excluded_text, '', text)
    return [name.strip() for name in text.split(",") if name.strip()]

# Функция для обновления сообщения
async def update_message(message: types.Message, participants: list, callback: types.CallbackQuery, action_message: str):
    # Извлекаем время из текущего текста сообщения
    time_match = re.search(r'Я жду\s*(\d{1,2}:\d{2}|сколько угодно)', message.text)
    if time_match:
        time = time_match.group(1)
    else:
        time = "сколько угодно"  # Если времени нет

    # Считаем количество участников и составляем список
    participants_count = len(participants)
    joined_users = ", ".join(participants)

    # Формируем новый текст для сообщения с учетом времени
    updated_text = f"Я жду {time}...\n\nУчаствуют {participants_count} человек(а): {joined_users}".strip()

    # Если текущий текст и новый совпадают, не обновляем
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

# Хендлер для команды /inst
@router.message(Command(commands=["inst"]))
async def inst_handler(message: types.Message):
    try:
        # Извлекаем время, если оно указано
        time_match = re.search(r"(\d{1,2}:\d{2})", message.text)
        if time_match:
            time = time_match.group(1)
        else:
            time = "сколько угодно"  # Если время не указано

        # Фото для отправки (замените на свой путь к фото или URL)
        photo_url = "https://battleclub.space/uploads/monthly_2022_07/baylor.jpg.02e0df864753bf47b1ef76303b993a1d.jpg"  # Замените на URL или путь к вашему фото

        # Создание клавиатуры
        keyboard = create_keyboard()

        # Отправляем фото с подписью
        sent_message = await message.answer_photo(photo=photo_url, caption=f"Я жду {time}...\n\nУчаствуют 0 человек(а):", reply_markup=keyboard)
        await message.chat.pin_message(sent_message.message_id)
        logging.info(f"Фото отправлено и закреплено с id: {sent_message.message_id}")
    except Exception as e:
        logging.error(f"Ошибка при обработке команды /inst: {e}")
        await message.answer("Произошла ошибка. Попробуйте снова.")

