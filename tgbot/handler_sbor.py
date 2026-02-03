import os
import re
import logging
from aiogram import types, Router
from aiogram.filters import Command
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from tgbot.gspread_client import get_gspread_client

logging.basicConfig(level=logging.DEBUG)

router = Router()

# =========================
# Проверка доступа через лист "Добавление"
# =========================
def is_user_allowed_in_addition(user_id: int) -> bool:
    """
    Проверяет, есть ли user_id в листе "Добавление" Google Sheets.
    """
    client = get_gspread_client()
    if not client:
        logging.warning("Google Sheets client not available")
        return False
    try:
        sheet = client.open("ourid").worksheet("Добавление")
        data = sheet.get_all_records()
        for row in data:
            if str(row.get("id")) == str(user_id):
                return True
        return False
    except Exception as e:
        logging.error(f"Error checking user in 'Добавление': {e}")
        return False

# =========================
# Функции для работы с участниками
# =========================
def create_keyboard():
    plus_button = InlineKeyboardButton(text="➕ Присоединиться", callback_data="join_plus")
    minus_button = InlineKeyboardButton(text="➖ Не участвовать", callback_data="join_minus")
    return InlineKeyboardMarkup(inline_keyboard=[[plus_button, minus_button]])

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

async def update_caption(photo_message: types.Message, participants: list, callback: types.CallbackQuery,
                         action_message: str, time: str, keyboard: InlineKeyboardMarkup):
    participants = list(dict.fromkeys(participants))
    main_participants = participants[:7]
    bench_participants = participants[7:]

    header_match = re.search(r"^\s*[*_]?(.+?)\s*[*_]?[\n\r]", photo_message.caption or "")
    header = header_match.group(1) if header_match else f"Идем в {time}"

    main_text = f"Участвуют ({len(main_participants)}): {', '.join(main_participants)}"
    updated_text = f"*{header}*\n\n⚡⚡⚡*Нажмите ➕ в сообщении для участия*⚡⚡⚡\n\n{main_text}"

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
            await callback.answer("Не удалось обновить подпись. Попробуйте снова.")

# =========================
# Команды /bal, /inn, /ork, /inst
# =========================
@router.message(Command(commands=["bal"]))
async def bal_handler(message: types.Message):
    try:
        time_match = re.search(r"(\d{1,2}:\d{2}(?:-\d{1,2}:\d{2})?)", message.text)
        time = time_match.group(1) if time_match else "когда соберемся"

        photo_url = "https://i.pinimg.com/736x/ba/6c/7c/ba6c7c9c1bbde89410e5bcd8736166b2.jpg"
        keyboard = create_keyboard()
        caption = f"🔥 *Идем в гости к Балуану {time}* 🔥\n\n⚡⚡⚡*Нажмите ➕ в сообщении для участия*⚡⚡⚡\n\nУчаствуют (0): "

        sent_message = await message.bot.send_photo(
            chat_id=message.chat.id,
            photo=photo_url,
            caption=caption,
            parse_mode="Markdown",
            reply_markup=keyboard
        )
        await message.chat.pin_message(sent_message.message_id)
    except Exception as e:
        logging.error(f"Ошибка при обработке команды /bal: {e}")
        await message.answer("Произошла ошибка. Попробуйте снова.")

@router.message(Command(commands=["inn"]))
async def inn_handler(message: types.Message):
    try:
        time_match = re.search(r"(\d{1,2}:\d{2}(?:-\d{1,2}:\d{2})?)", message.text)
        time = time_match.group(1) if time_match else "когда соберемся"

        photo_url = "https://i.pinimg.com/736x/2f/4d/55/2f4d556777763c9018c7b026f281e235.jpg"
        keyboard = create_keyboard()
        caption = f"🌿 *Сбор в Иннадрил {time}* 🌿\n\n⚡⚡⚡*Нажмите ➕ в сообщении для участия*⚡⚡⚡\n\nУчаствуют (0): "

        sent_message = await message.bot.send_photo(
            chat_id=message.chat.id,
            photo=photo_url,
            caption=caption,
            parse_mode="Markdown",
            reply_markup=keyboard
        )
        await message.chat.pin_message(sent_message.message_id)
    except Exception as e:
        logging.error(f"Ошибка при обработке команды /inn: {e}")
        await message.answer("Произошла ошибка. Попробуйте снова.")

@router.message(Command(commands=["ork"]))
async def ork_handler(message: types.Message):
    try:
        time_match = re.search(r"(\d{1,2}:\d{2}(?:-\d{1,2}:\d{2})?)", message.text)
        time = time_match.group(1) if time_match else "когда соберемся"

        photo_url = "https://funny.klev.club/uploads/posts/2024-03/thumbs/funny-klev-club-p-smeshnie-kartinki-orki-7.jpg"
        keyboard = create_keyboard()
        caption = f"⚔️ *Идем на орков в {time}!* ⚔️\n\n⚡⚡⚡*Нажмите ➕ в сообщении для участия*⚡⚡⚡\n\nУчаствуют (0): "

        sent_message = await message.bot.send_photo(
            chat_id=message.chat.id,
            photo=photo_url,
            caption=caption,
            parse_mode="Markdown",
            reply_markup=keyboard
        )
        await message.chat.pin_message(sent_message.message_id)
    except Exception as e:
        logging.error(f"Ошибка при обработке команды /ork: {e}")
        await message.answer("Произошла ошибка. Попробуйте снова.")

@router.message(Command(commands=["inst"]))
async def fix_handler(message: types.Message):
    try:
        time_match = re.search(r"(\d{1,2}:\d{2}(?:-\d{1,2}:\d{2})?)", message.text)
        time = time_match.group(1) if time_match else "когда соберемся"

        photo_url = "https://battleclub.space/uploads/monthly_2022_07/baylor.jpg.02e0df864753bf47b1ef76303b993a1d.jpg"
        keyboard = create_keyboard()
        caption = f"☠️*Идем в инсты {time}*☠️\n\n⚡⚡⚡*Нажмите ➕ в сообщении для участия*⚡⚡⚡\n\nУчаствуют (0): "

        sent_message = await message.bot.send_photo(
            chat_id=message.chat.id,
            photo=photo_url,
            caption=caption,
            parse_mode="Markdown",
            reply_markup=keyboard
        )
        await message.chat.pin_message(sent_message.message_id)
    except Exception as e:
        logging.error(f"Ошибка при обработке команды /inst: {e}")
        await message.answer("Произошла ошибка. Попробуйте снова.")

# =========================
# Хендлеры для "+ имя" / "- имя" с проверкой в "Добавление"
# =========================
@router.message(lambda message: message.text and message.text.startswith("+ "))
async def handle_plus_message(message: types.Message):
    user_id = message.from_user.id
    if not is_user_allowed_in_addition(user_id):
        return

    username = message.text[2:].strip()
    message_obj = message.reply_to_message
    if not message_obj or not message_obj.caption:
        return

    participants = parse_participants(message_obj.caption)
    if username in participants:
        return

    participants.append(username)
    time = extract_time_from_caption(message_obj.caption)
    keyboard = create_keyboard()
    await update_caption(message_obj, participants, None, f"{username} присоединился!", time, keyboard)

@router.message(lambda message: message.text and message.text.startswith("- "))
async def handle_minus_message(message: types.Message):
    user_id = message.from_user.id
    if not is_user_allowed_in_addition(user_id):
        return

    username = message.text[2:].strip()
    message_obj = message.reply_to_message
    if not message_obj or not message_obj.caption:
        return

    participants = parse_participants(message_obj.caption)
    if username not in participants:
        return

    participants.remove(username)
    time = extract_time_from_caption(message_obj.caption)
    keyboard = create_keyboard()
    await update_caption(message_obj, participants, None, f"{username} больше не участвует.", time, keyboard)
