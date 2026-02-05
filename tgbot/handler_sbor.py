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

# ==========================
# Получение имени пользователя из листа ID
# ==========================
def get_user_from_sheet(user_id: int):
    client = get_gspread_client()
    if not client:
        return None

    sheet = client.open("DareDevils").worksheet("ID")
    data = sheet.get_all_records()

    for row in data:
        if row.get('user_id') == user_id:
            return row.get('name')
    return None

# ==========================
# Получение списка разрешенных ID пользователей
# ==========================
def get_allowed_user_ids():
    client = get_gspread_client()
    if not client:
        return set()
    try:
        sheet = client.open("DareDevils").worksheet("ID")
        data = sheet.get_all_records()
        return set(int(row["id"]) for row in data if "id" in row and row["id"])
    except Exception as e:
        logging.error(f"Ошибка при получении get_allowed_user_ids(): {e}")
        return set()

# ==========================
# Создание клавиатуры
# ==========================
def create_keyboard():
    plus_button = InlineKeyboardButton(text="➕ Присоединиться", callback_data="join_plus")
    minus_button = InlineKeyboardButton(text="➖ Не участвовать", callback_data="join_minus")
    return InlineKeyboardMarkup(inline_keyboard=[[plus_button, minus_button]])

# ==========================
# Функции работы с участниками
# ==========================
def parse_participants(caption: str):
    main_participants = []
    match_main = re.search(r"Участвуют \(\d+\): ([^\n]+)", caption)
    if match_main:
        main_participants = [name.strip() for name in match_main.group(1).split(",") if name.strip()]

    bench_participants = []
    match_bench = re.search(r"Скамейка запасных \(\d+\): ([^\n]+)", caption)
    if match_bench:
        bench_participants = [name.strip() for name in match_bench.group(1).split(",") if name.strip()]

    return main_participants + bench_participants

def extract_time_from_caption(caption: str):
    time_match = re.search(r"\b\d{1,2}:\d{2}(?:-\d{1,2}:\d{2})?\b", caption)
    return time_match.group(0) if time_match else "когда соберемся"

async def update_caption(photo_message: types.Message, participants: list, callback: types.CallbackQuery,
                         action_message: str, time: str, keyboard: InlineKeyboardMarkup):
    participants = list(dict.fromkeys(participants))
    main_participants = participants[:7]
    bench_participants = participants[7:]

    header_match = re.search(r"^\s*[*_]?(.+?)\s*[*_]?[\n\r]", photo_message.caption or "")
    header = header_match.group(1) if header_match else f"Идем в {time}"

    main_text = f"Участвуют ({len(main_participants)}): {', '.join(main_participants)}"
    updated_text = (
        f"*{header}*\n\n"
        f"\u26a1\u26a1\u26a1*Нажмите \u2795 в сообщении для участия*\u26a1\u26a1\u26a1\n\n"
        f"{main_text}"
    )

    if bench_participants:
        bench_text = f"Скамейка запасных ({len(bench_participants)}): {', '.join(bench_participants)}"
        updated_text += f"\n\n{bench_text}"

    try:
        await photo_message.edit_caption(
            caption=updated_text,
            parse_mode="Markdown",
            reply_markup=keyboard
        )
        if callback:
            await callback.answer(action_message)
    except Exception as e:
        logging.error(f"Ошибка при обновлении подписи: {e}")
        if callback:
            await callback.answer("Не удалось обновить подпись. Попробуйте снова.")

# ==========================
# Обработчики кнопок ➕ и ➖
# ==========================
@router.callback_query(lambda callback: callback.data == "join_plus")
async def handle_plus_reaction(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    username = callback.from_user.first_name
    message = callback.message

    participants = parse_participants(message.caption)
    display_name = get_user_from_sheet(user_id) or username

    if display_name in participants:
        await callback.answer(f"Вы уже участвуете, {display_name}!")
        return

    participants.append(display_name)
    time = extract_time_from_caption(message.caption)
    keyboard = create_keyboard()
    await update_caption(message, participants, callback, f"Вы присоединились, {display_name}!", time, keyboard)

@router.callback_query(lambda callback: callback.data == "join_minus")
async def handle_minus_reaction(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    username = callback.from_user.first_name
    message = callback.message

    participants = parse_participants(message.caption)
    display_name = get_user_from_sheet(user_id) or username

    if display_name in participants:
        participants.remove(display_name)
    else:
        await callback.answer("Вы не участвуете.")
        return

    time = extract_time_from_caption(message.caption)
    keyboard = create_keyboard()
    await update_caption(message, participants, callback, f"Вы больше не участвуете, {display_name}.", time, keyboard)

# ==========================
# Обработчики сообщений + и -
# ==========================
@router.message(lambda message: message.text and message.text.startswith("+ "))
async def handle_plus_message(message: types.Message):
    user_id = message.from_user.id
    if user_id not in get_allowed_user_ids():
        return

    username = message.text[2:].strip()
    message_obj = message.reply_to_message
    if not message_obj or not (message_obj.caption or message_obj.text):
        return

    caption = message_obj.caption or message_obj.text
    participants = parse_participants(caption)
    if username in participants:
        await message.answer(f"{username} уже участвует!")
        return

    participants.append(username)
    time = extract_time_from_caption(caption)
    keyboard = create_keyboard()
    await update_caption(message_obj, participants, None, f"{username} присоединился!", time, keyboard)

@router.message(lambda message: message.text and message.text.startswith("- "))
async def handle_minus_message(message: types.Message):
    user_id = message.from_user.id
    if user_id not in get_allowed_user_ids():
        return

    username = message.text[2:].strip()
    message_obj = message.reply_to_message
    if not message_obj or not (message_obj.caption or message_obj.text):
        return

    caption = message_obj.caption or message_obj.text
    participants = parse_participants(caption)
    if username not in participants:
        await message.answer(f"{username} не участвует.")
        return

    participants.remove(username)
    time = extract_time_from_caption(caption)
    keyboard = create_keyboard()
    await update_caption(message_obj, participants, None, f"{username} больше не участвует.", time, keyboard)
