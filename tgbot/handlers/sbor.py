import re
import logging
from aiogram import types, Router
from aiogram.filters import Command
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from tgbot.redis.redis_cash import (
    redis,
    get_name,
    get_allowed_user_ids,
    get_bal_data,
    get_inn_data,
    get_ork_data,
    get_inst_data,
    get_freya_data,
    get_ramona_data,
    get_name_username_dict,
    get_column_data_from_autosbor
)
logging.basicConfig(level=logging.DEBUG)
router = Router()


# ==========================
# EVENT MAP (универсальный хендлер)
# ==========================
EVENT_MAP = {
    "bal": get_bal_data,
    "inn": get_inn_data,
    "ork": get_ork_data,
    "inst": get_inst_data,
    "freya": get_freya_data,
    "ramona": get_ramona_data,
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
    text = message.text

    # --- Старый алгоритм извлечения времени ---
    time_match = re.search(r"\b\d{1,2}:\d{2}(?:-\d{1,2}:\d{2})?\b", text)
    time = time_match.group(0) if time_match else "когда соберемся"

    # --- Старый алгоритм извлечения одной колонки ---
    col_index = None
    after_text = text  # будем искать букву l после команды, кроме первого слова
    if time_match:
        after_text = text[time_match.end():]
        col_match = re.search(r"\b\d+\b", after_text)
        if col_match:
            col_index = int(col_match.group(0))
    else:
        col_match = re.search(r"\b\d+\b", text)
        if col_match:
            col_index = int(col_match.group(0))

    # --- Проверка буквы "l" в тексте после команды ---
    parts = text.split()
    after_command = " ".join(parts[1:])  # всё кроме первого слова (команды)
    include_list = "l" in after_command.lower()

    user_id = message.from_user.id
    allowed_ids = get_allowed_user_ids()

    participants = []

    # --- Получение участников из колонки ---
    if col_index and user_id in allowed_ids:
        participants = get_column_data_from_autosbor(col_index)

    # --- Если есть буква "l", добавляем участников из листа ---
    if include_list and user_id in allowed_ids:
        redis_key = f"list_{user_id}"
        try:
            existing_list = redis.lrange(redis_key, 0, -1)
            if existing_list:
                # декодируем и добавляем всех участников из листа (включая создателя)
                existing_list = [
                    v.decode() if isinstance(v, bytes) else v
                    for v in existing_list
                ]
                for name in existing_list:
                    if name not in participants:
                        participants.append(name)
            else:
                # листа нет
                await message.answer("ℹ️ Листа у тебя нет, используем обычный набор участников.")
        except Exception as e:
            logging.error(f"Ошибка при получении листа {redis_key}: {e}")
            await message.answer("❌ Ошибка при попытке загрузить лист, используем обычный набор участников.")

    header_text = f"{header_prefix} {time}"

    caption = (
        f"*{header_text}*\n\n"
        f"⚡⚡⚡*Нажмите ➕ в сообщении для участия*⚡⚡⚡\n\n"
    )

    if participants:
        caption += f"Участвуют ({len(participants)}): {', '.join(participants)}"
    else:
        caption += "Участвуют (0): "

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
@router.message(Command(*EVENT_MAP.keys()))
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
    telegram_name = callback.from_user.first_name or "Unknown"
    message = callback.message

    participants = parse_participants(message.caption)

    # 🔥 Берём имя из Redis
    display_name = get_name(user_id, telegram_name)

    if display_name in participants:
        await callback.answer("Вы уже участвуете!")
        return

    participants.append(display_name)

    time = extract_time_from_caption(message.caption)
    keyboard = create_keyboard()

    await update_caption(
        message,
        participants,
        callback,
        f"Вы присоединились, {display_name}!",
        time,
        keyboard
    )


# ==========================
# Callback ➖
# ==========================
@router.callback_query(lambda c: c.data == "join_minus")
async def handle_minus_reaction(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    telegram_name = callback.from_user.first_name or "Unknown"
    message = callback.message

    participants = parse_participants(message.caption)

    # 🔥 Берём имя из Redis
    display_name = get_name(user_id, telegram_name)

    if display_name not in participants:
        await callback.answer("Вы не участвуете.")
        return

    participants.remove(display_name)

    time = extract_time_from_caption(message.caption)
    keyboard = create_keyboard()

    await update_caption(
        message,
        participants,
        callback,
        f"Вы больше не участвуете, {display_name}.",
        time,
        keyboard
    )

# ==========================
# Проверка целевого сообщения бота
# ==========================
def is_target_bot_message(message: types.Message) -> bool:
    if not message:
        return False

    # сообщение должно быть от бота
    if not message.from_user or not message.from_user.is_bot:
        return False

    # должна быть inline клавиатура
    if not message.reply_markup or not message.reply_markup.inline_keyboard:
        return False

    # проверяем callback_data кнопок
    for row in message.reply_markup.inline_keyboard:
        for button in row:
            if button.callback_data in ("join_plus", "join_minus"):
                return True

    return False


# ==========================
# Ручное добавление
# ==========================
@router.message(lambda message: message.text and message.text.startswith("+ "))
async def handle_plus_message(message: types.Message):
    user_id = message.from_user.id
    if user_id not in get_allowed_user_ids():
        return

    message_obj = message.reply_to_message
    if not is_target_bot_message(message_obj):
        return

    username = message.text[2:].strip()

    caption = message_obj.caption or message_obj.text
    participants = parse_participants(caption)
    if username in participants:
        await message.answer(f"{username} уже участвует!")
        return

    participants.append(username)
    time = extract_time_from_caption(caption)
    keyboard = create_keyboard()

    await update_caption(
        message_obj,
        participants,
        None,
        f"{username} добавлен!",
        time,
        keyboard
    )

    try:
        await message.delete()
    except Exception:
        pass


# ==========================
# Ручное удаление
# ==========================
@router.message(lambda message: message.text and message.text.startswith("- "))
async def handle_minus_message(message: types.Message):
    user_id = message.from_user.id
    if user_id not in get_allowed_user_ids():
        return

    message_obj = message.reply_to_message
    if not is_target_bot_message(message_obj):
        return

    username = message.text[2:].strip()

    caption = message_obj.caption or message_obj.text
    participants = parse_participants(caption)
    if username not in participants:
        await message.answer(f"{username} не участвует.")
        return

    participants.remove(username)
    time = extract_time_from_caption(caption)
    keyboard = create_keyboard()

    await update_caption(
        message_obj,
        participants,
        None,
        f"{username} удален!",
        time,
        keyboard
    )

    try:
        await message.delete()
    except Exception:
        pass


# ==========================
# Команда "го"
# ==========================
@router.message(lambda message: message.text and message.text.lower().startswith("го") and message.reply_to_message)
async def handle_go_numbered(message: types.Message):
    user_id = message.from_user.id
    allowed_ids = get_allowed_user_ids()
    if user_id not in allowed_ids:
        return

    reply_msg = message.reply_to_message
    if not is_target_bot_message(reply_msg):
        return

    caption = reply_msg.caption or reply_msg.text or ""
    if not caption:
        return

    participants = parse_participants(caption)
    if not participants:
        await message.answer("Не удалось найти участников в сообщении.")
        return

    name_username = get_name_username_dict()
    if not name_username:
        await message.answer("Не удалось получить данные из Google Sheets.")
        return

    numbers = re.findall(r"\d+", message.text)
    if numbers:
        indexes = [int(n) - 1 for n in numbers if 0 < int(n) <= len(participants)]
        selected = [participants[i] for i in indexes]
    else:
        selected = participants

    tg_usernames = []
    for name in selected:
        username = name_username.get(name)
        if username and username.lower() != "unknown":
            tg_usernames.append(f"@{username}")
        else:
            tg_usernames.append(name)

    if not tg_usernames:
        await message.answer("Не удалось сопоставить участников с их Telegram-никами.")
        return

    await message.answer(f"Собираемся: {', '.join(tg_usernames)}")

    try:
        await message.delete()
    except Exception:
        pass
