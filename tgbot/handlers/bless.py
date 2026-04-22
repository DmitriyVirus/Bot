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
    in_extra = False

    for line in text.splitlines():

        if "СУББОТА" in line:
            current = "sb"
            in_extra = False

        elif "ВОСКРЕСЕНЬЕ" in line:
            current = "vs"
            in_extra = False

        elif "Доп. Желающие" in line and current == "sb":
            in_extra = True

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
SB_LIMIT = 10

SB_DEFAULT = [
    "Павел(Обезгномливание)",
    "Александр(Piuv)",
]

VS_DEFAULT = [
    "Евгений(ХныкКи)",
    "Александр(Piuv)",
]


def format_sb_list(participants: list, min_rows: int = 5) -> str:
    """
    Нумерованный список для СБ.
    Первые места — SB_DEFAULT, затем остальные участники.
    Основной список — до SB_LIMIT мест (минимум min_rows пустых строк).
    Если участников больше SB_LIMIT — добавляется блок 'Доп. Желающие'.
    """
    # Дефолтные всегда первые, остальные после них без дублей
    extra_participants = [p for p in participants if p not in SB_DEFAULT]
    full = SB_DEFAULT + extra_participants

    main = full[:SB_LIMIT]
    extra = full[SB_LIMIT:]

    total = max(len(main), min_rows)
    lines = []
    for i in range(total):
        if i < len(main):
            lines.append(f"{i+1}. {main[i]}")
        else:
            lines.append(f"{i+1}.")

    if extra:
        lines.append("")
        lines.append("Доп. Желающие:")
        for i, name in enumerate(extra, 1):
            lines.append(f"{i}. {name}")

    return "\n".join(lines)


def format_vs_list(participants: list, min_rows: int = 5) -> str:
    """
    Нумерованный список для ВС.
    Первые места — VS_DEFAULT, затем остальные участники.
    Минимум min_rows строк.
    """
    extra_participants = [p for p in participants if p not in VS_DEFAULT]
    full = VS_DEFAULT + extra_participants

    total = max(len(full), min_rows)
    lines = []
    for i in range(total):
        if i < len(full):
            lines.append(f"{i+1}. {full[i]}")
        else:
            lines.append(f"{i+1}.")
    return "\n".join(lines)


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
