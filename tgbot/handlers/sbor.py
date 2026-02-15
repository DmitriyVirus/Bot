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
# Markdown escape (только для заголовка)
# ==========================
def escape_md(text: str) -> str:
    return re.sub(r'([_*\[\]()~`>#+\-=|{}.!])', r'\\\1', text)

# ==========================
# Асинхронный safe fetch для блокирующих вызовов
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
    main = re.findall(r"Участвуют \(\d+\): ([^\n]+)", caption)
    bench = re.findall(r"Скамейка запасных \(\d+\): ([^\n]+)", caption)
    participants = []
    if main:
        participants += [n.strip() for n in main[0].split(",") if n.strip()]
    if bench:
        participants += [n.strip() for n in bench[0].split(",") if n.strip()]
    return participants

def extract_time(caption: str):
    m = re.search(r"\b\d{1,2}:\d{2}(?:-\d{1,2}:\d{2})?\b", caption)
    return m.group(0) if m else "когда соберемся"

# ==========================
# Универсальная модификация участников
# ==========================
async def modify_participants(msg: types.Message, username: str, action: str, callback: types.CallbackQuery = None):
    participants = parse_participants(msg.caption or msg.text)
    if action == "add":
        if username in participants:
            if callback: await callback.answer("Вы уже участвуете!")
            return
        participants.append(username)
        msg_text = f"Вы присоединились, {username}!" if callback else f"{username} добавлен!"
    elif action == "remove":
        if username not in participants:
            if callback: await callback.answer("Вы не участвуете.")
            return
        participants.remove(username)
        msg_text = f"Вы больше не участвуете, {username}." if callback else f"{username} удален!"
    else:
        return

    await update_caption(msg, participants, msg_text, callback)


# ==========================
# Обновление подписи (единственная функция)
# ==========================
async def update_caption(msg: types.Message, participants: list, msg_text: str, callback: types.CallbackQuery = None):
    participants = list(dict.fromkeys(participants))
    main = participants[:7]
    bench = participants[7:]

    # Сохраняем заголовок отдельно
    caption_orig = msg.caption or msg.text or ""
    # Если это уже редактированное сообщение, берем первую строку до \n\n как заголовок
    header_line = caption_orig.split("\n\n")[0] if "\n\n" in caption_orig else caption_orig
    # Убираем лишние символы Markdown и знаки времени
    header = re.sub(r"\b\d{1,2}:\d{2}(?:-\d{1,2}:\d{2})?\b", "", header_line).strip()
    header = escape_md(header) or msg_text

    # Вытаскиваем время
    time = extract_time(caption_orig)

    # Формируем текст
    text = f"*{header}* {time}\n\n⚡⚡⚡*Нажмите ➕ в сообщении для участия*⚡⚡⚡\n\n"
    text += f"Участвуют ({len(main)}): {', '.join(main)}"
    if bench:
        text += f"\n\nСкамейка запасных ({len(bench)}): {', '.join(bench)}"

    keyboard = create_keyboard()
    try:
        await msg.edit_caption(caption=text, parse_mode="Markdown", reply_markup=keyboard)
        if callback: await callback.answer(msg_text)
    except Exception as e:
        logging.error(f"Ошибка обновления подписи {msg.message_id}: {e}")
        if callback: await callback.answer("Не удалось обновить подпись.")


# ==========================
# Отправка события
# ==========================
async def send_event_photo(message: types.Message, photo_url: str, header_prefix: str):
    text_msg = message.text or ""
    time = extract_time(text_msg)
    numbers = [int(n) for n in re.findall(r"\b\d+\b", text_msg)]
    user_id = message.from_user.id
    allowed_ids = await safe_fetch(get_allowed_user_ids)
    participants = []

    if user_id in allowed_ids and numbers:
        for col in numbers:
            data = await safe_fetch(get_column_data_from_autosbor, col)
            if data: participants.extend(data)
    participants = list(dict.fromkeys(participants))

    header_text = escape_md(header_prefix)
    caption = f"*{header_text}* {extract_time(message.text or '')}\n\n⚡⚡⚡*Нажмите ➕ в сообщении для участия*⚡⚡⚡\n\n"
    caption += f"Участвуют ({len(participants)}): {', '.join(participants)}" if participants else "Участвуют (0): "

    keyboard = create_keyboard()
    try:
        sent = await (message.bot.send_photo(chat_id=message.chat.id, photo=photo_url, caption=caption,
                                             parse_mode="Markdown", reply_markup=keyboard)
                      if photo_url else message.answer(caption, parse_mode="Markdown", reply_markup=keyboard))
        try: await message.chat.pin_message(sent.message_id)
        except Exception as e: logging.warning(f"Не удалось закрепить {sent.message_id}: {e}")
    except Exception as e:
        logging.error(f"Ошибка отправки события: {e}")
    finally:
        try: await message.delete()
        except Exception: pass

# ==========================
# Универсальный хендлер команд
# ==========================
@router.message(Command(*EVENT_MAP.keys()))
async def event_handler(message: types.Message):
    command = message.text.split()[0].replace("/", "")
    handler_func = EVENT_MAP.get(command)
    if not handler_func: return
    text, media_url = await safe_fetch(handler_func)
    await send_event_photo(message, media_url, text)

# ==========================
# Callback ➕ / ➖
# ==========================
@router.callback_query(lambda c: c.data in ["join_plus", "join_minus"])
async def handle_reaction(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    username = callback.from_user.first_name
    display_name = await safe_fetch(get_user_from_sheet, user_id) or username
    action = "add" if callback.data == "join_plus" else "remove"
    await modify_participants(callback.message, display_name, action, callback)

# ==========================
# Ручное + / - через сообщение
# ==========================
@router.message(lambda m: m.text and m.text.startswith(("+ ", "- ")))
async def handle_manual_message(message: types.Message):
    allowed_ids = await safe_fetch(get_allowed_user_ids)
    if message.from_user.id not in allowed_ids: return
    obj = message.reply_to_message
    if not obj or not (obj.caption or obj.text): return
    action = "add" if message.text.startswith("+ ") else "remove"
    await modify_participants(obj, message.text[2:].strip(), action)
    try: await message.delete()
    except Exception: pass

# ==========================
# "го" с тегами
# ==========================
@router.message(lambda m: m.text and m.text.lower().startswith("го") and m.reply_to_message)
async def handle_go_numbered(message: types.Message):
    allowed_ids = await safe_fetch(get_allowed_user_ids)
    if message.from_user.id not in allowed_ids: return
    reply_msg = message.reply_to_message
    caption = reply_msg.caption or reply_msg.text or ""
    participants = parse_participants(caption)
    if not participants:
        await message.answer("Не удалось найти участников.")
        return
    name_username = await safe_fetch(get_name_username_dict)
    if not name_username:
        await message.answer("Не удалось получить данные из Google Sheets.")
        return
    numbers = re.findall(r"\d+", message.text)
    indexes = sorted(set([int(n)-1 for n in numbers if 0 < int(n) <= len(participants)])) if numbers else range(len(participants))
    selected = [participants[i] for i in indexes]
    tg_usernames = [f"@{name_username.get(n)}" if name_username.get(n) and name_username.get(n).lower() != "unknown" else n for n in selected]
    if not tg_usernames:
        await message.answer("Не удалось сопоставить участников с Telegram.")
        return
    await message.answer(f"Собираемся: {', '.join(tg_usernames)}")
    try: await message.delete()
    except Exception: pass
