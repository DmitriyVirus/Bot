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
    get_inst_data,
    get_name_username_dict
)

logging.basicConfig(level=logging.DEBUG)
router = Router()


# ==========================
# Markdown escape
# ==========================
def escape_md(text: str) -> str:
    return re.sub(r'([_*\[\]()~`>#+\-=|{}.!])', r'\\\1', text)


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
    bench_participants = []

    match_main = re.search(r"Участвуют \(\d+\): ([^\n]+)", caption or "")
    if match_main:
        main_participants = [x.strip() for x in match_main.group(1).split(",") if x.strip()]

    match_bench = re.search(r"Скамейка запасных \(\d+\): ([^\n]+)", caption or "")
    if match_bench:
        bench_participants = [x.strip() for x in match_bench.group(1).split(",") if x.strip()]

    return main_participants, bench_participants


# ==========================
# Обновление подписи
# ==========================
async def update_caption(photo_message: types.Message,
                         main_participants: list,
                         bench_participants: list,
                         callback: types.CallbackQuery,
                         action_message: str,
                         keyboard: InlineKeyboardMarkup):

    main_participants = list(dict.fromkeys(main_participants))
    bench_participants = list(dict.fromkeys(bench_participants))

    caption_orig = photo_message.caption or ""
    first_line = caption_orig.split("\n")[0].replace("*", "").strip()

    header = re.sub(r"\b\d{1,2}:\d{2}(?:-\d{1,2}:\d{2})?\b", "", first_line).strip()
    if not header:
        header = "Событие"

    updated_text = (
        f"*{escape_md(header)}*\n\n"
        f"⚡⚡⚡*Нажмите ➕ в сообщении для участия*⚡⚡⚡\n\n"
        f"Участвуют ({len(main_participants)}): {', '.join(main_participants) if main_participants else ''}"
    )

    if bench_participants:
        updated_text += (
            f"\n\nСкамейка запасных ({len(bench_participants)}): "
            f"{', '.join(bench_participants)}"
        )

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
            await callback.answer("Ошибка обновления.")


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
    allowed_ids = get_allowed_user_ids()

    main_participants = []
    bench_participants = []

    if user_id in allowed_ids and col_indexes:
        for col in col_indexes:
            column_data = get_column_data_from_autosbor(col)
            if column_data:
                main_participants.extend(column_data)

    main_participants = list(dict.fromkeys(main_participants))

    header_text = escape_md(f"{header_prefix} {time}")

    caption = (
        f"*{header_text}*\n\n"
        f"⚡⚡⚡*Нажмите ➕ в сообщении для участия*⚡⚡⚡\n\n"
        f"Участвуют ({len(main_participants)}): "
        f"{', '.join(main_participants) if main_participants else ''}"
    )

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
    except:
        pass

    try:
        await message.delete()
    except:
        pass


# ==========================
# Команды событий
# ==========================
@router.message(Command(*EVENT_MAP.keys()))
async def event_handler(message: types.Message):
    command = message.text.split()[0].replace("/", "")
    handler_func = EVENT_MAP.get(command)

    if not handler_func:
        return

    text, media_url = handler_func()
    await send_event_photo(message, media_url, text)


# ==========================
# ➕ Кнопка
# ==========================
@router.callback_query(lambda c: c.data == "join_plus")
async def handle_plus(callback: types.CallbackQuery):
    message = callback.message
    main_participants, bench_participants = parse_participants(message.caption)

    display_name = get_user_from_sheet(callback.from_user.id) or callback.from_user.first_name

    if display_name in main_participants or display_name in bench_participants:
        await callback.answer("Вы уже участвуете!")
        return

    if len(main_participants) < 7:
        main_participants.append(display_name)
    else:
        bench_participants.append(display_name)

    await update_caption(
        message,
        main_participants,
        bench_participants,
        callback,
        "Вы добавлены!",
        create_keyboard()
    )


# ==========================
# ➖ Кнопка
# ==========================
@router.callback_query(lambda c: c.data == "join_minus")
async def handle_minus(callback: types.CallbackQuery):
    message = callback.message
    main_participants, bench_participants = parse_participants(message.caption)

    display_name = get_user_from_sheet(callback.from_user.id) or callback.from_user.first_name

    if display_name in main_participants:
        main_participants.remove(display_name)
    elif display_name in bench_participants:
        bench_participants.remove(display_name)
    else:
        await callback.answer("Вы не участвуете.")
        return

    await update_caption(
        message,
        main_participants,
        bench_participants,
        callback,
        "Вы удалены.",
        create_keyboard()
    )


# ==========================
# Ручное добавление + Имя
# ==========================
@router.message(lambda message: message.text and message.text.startswith("+ "))
async def manual_add(message: types.Message):
    reply = message.reply_to_message
    if not reply or not reply.caption:
        return

    name = message.text[2:].strip()
    main_participants, bench_participants = parse_participants(reply.caption)

    if name in main_participants or name in bench_participants:
        return

    if len(main_participants) < 7:
        main_participants.append(name)
    else:
        bench_participants.append(name)

    await update_caption(
        reply,
        main_participants,
        bench_participants,
        None,
        "",
        create_keyboard()
    )

    await message.delete()


# ==========================
# ГО — массовое добавление
# ==========================
@router.message(lambda message: message.text and message.text.lower() == "го")
async def go_all(message: types.Message):
    reply = message.reply_to_message
    if not reply or not reply.caption:
        return

    name_dict = get_name_username_dict()
    main_participants, bench_participants = parse_participants(reply.caption)

    for name in name_dict.values():
        if name not in main_participants and name not in bench_participants:
            if len(main_participants) < 7:
                main_participants.append(name)
            else:
                bench_participants.append(name)

    await update_caption(
        reply,
        main_participants,
        bench_participants,
        None,
        "",
        create_keyboard()
    )

    await message.delete()
