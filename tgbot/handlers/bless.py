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
# ПРОВЕРКА ЧТО ЭТО НУЖНОЕ СООБЩЕНИЕ
# =================================
def is_bless_message(message: types.Message):

    if not message:
        return False

    if not message.reply_markup:
        return False

    for row in message.reply_markup.inline_keyboard:
        for button in row:

            if (
                button.callback_data
                and button.callback_data.startswith("bless_")
            ):
                return True

    return False


# =================================
# РУЧНОЕ ДОБАВЛЕНИЕ
# =================================
@router.message(lambda m: m.text and m.text.lower().startswith("+"))
async def bless_manual_plus(message: types.Message):

    user_id = message.from_user.id

    if user_id not in get_allowed_user_ids():
        return

    reply = message.reply_to_message

    if not is_bless_message(reply):
        return

    parts = message.text.split(maxsplit=2)

    if len(parts) < 3:
        return

    day = parts[1].lower()
    name = parts[2].strip()

    if day not in ["сб", "вс"]:
        return

    day_key = "sb" if day == "сб" else "vs"

    await process_action(
        types.CallbackQuery(
            id="manual",
            from_user=message.from_user,
            chat_instance="manual",
            message=reply,
            data="manual"
        ),
        day_key,
        "plus",
        name
    )

    try:
        await message.delete()
    except:
        pass


# =================================
# РУЧНОЕ УДАЛЕНИЕ
# =================================
@router.message(lambda m: m.text and m.text.lower().startswith("-"))
async def bless_manual_minus(message: types.Message):

    user_id = message.from_user.id

    if user_id not in get_allowed_user_ids():
        return

    reply = message.reply_to_message

    if not is_bless_message(reply):
        return

    parts = message.text.split(maxsplit=2)

    if len(parts) < 3:
        return

    day = parts[1].lower()
    name = parts[2].strip()

    if day not in ["сб", "вс"]:
        return

    day_key = "sb" if day == "сб" else "vs"

    await process_action(
        types.CallbackQuery(
            id="manual",
            from_user=message.from_user,
            chat_instance="manual",
            message=reply,
            data="manual"
        ),
        day_key,
        "minus",
        name
    )

    try:
        await message.delete()
    except:
        pass
