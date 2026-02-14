import os
import re
import logging
import asyncio
from aiogram import types, Router
from aiogram.filters import Command
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from tgbot.sheets.take_from_sheet import (
    get_user_from_sheet,
    get_allowed_user_ids,
    get_column_data_from_autosbor,
    get_bal_data,
    get_inn_data,
    get_ork_data,
    get_inst_data, 
    get_name_username_dict
)

logging.basicConfig(level=logging.DEBUG)
router = Router()

# ==========================
# Markdown escape (aiogram v3 safe)
# ==========================
def escape_md(text: str) -> str:
    return re.sub(r'([_*\[\]()~`>#+\-=|{}.!])', r'\\\1', text)

# ==========================
# Асинхронный вызов блокирующих функций
# ==========================
async def safe_fetch(func, *args):
    try:
        return await asyncio.to_thread(func, *args)
    except Exception as e:
        logging.exception(f"Ошибка при вызове {func.__name__}: {e}")
        return None

# ==========================
# EVENT MAP
# ==========================
EVENT_MAP = {
    "bal": get_bal_data,
    "inn": get_inn_data,
    "ork": get_ork_data,
    "inst": get_inst_data,
}

# ==========================
# Клавиатура
# ==========================
def create_keyboard():
    plus_button = InlineKeyboardButton(text="➕ Присоединиться", callback_data="join_plus")
    minus_button = InlineKeyboardButton(text="➖ Не участвовать", callback_data="join_minus")
    return InlineKeyboardMarkup(inline_keyboard=[[plus_button, minus_button]])

# ==========================
# Парсинг участников
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

# ==========================
# Универсальная функция для добавления/удаления участников
# ==========================
async def modify_participants(message_obj: types.Message, username: str, action: str, callback: types.CallbackQuery = None):
    participants = parse_participants(message_obj.caption or message_obj.text)
    if action == "add":
        if username in participants:
            if callback:
                await callback.answer("Вы уже участвуете!")
            return
        participants.append(username)
        msg_text = f"{username} добавлен!" if not callback else f"Вы присоединились, {username}!"
    elif action == "remove":
        if username not in participants:
            if callback:
                await callback.answer("Вы не участвуете.")
            return
        participants.remove(username)
        msg_text = f"{username} удален!" if not callback else f"Вы больше не участвуете, {username}."
    else:
        return
    time = extract_time_from_caption(message_obj.caption or message_obj.text)
    keyboard = create_keyboard()
    await update_caption(message_obj, participants, callback, msg_text, time, keyboard)

# ==========================
# Обновление подписи
# ==========================
async def update_caption(photo_message: types.Message, participants: list,
                         callback: types.CallbackQuery,
                         action_message: str, time: str,
                         keyboard: InlineKeyboardMarkup):

    participants = list(dict.fromkeys(participants))
    main_participants = participants[:7]
    bench_participants = participants[7:]

    header_match = re.search(r"^\s*[*_]?(.+?)\s*[*_]?[\n\r]", photo_message.caption or "")
    header = header_match.group(1) if header_match else f"Идем в {time}"

    main_text = f"Участвуют ({len(main_participants)}): {', '.join(main_participants)}"

    updated_text = (
        f"*{escape_md(header)}*\n\n"
        f"⚡⚡⚡*Нажмите ➕ в сообщении для участия*⚡⚡⚡\n\n"
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
        logging.error(f"Ошибка при обновлении подписи для сообщения {photo_message.message_id}: {e}")
        if callback:
            await callback.answer("Не удалось обновить подпись.")

# ==========================
# Отправка события
# ==========================
async def send_event_photo(message: types.Message, photo_url: str, header_prefix: str):
    keyboard = create_keyboard()
    text = message.text or ""
    time_match = re.search(r"\b\d{1,2}:\d{2}(?:-\d{1,2}:\d{2})?\b", text)
    time = time_match.group(0) if time_match else "когда соберемся"
    numbers = re.findall(r"\b\d+\b", text)
    col_indexes = [int(n) for n in numbers]

    user_id = message.from_user.id
    allowed_ids = await safe_fetch(get_allowed_user_ids)

    participants = []
    if user_id in allowed_ids and col_indexes:
        for col in col_indexes:
            column_data = await safe_fetch(get_column_data_from_autosbor, col)
            if column_data:
                participants.extend(column_data)

    participants = list(dict.fromkeys(participants))
    header_text = escape_md(f"{header_prefix} {time}")

    caption = (
        f"*{header_text}*\n\n"
        f"⚡⚡⚡*Нажмите ➕ в сообщении для участия*⚡⚡⚡\n\n"
    )

    if participants:
        caption += f"Участвуют ({len(participants)}): {', '.join(participants)}"
    else:
        caption += "Участвуют (0): "

    try:
        if photo_url:
            sent_message = await message.bot.send_photo(
                chat_id=message.chat.id,
                photo=photo_url,
                caption=caption,
                parse_mode="Markdown",
                reply_markup=keyboard
            )
        else:
            sent_message = await message.answer(
                caption,
                parse_mode="Markdown",
                reply_markup=keyboard
            )

        try:
            await message.chat.pin_message(sent_message.message_id)
        except Exception as e:
            logging.warning(f"Не удалось закрепить сообщение {sent_message.message_id}: {e}")

    except Exception as e:
        logging.error(f"Ошибка отправки события: {e}")

    try:
        await message.delete()
    except Exception:
        pass

# ==========================
# Универсальный хендлер команд
# ==========================
@router.message(Command(*EVENT_MAP.keys()))
async def event_handler(message: types.Message):
    command = message.text.split()[0].replace("/", "")
    handler_func = EVENT_MAP.get(command)
    if not handler_func:
        return

    text, media_url = await safe_fetch(handler_func)
    await send_event_photo(message, media_url, text)

# ==========================
# Callback ➕ / ➖
# ==========================
@router.callback_query(lambda c: c.data in ["join_plus", "join_minus"])
async def handle_reaction(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    username = callback.from_user.first_name
    message = callback.message
    display_name = await safe_fetch(get_user_from_sheet, user_id) or username
    action = "add" if callback.data == "join_plus" else "remove"
    await modify_participants(message, display_name, action, callback)

# ==========================
# Ручное добавление / удаление участников через сообщение
# ==========================
@router.message(lambda message: message.text and message.text.startswith(("+ ", "- ")))
async def handle_manual_message(message: types.Message):
    user_id = message.from_user.id
    allowed_ids = await safe_fetch(get_allowed_user_ids)
    if user_id not in allowed_ids:
        return

    username = message.text[2:].strip()
    message_obj = message.reply_to_message
    if not message_obj or not (message_obj.caption or message_obj.text):
        return

    action = "add" if message.text.startswith("+ ") else "remove"
    await modify_participants(message_obj, username, action)
    try:
        await message.delete()
    except Exception:
        pass

# ==========================
# Callback "го" с тегами участников
# ==========================
@router.message(lambda message: message.text and message.text.lower().startswith("го") and message.reply_to_message)
async def handle_go_numbered(message: types.Message):
    user_id = message.from_user.id
    allowed_ids = await safe_fetch(get_allowed_user_ids)
    if user_id not in allowed_ids:
        return

    reply_msg = message.reply_to_message
    caption = reply_msg.caption or reply_msg.text or ""
    if not caption:
        return

    participants = parse_participants(caption)
    if not participants:
        await message.answer("Не удалось найти участников в сообщении.")
        return

    name_username = await safe_fetch(get_name_username_dict)
    if not name_username:
        await message.answer("Не удалось получить данные из Google Sheets.")
        return

    numbers = re.findall(r"\d+", message.text)
    indexes = sorted(set([int(n)-1 for n in numbers if 0 < int(n) <= len(participants)])) if numbers else range(len(participants))
    selected = [participants[i] for i in indexes]

    tg_usernames = [f"@{name_username.get(name)}" if name_username.get(name) and name_username.get(name).lower() != "unknown" else name for name in selected]

    if not tg_usernames:
        await message.answer("Не удалось сопоставить участников с их Telegram-никами.")
        return

    await message.answer(f"Собираемся: {', '.join(tg_usernames)}")
    try:
        await message.delete()
    except Exception:
        pass
