import re
import logging
from aiogram import types, Router
from aiogram.filters import Command
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from tgbot.redis.redis_cash import (
    get_name,
    get_bless_data
)

logging.basicConfig(level=logging.INFO)
router = Router()


# ==========================
# Клавиатура
# ==========================
def create_keyboard():

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="➕ Присоединиться",
                    callback_data="join_plus"
                ),
                InlineKeyboardButton(
                    text="➖ Не участвовать",
                    callback_data="join_minus"
                )
            ]
        ]
    )


# ==========================
# Парсинг списка имен
# ==========================
def parse_names(block_text):

    names = re.findall(r"\d+\.\s*([^\n]+)", block_text)

    return [x.strip() for x in names]


# ==========================
# Построение списка
# ==========================
def build_numbered(names):

    result = ""

    for i, name in enumerate(names, 1):
        result += f"{i}. {name}\n"

    return result


# ==========================
# Обновление текста
# ==========================
def update_caption_text(caption, add_name=None, remove_name=None):

    # ---------- суббота ----------
    sb_pattern = r"(Предварительный список \(всего 10 мест\):\n)(.*?)(2️⃣)"
    sb_match = re.search(sb_pattern, caption, re.S)

    if sb_match:

        prefix = sb_match.group(1)
        list_block = sb_match.group(2)
        suffix = sb_match.group(3)

        names = parse_names(list_block)

        if add_name and add_name not in names:
            names.append(add_name)

        if remove_name and remove_name in names:
            names.remove(remove_name)

        new_block = build_numbered(names)

        caption = (
            caption[:sb_match.start()]
            + prefix
            + new_block
            + suffix
            + caption[sb_match.end():]
        )

        return caption

    # ---------- воскресенье ----------
    vs_pattern = r"(Предварительный список \(места без ограничений\) 110\+:\s*)(.*?)(3️⃣)"
    vs_match = re.search(vs_pattern, caption, re.S)

    if vs_match:

        prefix = vs_match.group(1)
        list_block = vs_match.group(2)
        suffix = vs_match.group(3)

        names = parse_names(list_block)

        if add_name and add_name not in names:
            names.append(add_name)

        if remove_name and remove_name in names:
            names.remove(remove_name)

        new_block = build_numbered(names)

        caption = (
            caption[:vs_match.start()]
            + prefix
            + new_block
            + suffix
            + caption[vs_match.end():]
        )

        return caption

    return caption


# ==========================
# Команда /bless
# ==========================
@router.message(Command("bless"))
async def bless_event(message: types.Message):

    text, photo = get_bless_data()

    keyboard = create_keyboard()

    sent = await message.bot.send_photo(
        chat_id=message.chat.id,
        photo=photo,
        caption=text,
        reply_markup=keyboard
    )

    try:
        await message.chat.pin_message(sent.message_id)
    except:
        pass

    await message.delete()


# ==========================
# Callback +
# ==========================
@router.callback_query(lambda c: c.data == "join_plus")
async def join_plus(callback: types.CallbackQuery):

    user_id = callback.from_user.id
    name = get_name(user_id, callback.from_user.first_name)

    message = callback.message
    caption = message.caption

    new_caption = update_caption_text(
        caption,
        add_name=name
    )

    await message.edit_caption(
        caption=new_caption,
        reply_markup=create_keyboard()
    )

    await callback.answer("Вы добавлены")


# ==========================
# Callback -
# ==========================
@router.callback_query(lambda c: c.data == "join_minus")
async def join_minus(callback: types.CallbackQuery):

    user_id = callback.from_user.id
    name = get_name(user_id, callback.from_user.first_name)

    message = callback.message
    caption = message.caption

    new_caption = update_caption_text(
        caption,
        remove_name=name
    )

    await message.edit_caption(
        caption=new_caption,
        reply_markup=create_keyboard()
    )

    await callback.answer("Вы удалены")
