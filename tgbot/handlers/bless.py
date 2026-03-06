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
# ФОРМАТИРОВАНИЕ СПИСКОВ
# =================================
def format_sb_list(participants: list, total: int = 10) -> str:
    """Нумерованный список для СБ, всего total строк"""
    lines = []
    for i in range(total):
        if i < len(participants):
            lines.append(f"{i+1}. {participants[i]}")
        else:
            lines.append(f"{i+1}.")
    return "\n".join(lines)


def format_vs_list(participants: list) -> str:
    """Список через запятую для ВС"""
    if not participants:
        return ""
    return ", ".join(participants)


# =================================
# СБОРКА ТЕКСТА из шаблона Redis
# =================================
def build_caption(sb: list, vs: list) -> str:
    template, _ = get_bless_data()

    sb_list = format_sb_list(sb)
    vs_list = format_vs_list(vs)

    return template.replace("{sb_list}", sb_list).replace("{vs_list}", vs_list)


# =================================
# КОМАНДА
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
async def process_action(message: types.Message, day: str, action: str, name: str):
    """
    message: сообщение которое нужно отредактировать
    day: "sb" или "vs"
    action: "plus" или "minus"
    name: имя участника
    """
    text = message.caption or message.text

    sb, vs = parse_lists(text)
    participants = sb if day == "sb" else vs

    if action == "plus":
        if name not in participants:
            participants.append(name)
    elif action == "minus":
        if name in participants:
            participants.remove(name)

    caption = build_caption(sb, vs)

    try:
        if message.photo:
            await message.edit_caption(
                caption=caption,
                reply_markup=create_bless_keyboard()
            )
        else:
            await message.edit_text(
                text=caption,
                reply_markup=create_bless_keyboard()
            )
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

    await process_action(callback.message, day, action, name)
    await callback.answer()


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
