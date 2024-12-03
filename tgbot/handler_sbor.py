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
            time = "когда соберемся"  # Если время не указано

        # Фото для отправки (замените на свой путь к фото или URL)
        photo_url = "https://battleclub.space/uploads/monthly_2022_07/baylor.jpg.02e0df864753bf47b1ef76303b993a1d.jpg"  # Замените на URL или путь к вашему фото

        # Создание клавиатуры
        keyboard = create_keyboard()

        # Отправка текста для привязки к фото
        sent_message = await message.answer(f"Идем в инсты {time}. Как обычно идут Дмитрий(МакароноВирус), Леонид(ТуманныйТор) и кто-то еще. Нажимайте + в сообщении.\n\nЖелающие 0 человек(а):", reply_markup=keyboard)
        photo_message = await message.bot.send_photo(chat_id=message.chat.id, photo=photo_url, caption=sent_message.text)

        # Закрепляем сообщение с фото
        await message.chat.pin_message(photo_message.message_id)
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
    excluded_text = r'Идем в инсты\s*(\d{1,2}:\d{2}|когда соберемся)?\.\s*Как обычно идут Дмитрий\(МакароноВирус\), Леонид\(ТуманныйТор\)(?:, .+)?\s*Нажимайте \+ в сообщении\.\s*Желающие \d+ человек\(а\):\s*'
    text = re.sub(excluded_text, '', text)
    return [name.strip() for name in text.split(",") if name.strip()]

# Функция для обновления подписи к фото
async def update_caption(photo_message: types.Message, participants: list, callback: types.CallbackQuery, action_message: str, time: str):
    # Считаем количество участников и составляем список
    participants_count = len(participants)
    joined_users = ", ".join(participants)

    # Формируем новый текст для подписи с учетом времени
    updated_text = f"Идем в инсты {time}. Как обычно идут Дмитрий(МакароноВирус), Леонид(ТуманныйТор) и кто-то еще. Нажимайте + в сообщении.\n\nЖелающие: {joined_users}".strip()

    # Если текущая подпись и новая совпадают, не обновляем
    current_caption = photo_message.caption.strip() if photo_message.caption else ""
    if current_caption == updated_text:
        await callback.answer(action_message)
        return

    try:
        await photo_message.edit_caption(updated_text)
        await callback.answer(action_message)
        logging.info(f"Подпись обновлена: {updated_text}")
    except Exception as e:
        logging.error(f"Ошибка при обновлении подписи: {e}")
        await callback.answer("Не удалось обновить подпись. Попробуйте снова.")

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

    # Используем callback.message.message_id для получения сообщения с фото
    photo_message = await callback.message.bot.get_message(chat_id=callback.message.chat.id, message_id=callback.message.message_id)

    time_match = re.search(r'Идем в инсты\s*(\d{1,2}:\d{2}|когда соберемся)', photo_message.caption)
    if time_match:
        time = time_match.group(1)
    else:
        time = "когда соберемся"

    await update_caption(photo_message, participants, callback, action_message, time)

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

    # Используем callback.message.message_id для получения сообщения с фото
    photo_message = await callback.message.bot.get_message(chat_id=callback.message.chat.id, message_id=callback.message.message_id)

    time_match = re.search(r'Идем в инсты\s*(\d{1,2}:\d{2}|когда соберемся)', photo_message.caption)
    if time_match:
        time = time_match.group(1)
    else:
        time = "когда соберемся"

    await update_caption(photo_message, participants, callback, action_message, time)

