from aiogram import types, Router, Bot
from aiogram.filters import Command
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from tgbot.triggers import USER_MAPPING
import re
import logging

# Настройка логирования
logging.basicConfig(level=logging.DEBUG)

router = Router()

# Хендлер для команды /inst
@router.message(Command(commands=["inst"]))
async def fix_handler(message: types.Message, bot: Bot):
    try:
        time_match = re.search(r"(\d{1,2}:\d{2})", message.text)
        time = time_match.group(1) if time_match else "когда соберемся"
        photo_url = "https://battleclub.space/uploads/monthly_2022_07/baylor.jpg.02e0df864753bf47b1ef76303b993a1d.jpg"
        keyboard = create_keyboard()
        sent_message = await bot.send_photo(
            chat_id=message.chat.id,
            photo=photo_url,
            caption=(
                f"☠️*Идем в инсты {time}*.☠️\n\nКак обычно идут Дмитрий(МакароноВирус), Леонид(ТуманныйТор) и кто-то еще. Есть 5 мест.\n\n"
                f"⚡⚡⚡*Нажмите ➕ в сообщении для участия*⚡⚡⚡"
            ),
            parse_mode="Markdown",
            reply_markup=keyboard
        )
        await message.chat.pin_message(sent_message.message_id)
        logging.info(f"Сообщение отправлено и закреплено с id: {sent_message.message_id}")
    except Exception as e:
        logging.error(f"Ошибка при обработке команды /inst: {e}")
        await message.answer("Произошла ошибка. Попробуйте снова.")

def parse_participants(caption: str):
    parts = caption.split("Желающие:")
    first_part = parts[0]
    first_part_names = []
    match1 = re.search(r"Идут \d+ человек: (.+)", first_part, flags=re.DOTALL)
    if match1:
        first_part_names = [name.strip() for name in match1.group(1).split(",") if name.strip()]

    second_part = parts[1] if len(parts) > 1 else ""
    second_part_names = [name.strip() for name in second_part.split(",") if name.strip()]

    participants = first_part_names + second_part_names
    return participants

# Функция для извлечения времени из подписи
def extract_time_from_caption(caption: str):
    time_match = re.search(r"Идем в инсты\s*(\d{1,2}:\d{2}|когда соберемся)", caption)
    return time_match.group(1) if time_match else "когда соберемся"

# Функция для обновления подписи к фото
async def update_caption(photo_message: types.Message, participants: list, callback: types.CallbackQuery, action_message: str, time: str, keyboard: InlineKeyboardMarkup):
    main_participants = participants[:5]
    extra_participants = participants[5:]
    participants_count = len(participants)

    # Логируем общее количество участников
    logging.debug(f"Идут: {len(main_participants)} человек, Желающие: {len(extra_participants)} человек")

    if not participants:
        # Если список участников пуст
        updated_text = (
            f"☠️*Идем в инсты {time}*.☠️\n\n Как обычно идут Дмитрий(МакароноВирус), Леонид(ТуманныйТор) и кто-то еще. Есть 5 мест \n\n"
            f"⚡⚡⚡*Нажмите ➕ в сообщении для участия*.⚡⚡⚡"
        )
    else:
        # Формируем текст обновления
        main_text = ", ".join(main_participants)
        extra_text = ", ".join(extra_participants)
        updated_text = (
            f"☠️*Идем в инсты {time}*.☠️\n\n Как обычно идут Дмитрий(МакароноВирус), Леонид(ТуманныйТор) и кто-то еще. Есть 5 мест. \n\n"
            f"⚡⚡⚡*Нажмите ➕ в сообщении для участия*.⚡⚡⚡\n\n"
            f"😈Идут {len(main_participants)} человек: {main_text}"
        )
        if extra_participants:
            updated_text += f"\nЖелающие: {extra_text}"

    # Проверяем, нужно ли обновлять сообщение
    if photo_message.caption != updated_text or photo_message.reply_markup != keyboard:
        try:
            await photo_message.edit_caption(caption=updated_text, parse_mode="Markdown", reply_markup=keyboard)
            await callback.answer(action_message)
        except Exception as e:
            logging.error(f"Ошибка при обновлении подписи: {e}")
            await callback.answer("Не удалось обновить подпись. Попробуйте снова.")
    else:
        logging.debug("Изменений в сообщении нет, обновление пропущено.")
        await callback.answer(action_message)

# Обработчик для нажатия на кнопку "➕ Присоединиться"
@router.callback_query(lambda callback: callback.data == "join_plus")
async def handle_plus_reaction(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    username = callback.from_user.first_name
    message = callback.message

    participants = parse_participants(message.caption)
    logging.debug(f"[До добавления] Участники: {participants}")

    # Проверяем имя из таблицы
    display_name = USER_MAPPING.get(user_id, username)

    if display_name in participants:
        await callback.answer(f"Вы уже участвуете, {display_name}!")
        return

    participants.append(display_name)
    logging.debug(f"[После добавления] Участники: {participants}")

    time = extract_time_from_caption(message.caption)
    keyboard = create_keyboard()
    await update_caption(message, participants, callback, f"Вы присоединились, {display_name}!", time, keyboard)


# Обработчик для нажатия на кнопку "➖ Не участвовать"
@router.callback_query(lambda callback: callback.data == "join_minus")
async def handle_minus_reaction(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    username = callback.from_user.first_name
    message = callback.message

    participants = parse_participants(message.caption)
    logging.debug(f"[До удаления] Участники: {participants}")

    display_name = USER_MAPPING.get(user_id, username)

    if display_name in participants:
        participants.remove(display_name)
    else:
        await callback.answer("Вы не участвуете.")
        return

    logging.debug(f"[После удаления] Участники: {participants}")

    time = extract_time_from_caption(message.caption)
    keyboard = create_keyboard()
    await update_caption(message, participants, callback, f"Вы больше не участвуете, {display_name}.", time, keyboard)
    
# Функция для создания клавиатуры
def create_keyboard():
    plus_button = InlineKeyboardButton(text="➕ Присоединиться", callback_data="join_plus")
    minus_button = InlineKeyboardButton(text="➖ Не участвовать", callback_data="join_minus")
    return InlineKeyboardMarkup(inline_keyboard=[[plus_button, minus_button]])
