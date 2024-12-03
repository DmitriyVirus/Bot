from aiogram import types, Router
from aiogram.filters import Command
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.fsm.context import FSMContext
import re
import logging

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

        # Отправка фото с текстом и клавишами
        sent_message = await message.bot.send_photo(
            chat_id=message.chat.id,
            photo=photo_url,
            caption=f"Идем в инсты {time}. Как обычно идут Дмитрий(МакароноВирус), Леонид(ТуманныйТор) и кто-то еще. Нажимайте + в сообщении.\n\nЖелающие 0 человек(а):",
            reply_markup=keyboard
        )

        # Закрепляем сообщение с фото
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

# Функция для обновления подписи к фото
async def update_caption(photo_message: types.Message, participants: list, callback: types.CallbackQuery, action_message: str, time: str):
    # Проверка наличия подписи
    if not photo_message.caption:
        logging.error("Ошибка: подпись к фото отсутствует")
        await callback.answer("Подпись к фото отсутствует.")
        return

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
        # Обновляем подпись к фото
        await photo_message.edit_caption(updated_text)

        # Обновляем клавиатуру
        keyboard = create_keyboard()
        await photo_message.edit_reply_markup(reply_markup=keyboard)

        await callback.answer(action_message)
        logging.info(f"Подпись обновлена: {updated_text}")
    except Exception as e:
        logging.error(f"Ошибка при обновлении подписи: {e}")
        await callback.answer("Не удалось обновить подпись. Попробуйте снова.")

# Обработчик для нажатия на кнопку "➕ Присоединиться"
@router.callback_query(lambda query: query.data.startswith("join_"))
async def handle_join_reaction(callback: types.CallbackQuery):
    username = callback.from_user.first_name
    message = callback.message

    # Получаем участников из подписи
    participants = filter_participants(message.caption)
    if callback.data == "join_plus":
        if username not in participants:
            participants.append(username)
            action_message = f"Вы присоединились, {username}!"
        else:
            action_message = f"Вы уже участвуете, {username}!"
    elif callback.data == "join_minus":
        if username in participants:
            participants.remove(username)
            action_message = f"Вы больше не участвуете, {username}."
        else:
            action_message = f"Вы не участвовали."

    # Получаем последнее сообщение с фото
    photo_message = callback.message

    if photo_message:
        # Извлекаем время из подписи
        time_match = re.search(r'Идем в инсты\s*(\d{1,2}:\d{2}|когда соберемся)', photo_message.caption)
        if time_match:
            time = time_match.group(1)
        else:
            time = "когда соберемся"
        await update_caption(photo_message, participants, callback, action_message, time)
    else:
        await callback.answer("Сообщение с фото не найдено.")
