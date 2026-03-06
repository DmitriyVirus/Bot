import re
import logging
from aiogram import types, Router
from aiogram.filters import Command
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from tgbot.redis.redis_cash import (
    get_name,
    get_bless_data,
)

logging.basicConfig(level=logging.DEBUG)
router = Router()




# ==========================
# Клавиатура
# ==========================
def create_bless_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="➕ Сб", callback_data="bless_plus_sb"),
        InlineKeyboardButton(text="➖ Сб", callback_data="bless_minus_sb"),
        InlineKeyboardButton(text="➕ Вс", callback_data="bless_plus_vs"),
        InlineKeyboardButton(text="➖ Вс", callback_data="bless_minus_vs"),
    ]])


# ==========================
# Парсинг участников субботы и воскресенья
# ==========================
def parse_bless_participants(caption: str):
    sb_participants = []
    vs_participants = []

    # Суббота: нумерованные строки после "Предварительный список"
    sb_block_match = re.search(
        r"СУББОТА.+?Предварительный список[^\n]*\n((?:\d+\..+\n?)+)",
        caption, re.DOTALL
    )
    if sb_block_match:
        for line in sb_block_match.group(1).splitlines():
            match = re.match(r"\d+\.\s+(.+)", line.strip())
            if match:
                name = match.group(1).strip()
                if name:
                    sb_participants.append(name)

    # Воскресенье: список через запятую после "Предварительный список ... 110+:"
    vs_block_match = re.search(
        r"ВОСКРЕСЕНЬЕ.+?Предварительный список[^\n]*:\s*([^\n]+)",
        caption, re.DOTALL
    )
    if vs_block_match:
        raw = vs_block_match.group(1).replace("...", "").strip()
        raw = raw.replace("+ ВСАДНИКИ", "").strip().rstrip(",").strip()
        names = [n.strip() for n in re.split(r",\s*|\+", raw) if n.strip()]
        vs_participants = names

    return sb_participants, vs_participants


# ==========================
# Сборка caption из шаблона
# ==========================
def build_bless_caption(template: str, sb_participants: list, vs_participants: list, limit: int = 10) -> str:
    sb_marker = "{sb_list}"
    vs_marker = "{vs_list}"

    sb_lines = ""
    for i in range(1, limit + 1):
        if i <= len(sb_participants):
            sb_lines += f"{i}. {sb_participants[i-1]}\n"
        else:
            sb_lines += f"{i}. \n"

    if vs_participants:
        vs_list = ", ".join(vs_participants[:limit])
        vs_extra = f" (+ {len(vs_participants) - limit} в очереди)" if len(vs_participants) > limit else ""
        vs_block = f"{vs_list}{vs_extra}... + ВСАДНИКИ"
    else:
        vs_block = "... + ВСАДНИКИ"

    return template.replace(sb_marker, sb_lines).replace(vs_marker, vs_block)


# ==========================
# Команда /bless
# ==========================
@router.message(Command("bless"))
async def bless_handler(message: types.Message):
    template, photo_url = get_bless_data()
    caption = build_bless_caption(template, [], [])
    keyboard = create_bless_keyboard()

    try:
        if photo_url:
            sent = await message.bot.send_photo(
                chat_id=message.chat.id,
                photo=photo_url,
                caption=caption,
                reply_markup=keyboard
            )
        else:
            sent = await message.answer(caption, reply_markup=keyboard)

        try:
            await message.chat.pin_message(sent.message_id)
        except Exception as e:
            logging.warning(f"Не удалось закрепить: {e}")

    except Exception as e:
        logging.error(f"Ошибка отправки /bless: {e}")

    try:
        await message.delete()
    except Exception:
        pass


# ==========================
# Универсальный обработчик кнопок
# ==========================
async def handle_bless_callback(callback: types.CallbackQuery, day: str, action: str, limit: int = 10):
    user_id = callback.from_user.id
    telegram_name = callback.from_user.first_name or "Unknown"
    message = callback.message

    caption = message.caption or message.text or ""
    sb_participants, vs_participants = parse_bless_participants(caption)
    display_name = get_name(user_id, telegram_name)

    participants = sb_participants if day == "sb" else vs_participants
    day_label = "субботу" if day == "sb" else "воскресенье"

    if action == "plus":
        if display_name in participants:
            await callback.answer("Вы уже в списке!")
            return
        if len(participants) >= limit:
            await callback.answer(f"Мест нет, {display_name}. Все {limit} заняты!")
            return
        participants.append(display_name)
        answer_text = f"Вы записаны на {day_label}, {display_name}!"
    else:
        if display_name not in participants:
            await callback.answer("Вас нет в списке.")
            return
        participants.remove(display_name)
        answer_text = f"Вы убраны из списка на {day_label}, {display_name}."

    if day == "sb":
        sb_participants = participants
    else:
        vs_participants = participants

    # Берём актуальный шаблон из Redis
    template, _ = get_bless_data()
    new_caption = build_bless_caption(template, sb_participants, vs_participants)

    try:
        await message.edit_caption(caption=new_caption, reply_markup=create_bless_keyboard())
        await callback.answer(answer_text)
    except Exception as e:
        logging.error(f"Ошибка обновления bless caption: {e}")
        await callback.answer("Не удалось обновить список.")


@router.callback_query(lambda c: c.data == "bless_plus_sb")
async def bless_plus_sb(callback: types.CallbackQuery):
    await handle_bless_callback(callback, day="sb", action="plus")

@router.callback_query(lambda c: c.data == "bless_minus_sb")
async def bless_minus_sb(callback: types.CallbackQuery):
    await handle_bless_callback(callback, day="sb", action="minus")

@router.callback_query(lambda c: c.data == "bless_plus_vs")
async def bless_plus_vs(callback: types.CallbackQuery):
    await handle_bless_callback(callback, day="vs", action="plus")

@router.callback_query(lambda c: c.data == "bless_minus_vs")
async def bless_minus_vs(callback: types.CallbackQuery):
    await handle_bless_callback(callback, day="vs", action="minus")
