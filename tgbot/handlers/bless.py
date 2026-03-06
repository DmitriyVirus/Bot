import re
import logging
from aiogram import types, Router
from aiogram.filters import Command
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from tgbot.redis.redis_cash import (
    get_name,
    get_allowed_user_ids,
    get_bless_data
)

router = Router()
logging.basicConfig(level=logging.INFO)


# =================================
# КНОПКИ
# =================================

def create_bless_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="➕ Сб", callback_data="bless_plus_sb"),
                InlineKeyboardButton(text="➖ Сб", callback_data="bless_minus_sb"),
            ],
            [
                InlineKeyboardButton(text="➕ Вс", callback_data="bless_plus_vs"),
                InlineKeyboardButton(text="➖ Вс", callback_data="bless_minus_vs"),
            ],
        ]
    )


# =================================
# ПАРСИНГ
# =================================

def parse_lists(text: str):

    sb = []
    vs = []

    current = None

    for line in text.splitlines():

        if "СУББОТА" in line:
            current = "sb"

        elif "ВОСКРЕСЕНЬЕ" in line:
            current = "vs"

        match = re.match(r"\d+\.\s*(.+)", line)

        if match:
            name = match.group(1).strip()

            if name:

                if current == "sb":
                    sb.append(name)

                elif current == "vs":
                    vs.append(name)

    return sb, vs


# =================================
# СБОРКА ТЕКСТА
# =================================

def format_block(title, collector, participants):

    visible = 5

    text = f"{title}\n\n"

    text += f"Собирает: {collector}\n\n"

    text += "Предварительный список:\n\n"

    for i in range(visible):

        if i < len(participants):
            text += f"{i+1}. {participants[i]}\n"
        else:
            text += f"{i+1}.\n"

    if len(participants) > visible:

        text += "\n"

        for i in range(visible, len(participants)):
            text += f"{i+1}. {participants[i]}\n"

    return text


def build_caption(sb, vs):

    text = ""

    text += format_block(
        "📌📌📌 СУББОТА — 16:00 (РУНА)",
        "Павел",
        sb
    )

    text += "\n"

    text += "2️⃣ Блески первый заход — 110+\n\n"
    text += "3️⃣ После блесок — ТАРАС (115+)\n\n\n"

    text += format_block(
        "📌📌📌 ВОСКРЕСЕНЬЕ — 11:30",
        "Влад",
        vs
    )

    return text


# =================================
# КОМАНДА
# =================================

@router.message(Command("bless"))
async def bless(message: types.Message):

    text, photo = get_bless_data()

    caption = build_caption([], [])

    keyboard = create_bless_keyboard()

    if photo:
        sent = await message.bot.send_photo(
            message.chat.id,
            photo,
            caption=caption,
            reply_markup=keyboard
        )
    else:
        sent = await message.answer(
            caption,
            reply_markup=keyboard
        )

    try:
        await message.chat.pin_message(sent.message_id)
    except:
        pass

    await message.delete()


# =================================
# ЛОГИКА
# =================================

async def process_action(callback, day, action, name):

    message = callback.message

    text = message.caption or message.text

    sb, vs = parse_lists(text)

    participants = sb if day == "sb" else vs

    if action == "plus":

        if name not in participants:
            participants.append(name)

    else:

        if name in participants:
            participants.remove(name)

    caption = build_caption(sb, vs)

    try:

        await message.edit_caption(
            caption=caption,
            reply_markup=create_bless_keyboard()
        )

        await callback.answer()

    except Exception as e:
        logging.error(e)


# =================================
# CALLBACK
# =================================

@router.callback_query(lambda c: c.data.startswith("bless_"))
async def bless_callback(callback: types.CallbackQuery):

    data = callback.data.split("_")

    action = data[1]
    day = data[2]

    name = get_name(
        callback.from_user.id,
        callback.from_user.first_name
    )

    await process_action(callback, day, action, name)


# =================================
# ТЕКСТОВЫЕ КОМАНДЫ
# =================================

@router.message(lambda m: m.reply_to_message and m.text)
async def bless_text_control(message: types.Message):

    text = message.text.lower()

    if not text.startswith(("+", "-")):
        return

    parts = text.split()
    if len(parts) < 2:
        return

    action = "plus" if parts[0] == "+" else "minus"
    day = "sb" if "сб" in parts[1] else "vs" if "вс" in parts[1] else None

    if not day:
        return

    reply = message.reply_to_message
    if not reply:
        return

    # Определяем имя
    if len(parts) > 2 and message.from_user.id in get_allowed_user_ids():
        target_name = " ".join(parts[2:])
    else:
        target_name = get_name(message.from_user.id, message.from_user.first_name)

    # Парсим и меняем список напрямую
    text_src = reply.caption or reply.text or ""
    sb, vs = parse_lists(text_src)

    participants = sb if day == "sb" else vs

    if action == "plus":
        if target_name not in participants:
            participants.append(target_name)
    else:
        if target_name in participants:
            participants.remove(target_name)

    caption = build_caption(sb, vs)

    try:
        await reply.edit_caption(
            caption=caption,
            reply_markup=create_bless_keyboard()
        )
    except Exception as e:
        logging.error(f"Ошибка ручного управления bless: {e}")

    try:
        await message.delete()
    except Exception:
        pass
