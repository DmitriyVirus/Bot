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
        # Попытка извлечь время из текста
        time_match = re.search(r"(\d{1,2}:\d{2})", message.text)
        time = time_match.group(1) if time_match else "когда соберемся"
        # Фото для отправки
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
        logging.error(f"Ошибка при обработке команды /inst: {e}")
        await message.answer("Произошла ошибка. Попробуйте снова.")

# Функция для парсинга текста и получения списка участников
def filter_participants(caption: str):
    match = re.search(r"Идут \d+ человек: (.+)", caption, flags=re.DOTALL)
    if match:
        return [name.strip() for name in match.group(1).split(",") if name.strip()]
    return []

# Функция для извлечения списка "Желающих"
def filter_extra_participants(caption: str):
    match = re.search(r"Желающие \d+: (.+)", caption, flags=re.DOTALL)
    if match:
        return [name.strip() for name in match.group(1).split(",") if name.strip()]
    return []

# Функция для извлечения времени из подписи
def extract_time_from_caption(caption: str):
    time_match = re.search(r"Идем в инсты\s*(\d{1,2}:\d{2}|когда соберемся)", caption)
    return time_match.group(1) if time_match else "когда соберемся"

# Функция для обновления подписи к фото
async def update_caption(photo_message: types.Message, participants: list, callback: types.CallbackQuery, action_message: str, time: str, keyboard: InlineKeyboardMarkup):
    main_participants = participants[:5]
    extra_participants = participants[5:]
    participants_count = len(participants)

    if participants_count == 0:
        updated_text = (
            f"*Идем в инсты {time}*. Как обычно идут Дмитрий(МакароноВирус), Леонид(ТуманныйТор) и кто-то еще. "
            f"*Нажмите ➕ в сообщении для участия*."
        )
    elif participants_count <= 5:
        joined_users = ", ".join(main_participants)
        updated_text = (
            f"*Идем в инсты {time}*. Как обычно идут Дмитрий(МакароноВирус), Леонид(ТуманныйТор) и кто-то еще. "
            f"*Нажмите ➕ в сообщении для участия*.\n\nИдут {participants_count} человек: *{joined_users}*"
        )
    else:
        main_text = ", ".join(main_participants)
        extra_text = f"Желающие {len(extra_participants)}: " + ", ".join(extra_participants)
        updated_text = (
            f"*Идем в инсты {time}*. Как обычно идут Дмитрий(МакароноВирус), Леонид(ТуманныйТор) и кто-то еще. "
            f"*Нажмите ➕ в сообщении для участия*.\n\n"
            f"Идут {len(main_participants)} человек: *{main_text}*\n"
            f"{extra_text}" if extra_participants else ""
        )

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

    main_participants = filter_participants(message.caption)
    extra_participants = filter_extra_participants(message.caption)

    if username in main_participants or username in extra_participants:
        await callback.answer(f"Вы уже участвуете, {username}!")
        return

    if len(main_participants) < 5:
        main_participants.append(username)
    else:
        extra_participants.append(username)

    time = extract_time_from_caption(message.caption)
    keyboard = create_keyboard()
    await update_caption(message, main_participants + extra_participants, callback, f"Вы присоединились, {username}!", time, keyboard)

# Обработчик для нажатия на кнопку "➖ Не участвовать"
@router.callback_query(lambda callback: callback.data == "join_minus")
async def handle_minus_reaction(callback: types.CallbackQuery):
    username = callback.from_user.first_name
    message = callback.message

    main_participants = filter_participants(message.caption)
    extra_participants = filter_extra_participants(message.caption)

    if username in main_participants:
        main_participants.remove(username)
        if extra_participants:
            # Перемещаем первого из "Желающих" в "Идут"
            main_participants.append(extra_participants.pop(0))
    elif username in extra_participants:
        extra_participants.remove(username)
    else:
        await callback.answer("Вы не участвуете.")
        return

    time = extract_time_from_caption(message.caption)
    keyboard = create_keyboard()
    await update_caption(message, main_participants + extra_participants, callback, f"Вы больше не участвуете, {username}.", time, keyboard)

# Функция для создания клавиатуры
def create_keyboard():
    plus_button = InlineKeyboardButton(text="➕ Присоединиться", callback_data="join_plus")
    minus_button = InlineKeyboardButton(text="➖ Не участвовать", callback_data="join_minus")
    return InlineKeyboardMarkup(inline_keyboard=[[plus_button, minus_button]])
