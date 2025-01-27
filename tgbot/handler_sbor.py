import os
import re
import logging
from aiogram import types, Router
from aiogram.filters import Command
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from tgbot.gspread_client import get_gspread_client

# Настройка логирования
logging.basicConfig(level=logging.DEBUG)

router = Router()

# Функция для создания клавиатуры
def create_keyboard():
    plus_button = InlineKeyboardButton(text="➕ Присоединиться", callback_data="join_plus")
    minus_button = InlineKeyboardButton(text="➖ Не участвовать", callback_data="join_minus")
    return InlineKeyboardMarkup(inline_keyboard=[[plus_button, minus_button]])

def get_user_from_sheet(user_id: int):
    client = get_gspread_client()  # Получаем клиент для Google Sheets
    if not client:
        return None

    sheet = client.open("ourid").sheet1  # Получаем первую таблицу
    data = sheet.get_all_records()  # Получаем все данные из таблицы

    # Ищем пользователя по user_id
    for row in data:
        if row.get('user_id') == user_id:
            return row.get('name')  # Возвращаем имя из столбца 'name'

    return None  # Если пользователя не нашли

# Обновлённая функция для извлечения алиасов из Google Sheets
def get_user_from_alias_or_name(user_input: str):
    aliases = get_aliases_from_sheet()  # Получаем список алиасов
    client = get_gspread_client()  # Получаем клиент для Google Sheets
    if not client:
        return None

    sheet = client.open("ourid").sheet1  # Получаем первую таблицу
    data = sheet.get_all_records()  # Получаем все данные из таблицы

    # Проверяем, является ли введённое имя алиасом
    for row in data:
        aliases_column = row.get('aliases', '')
        name = row.get('name')

        # Если нашли соответствие по алиасу, возвращаем имя
        if aliases_column:
            alias_list = aliases_column.split(",")
            if user_input in alias_list:
                return name

    # Если не нашли алиас, возвращаем саму строку, возможно это нормальное имя
    return user_input.strip()

# Хендлер для команды /inst
@router.message(Command(commands=["inst"]))
async def fix_handler(message: types.Message):
    try:
        time_match = re.search(r"(\d{1,2}:\d{2})", message.text)
        time = time_match.group(1) if time_match else "когда соберемся"
        photo_url = "https://battleclub.space/uploads/monthly_2022_07/baylor.jpg.02e0df864753bf47b1ef76303b993a1d.jpg"
        keyboard = create_keyboard()
        
        caption = (
            f"\u2620\ufe0f*Идем в инсты {time}*.\u2620\ufe0f\n\n"
            f"\u26a1\u26a1\u26a1*Нажмите \u2795 в сообщении для участия*\u26a1\u26a1\u26a1\n\n"
            f"Участвуют (2): Дмитрий(маКароноВирус), Леонид(ТуманныйТор)"
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

# Функция для разбора участников
def parse_participants(caption: str):
    logging.debug(f"Исходная подпись:\n{caption}")

    # Извлекаем основную часть участников
    main_participants = []
    match_main = re.search(r"Участвуют \(\d+\): ([^\n]+)", caption)
    if match_main:
        main_participants = [
            name.strip() for name in match_main.group(1).split(",") if name.strip()
        ]

    logging.debug(f"Основной список участников: {main_participants}")

    # Извлекаем скамейку запасных
    bench_participants = []
    match_bench = re.search(r"Скамейка запасных \(\d+\): ([^\n]+)", caption)
    if match_bench:
        bench_participants = [
            name.strip() for name in match_bench.group(1).split(",") if name.strip()
        ]

    logging.debug(f"Скамейка запасных: {bench_participants}")

    # Объединяем оба списка
    participants = main_participants + bench_participants
    logging.debug(f"Общий список участников: {participants}")
    return participants

# Функция для извлечения времени из подписи
def extract_time_from_caption(caption: str):
    time_match = re.search(r"Идем в инсты\s*(\d{1,2}:\d{2}|когда соберемся)", caption)
    return time_match.group(1) if time_match else "когда соберемся"

# Функция для обновления подписи к фото
async def update_caption(photo_message: types.Message, participants: list, callback: types.CallbackQuery, action_message: str, time: str, keyboard: InlineKeyboardMarkup):
    participants = list(dict.fromkeys(participants))

    # Основной список участников и скамейка запасных
    main_participants = participants[:7]
    bench_participants = participants[7:]

    # Формируем текст
    main_text = f"Участвуют ({len(main_participants)}): {', '.join(main_participants)}"
    updated_text = (
        f"\u2620\ufe0f*Идем в инсты {time}*.\u2620\ufe0f\n\n"
        f"\u26a1\u26a1\u26a1*Нажмите \u2795 в сообщении для участия*.\u26a1\u26a1\u26a1\n\n"
        f"{main_text}"
    )
    if bench_participants:
        bench_text = f"Скамейка запасных ({len(bench_participants)}): {', '.join(bench_participants)}"
        updated_text += f"\n\n{bench_text}"

    try:
        await photo_message.edit_caption(caption=updated_text, parse_mode="Markdown", reply_markup=keyboard)
        await callback.answer(action_message)
        if callback:
            await callback.answer(action_message)
    except Exception as e:
        logging.error(f"Ошибка при обновлении подписи: {e}")

# Обработчик для нажатия на кнопку "➕ Присоединиться"
@router.callback_query(lambda callback: callback.data == "join_plus")
async def handle_plus_reaction(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    username = callback.from_user.first_name  # По умолчанию, используем first_name
    message = callback.message

    participants = parse_participants(message.caption)
    logging.debug(f"[До добавления] Участники: {participants}")

    # Получаем имя пользователя из Google Sheets
    display_name = get_user_from_sheet(user_id) or username  # Используем Google Sheets, если не нашли - fallback на first_name

    if display_name in participants:
        return  # Убираем ответ бота

    participants.append(display_name)
    logging.debug(f"[После добавления] Участники: {participants}")

    time = extract_time_from_caption(message.caption)
    keyboard = create_keyboard()
    await update_caption(message, participants, callback, f"Вы присоединились, {display_name}!", time, keyboard)

# Обработчик для нажатия на кнопку "➖ Не участвовать"
@router.callback_query(lambda callback: callback.data == "join_minus")
async def handle_minus_reaction(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    username = callback.from_user.first_name  # По умолчанию, используем first_name
    message = callback.message

    participants = parse_participants(message.caption)
    logging.debug(f"[До удаления] Участники: {participants}")

    # Получаем имя пользователя из Google Sheets
    display_name = get_user_from_sheet(user_id) or username  # Используем Google Sheets, если не нашли - fallback на first_name

    if display_name in participants:
        participants.remove(display_name)
        logging.debug(f"[После удаления] Участники: {participants}")
    else:
        return  # Убираем ответ бота
        
    time = extract_time_from_caption(message.caption)
    keyboard = create_keyboard()
    await update_caption(message, participants, callback, f"Вы больше не участвуете, {display_name}.", time, keyboard)

# Обработчик для ввода текста
@router.message()
async def handle_user_text(message: types.Message):
    try:
        user_input = message.text.strip()  # Убираем пробелы вокруг текста
        message_with_photo = message.reply_to_message  # Проверяем, отвечает ли пользователь на сообщение с фото

        if not message_with_photo or not message_with_photo.caption:
            return

        participants = parse_participants(message_with_photo.caption)  # Текущий список участников
        logging.debug(f"Текущий список участников: {participants}")

        # Добавление участника
        if user_input.startswith("+"):
            name_to_add = user_input[1:].strip()  # Убираем '+' и пробелы
            if not name_to_add:
                return

            # Получаем имя пользователя из Google Sheets, проверяя алиасы
            name_to_add = get_user_from_alias_or_name(name_to_add)

            if name_to_add in participants:
                return  # Убираем ответ бота
            else:
                participants.append(name_to_add)

        # Удаление участника
        elif user_input.startswith("-"):
            name_to_remove = user_input[1:].strip()  # Убираем '-' и пробелы
            if not name_to_remove:
                return

            # Получаем имя пользователя из Google Sheets, проверяя алиасы
            name_to_remove = get_user_from_alias_or_name(name_to_remove)

            if name_to_remove in participants:
                participants.remove(name_to_remove)
            else:
                return

        else:
            return

        # Обновляем подпись сообщения
        time = extract_time_from_caption(message_with_photo.caption)  # Извлекаем время из подписи
        keyboard = create_keyboard()  # Создаем клавиатуру
        await update_caption(
            message_with_photo, participants, None, "Список обновлен!", time, keyboard
        )

    except Exception as e:
        logging.error(f"Ошибка при обработке текста от пользователя: {e}") 
