from aiogram import types, Router
from aiogram.filters import Command
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
import re
import logging

# Настройка логирования
logging.basicConfig(level=logging.DEBUG)

router = Router()

# Хендлер для команды /inst
@router.message(Command(commands=["inst"]))
async def fix_handler(message: types.Message):
    try:
        time_match = re.search(r"(\d{1,2}:\d{2})", message.text)
        time = time_match.group(1) if time_match else "когда соберемся"
        photo_url = "https://battleclub.space/uploads/monthly_2022_07/baylor.jpg.02e0df864753bf47b1ef76303b993a1d.jpg"
        keyboard = create_keyboard()
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
        await message.chat.pin_message(sent_message.message_id)
        logging.info(f"Сообщение отправлено и закреплено с id: {sent_message.message_id}")
    except Exception as e:
        logging.error(f"Ошибка при обработке команды /inst: {e}")
        await message.answer("Произошла ошибка. Попробуйте снова.")

# Функция для парсинга текста и получения списка участников
def parse_participants(caption: str):
    # Удаляем слово "Желающие:" из текста
    cleaned_caption = re.sub(r"\bЖелающие:\b", "", caption)
    
    # Находим строку с участниками
    match = re.search(r"Идут \d+ человек: (.+)", cleaned_caption, flags=re.DOTALL)
    
    if match:
        # Разбиваем список участников по запятым и очищаем
        participants = [name.strip() for name in match.group(1).split(",") if name.strip()]
        return participants

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

    # Логируем общее количество участников
    logging.debug(f"Идут: {len(main_participants)} человек, Желающие: {len(extra_participants)} человек")

    if not participants:
        # Если список участников пуст
        updated_text = (
            f"*Идем в инсты {time}*. Как обычно идут Дмитрий(МакароноВирус), Леонид(ТуманныйТор) и кто-то еще. "
            f"*Нажмите ➕ в сообщении для участия*."
        )
    else:
        # Формируем текст обновления
        main_text = ", ".join(main_participants)
        extra_text = ", ".join(extra_participants)
        updated_text = (
            f"*Идем в инсты {time}*. Как обычно идут Дмитрий(МакароноВирус), Леонид(ТуманныйТор) и кто-то еще. "
            f"*Нажмите ➕ в сообщении для участия*.\n\n"
            f"Идут {len(main_participants)} человек: *{main_text}*"
        )
        if extra_participants:
            updated_text += f"\nЖелающие: {extra_text}"

    # Проверяем, нужно ли обновлять сообщение
    if photo_message.caption != updated_text or photo_message.reply_markup != keyboard:
        try:
            await photo_message.edit_caption(caption=updated_text, parse_mode="Markdown", reply_markup=keyboard)
            await callback.answer(action_message)
        except Exception as e:
            logging.error(f"Ошибка при обновлении подписи: {e}")
            await callback.answer("Не удалось обновить подпись. Попробуйте снова.")
    else:
        logging.debug("Изменений в сообщении нет, обновление пропущено.")
        await callback.answer(action_message)

# Обработчик для нажатия на кнопку "➕ Присоединиться"
@router.callback_query(lambda callback: callback.data == "join_plus")
async def handle_plus_reaction(callback: types.CallbackQuery):
    username = callback.from_user.first_name
    message = callback.message

    participants = parse_participants(message.caption)

    logging.debug(f"[До добавления] Участники: {participants}")

    if username in participants:
        await callback.answer(f"Вы уже участвуете, {username}!")
        return

    participants.append(username)
    logging.debug(f"[После добавления] Участники: {participants}")

    time = extract_time_from_caption(message.caption)
    keyboard = create_keyboard()
    await update_caption(message, participants, callback, f"Вы присоединились, {username}!", time, keyboard)

# Обработчик для нажатия на кнопку "➖ Не участвовать"
@router.callback_query(lambda callback: callback.data == "join_minus")
async def handle_minus_reaction(callback: types.CallbackQuery):
    username = callback.from_user.first_name
    message = callback.message

    participants = parse_participants(message.caption)

    logging.debug(f"[До удаления] Участники: {participants}")

    if username in participants:
        participants.remove(username)
    else:
        await callback.answer("Вы не участвуете.")
        return

    logging.debug(f"[После удаления] Участники: {participants}")

    time = extract_time_from_caption(message.caption)
    keyboard = create_keyboard()
    await update_caption(message, participants, callback, f"Вы больше не участвуете, {username}.", time, keyboard)
    
# Функция для создания клавиатуры
def create_keyboard():
    plus_button = InlineKeyboardButton(text="➕ Присоединиться", callback_data="join_plus")
    minus_button = InlineKeyboardButton(text="➖ Не участвовать", callback_data="join_minus")
    return InlineKeyboardMarkup(inline_keyboard=[[plus_button, minus_button]])
