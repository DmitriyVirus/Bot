import re
import logging
from aiogram import types, Router
from aiogram.filters import Command
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

# Настройка логирования
logging.basicConfig(level=logging.DEBUG)

router = Router()

# Словарь пользовательских отображений
USER_MAPPING = {
    559273200: "Дмитрий(маКароноВирус)",
    638155657: "Вячеслав(DumSpiroSpero)",
    1141764502: "Аня(Elisan)",
    1034353655: "Вячеслав(Saela)",
    809946596: "Кристина(СерыеГлазки)",
    5263336963: "Леонид(ТуманныйТор)",
    1687314254: "Игорь(ФунтАпельсинов)",
    1207400705: "Евгений(ХныкКи)",
    1705787763: "Александр(Piuv)",
    442475543: "Александр(Клаар)",
    923927066: "Михаил(Remorse)",
}

# Хендлер для команды /inst
@router.message(Command(commands=["inst"]))
async def fix_handler(message: types.Message):
    try:
        time_match = re.search(r"(\d{1,2}:\d{2})", message.text)
        time = time_match.group(1) if time_match else "когда соберемся"
        photo_url = "https://battleclub.space/uploads/monthly_2022_07/baylor.jpg.02e0df864753bf47b1ef76303b993a1d.jpg"
        keyboard = create_keyboard()

        # Добавляем фиксированных участников в начало списка
        initial_participants = ["Дмитрий(маКароноВирус)", "Леонид(ТуманныйТор)"]
        caption = (
            f"\u2620\ufe0f*Идем в инсты {time}*.\u2620\ufe0f\n\n"
            f"\u26a1\u26a1\u26a1*Нажмите \u2795 в сообщении для участия*\u26a1\u26a1\u26a1\n\n"
            f"Участвуют: {', '.join(initial_participants)}"
        )

        sent_message = await message.bot.send_photo(
            chat_id=message.chat.id,
            photo=photo_url,
            caption=caption,
            parse_mode="Markdown",
            reply_markup=keyboard
        )

        await message.chat.pin_message(sent_message.message_id)
        logging.info(f"Сообщение отправлено и закреплено с id: {sent_message.message_id}")
    except Exception as e:
        logging.error(f"Ошибка при обработке команды /inst: {e}")
        await message.answer("Произошла ошибка. Попробуйте снова.")

# Функция для разбора участников
def parse_participants(caption: str):
    match = re.search(r"Участвуют: (.+)", caption, flags=re.DOTALL)
    if match:
        return [name.strip() for name in match.group(1).split(",") if name.strip()]
    return []

# Функция для извлечения времени из подписи
def extract_time_from_caption(caption: str):
    time_match = re.search(r"Идем в инсты\s*(\d{1,2}:\d{2}|когда соберемся)", caption)
    return time_match.group(1) if time_match else "когда соберемся"

# Функция для обновления подписи к фото
async def update_caption(photo_message: types.Message, participants: list, callback: types.CallbackQuery, action_message: str, time: str, keyboard: InlineKeyboardMarkup):
    """
    Обновляет подпись с учетом фиксированных участников.
    """
    # Убираем дубли
    participants = list(dict.fromkeys(participants))

    # Формируем текст
    main_text = ", ".join(participants)
    updated_text = (
        f"\u2620\ufe0f*Идем в инсты {time}*.\u2620\ufe0f\n\n"
        f"\u26a1\u26a1\u26a1*Нажмите \u2795 в сообщении для участия*.\u26a1\u26a1\u26a1\n\n"
        f"Участвуют: {main_text}"
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
    user_id = callback.from_user.id
    username = callback.from_user.first_name
    message = callback.message

    participants = parse_participants(message.caption)
    logging.debug(f"[До добавления] Участники: {participants}")

    # Проверяем имя из таблицы
    display_name = USER_MAPPING.get(user_id, username)

    # Проверка на дублирование
    if display_name in participants:
        await callback.answer(f"Вы уже участвуете, {display_name}!")
        return

    # Добавляем нового участника
    participants.append(display_name)

    # Обновляем текст
    time = extract_time_from_caption(message.caption)
    keyboard = create_keyboard()
    await update_caption(message, participants, callback, f"Вы присоединились, {display_name}!", time, keyboard)

# Обработчик для нажатия на кнопку "➖ Не участвовать"
@router.callback_query(lambda callback: callback.data == "join_minus")
async def handle_minus_reaction(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    username = callback.from_user.first_name
    message = callback.message

    participants = parse_participants(message.caption)
    logging.debug(f"[До удаления] Участники: {participants}")

    # Проверяем имя из таблицы
    display_name = USER_MAPPING.get(user_id, username)

    if display_name in participants:
        participants.remove(display_name)
        logging.debug(f"[После удаления] Участники: {participants}")
    else:
        await callback.answer("Вы не участвуете.")
        return

    # Обновляем текст
    time = extract_time_from_caption(message.caption)
    keyboard = create_keyboard()
    await update_caption(message, participants, callback, f"Вы больше не участвуете, {display_name}.", time, keyboard)

# Функция для создания клавиатуры
def create_keyboard():
    plus_button = InlineKeyboardButton(text="➕ Присоединиться", callback_data="join_plus")
    minus_button = InlineKeyboardButton(text="➖ Не участвовать", callback_data="join_minus")
    return InlineKeyboardMarkup(inline_keyboard=[[plus_button, minus_button]])
