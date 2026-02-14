import os
import re
import logging
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
    get_inst_data
)

logging.basicConfig(level=logging.DEBUG)
router = Router()

# ==========================
# Markdown escape (aiogram v3 safe)
# ==========================
def escape_md(text: str) -> str:
    return re.sub(r'([_*\[\]()~`>#+\-=|{}.!])', r'\\\1', text)


# ==========================
# EVENT MAP (универсальный хендлер)
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
        f"*{header}*\n\n"
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
        logging.error(f"Ошибка при обновлении подписи: {e}")
        if callback:
            await callback.answer("Не удалось обновить подпись.")


# ==========================
# Отправка события
# ==========================
async def send_event_photo(message: types.Message, photo_url: str, header_prefix: str):

    keyboard = create_keyboard()
    time_match = re.search(r"\b\d{1,2}:\d{2}(?:-\d{1,2}:\d{2})?\b", message.text or "")
    time = time_match.group(0) if time_match else "когда соберемся"

    header_text = escape_md(f"{header_prefix} {time}")
    caption = (
        f"*{header_text}*\n\n"
        f"⚡⚡⚡*Нажмите ➕ в сообщении для участия*⚡⚡⚡\n\n"
        f"Участвуют (0): "
    )

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
            logging.warning(f"Не удалось закрепить сообщение: {e}")

    except Exception as e:
        logging.error(f"Ошибка отправки события: {e}")

    try:
        await message.delete()
    except Exception:
        pass


# ==========================
# Универсальный хендлер команд
# ==========================
@router.message(Command(list(EVENT_MAP.keys())))
async def event_handler(message: types.Message):
    command = message.text.split()[0].replace("/", "")
    handler_func = EVENT_MAP.get(command)

    if not handler_func:
        return

    text, media_url = handler_func()
    await send_event_photo(message, media_url, text)


# ==========================
# Callback ➕
# ==========================
@router.callback_query(lambda c: c.data == "join_plus")
async def handle_plus_reaction(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    username = escape_md(callback.from_user.first_name)
    message = callback.message
    participants = parse_participants(message.caption)

    display_name = escape_md(get_user_from_sheet(user_id) or username)

    if display_name in participants:
        await callback.answer("Вы уже участвуете!")
        return

    participants.append(display_name)
    time = extract_time_from_caption(message.caption)
    keyboard = create_keyboard()

    await update_caption(message, participants, callback,
                         f"Вы присоединились, {display_name}!", time, keyboard)


# ==========================
# Callback ➖
# ==========================
@router.callback_query(lambda c: c.data == "join_minus")
async def handle_minus_reaction(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    username = escape_md(callback.from_user.first_name)
    message = callback.message
    participants = parse_participants(message.caption)

    display_name = escape_md(get_user_from_sheet(user_id) or username)

    if display_name not in participants:
        await callback.answer("Вы не участвуете.")
        return

    participants.remove(display_name)
    time = extract_time_from_caption(message.caption)
    keyboard = create_keyboard()

    await update_caption(message, participants, callback,
                         f"Вы больше не участвуете, {display_name}.", time, keyboard)
