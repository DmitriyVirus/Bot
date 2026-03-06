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

def format_block(title, collector, participants, limit=5):
    text = f"{title}\n\n"
    text += f"Собирает: {collector}\n\n"
    text += "Предварительный список:\n\n"

    for i in range(limit):
        if i < len(participants):
            text += f"{i+1}. {participants[i]}\n"
        else:
            text += f"{i+1}.\n"

    if len(participants) > limit:
        text += "\n"
        for i in range(limit, len(participants)):
            text += f"{i+1}. {participants[i]}\n"

    return text


def build_caption(sb, vs):
    text = ""
    text += format_block("📌📌📌 СУББОТА — 16:00 (РУНА)", "Павел", sb)
    text += "\n"
    text += "2️⃣ Блески первый заход — 110+\n\n"
    text += "3️⃣ После блесок — ТАРАС (115+)\n\n\n"
    text += format_block("📌📌📌 ВОСКРЕСЕНЬЕ — 11:30", "Влад", vs)
    return text


# =================================
# ПРОВЕРКА ЧТО ЭТО НУЖНОЕ СООБЩЕНИЕ
# =================================

def is_bless_message(message: types.Message) -> bool:
    if not message or not message.reply_markup:
        return False
    for row in message.reply_markup.inline_keyboard:
        for button in row:
            if button.callback_data and button.callback_data.startswith("bless_"):
                return True
    return False


# =================================
# КОМАНДА /bless
# =================================

@router.message(Command("bless"))
async def bless(message: types.Message):
    _, photo = get_bless_data()
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
        sent = await message.answer(caption, reply_markup=keyboard)

    try:
        await message.chat.pin_message(sent.message_id)
    except Exception:
        pass

    try:
        await message.delete()
    except Exception:
        pass


# =================================
# ЛОГИКА (общая для кнопок и текста)
# =================================

async def apply_action(reply_message: types.Message, day_key: str, action: str, name: str):
    text_src = reply_message.caption or reply_message.text or ""
    sb, vs = parse_lists(text_src)
    participants = sb if day_key == "sb" else vs

    if action == "plus":
        if name not in participants:
            participants.append(name)
    else:
        if name in participants:
            participants.remove(name)

    caption = build_caption(sb, vs)

    await reply_message.edit_caption(
        caption=caption,
        reply_markup=create_bless_keyboard()
    )


# =================================
# CALLBACK (кнопки)
# =================================

@router.callback_query(lambda c: c.data.startswith("bless_"))
async def bless_callback(callback: types.CallbackQuery):
    data = callback.data.split("_")
    action = data[1]
    day_key = data[2]

    name = get_name(callback.from_user.id, callback.from_user.first_name)

    try:
        await apply_action(callback.message, day_key, action, name)
        await callback.answer()
    except Exception as e:
        logging.error(f"Ошибка callback bless: {e}")
        await callback.answer("Не удалось обновить список.")


# =================================
# РУЧНОЕ УПРАВЛЕНИЕ (текстом)
# Формат: + сб Имя  /  - вс Имя
# Только для allowed_user_ids
# =================================

@router.message(lambda m: m.reply_to_message and m.text and
                m.text.lower().startswith(("+", "-")))
async def bless_manual(message: types.Message):
    if message.from_user.id not in get_allowed_user_ids():
        return

    reply = message.reply_to_message
    if not is_bless_message(reply):
        return

    parts = message.text.split(maxsplit=2)
    if len(parts) < 3:
        return

    action = "plus" if parts[0] == "+" else "minus"
    day = parts[1].lower()

    if day not in ("сб", "вс"):
        return

    day_key = "sb" if day == "сб" else "vs"

    # Имя берём из команды как есть — если человека нет в Redis,
    # используется то что написано руками
    written_name = parts[2].strip()
    name = get_name(message.from_user.id, written_name)
    # get_name вернёт written_name если user_id не найден в Redis
    # (так как мы передаём written_name как fallback)

    try:
        await apply_action(reply, day_key, action, name)
    except Exception as e:
        logging.error(f"Ошибка ручного bless: {e}")

    try:
        await message.delete()
    except Exception:
        pass
