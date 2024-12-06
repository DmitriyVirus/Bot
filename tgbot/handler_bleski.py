import re
import logging
from aiogram import types, Router
from aiogram.filters import Command
from tgbot.triggers import USER_MAPPING
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

# Настройка логирования
logging.basicConfig(level=logging.DEBUG)

router = Router()

# Хендлер для команды /bleski
@router.message(Command(commands=["bleski"]))
async def bleski_handler(message: types.Message):
    try:
        # Извлекаем текст после команды /bleski
        time = message.text[len("/bleski "):] if len(message.text) > len("/bleski ") else "когда соберемся"
        
        # Используем это слово в подписи
        photo_url = "https://i.pinimg.com/736x/85/a9/d9/85a9d968b58b3294ff44774f960992af.jpg"  # Укажите URL для вашей картинки
        keyboard = create_keyboard()
        sent_message = await message.bot.send_photo(
            chat_id=message.chat.id,
            photo=photo_url,
            caption=( 
                f"☠️*Идем в блески {time}*.☠️\n\nКак обычно идут Дмитрий(МакароноВирус), Леонид(ТуманныйТор) и кто-то еще. Есть 5 мест.\n\n"
                f"⚡⚡⚡*Нажмите ➕ в сообщении для участия*⚡⚡⚡"
            ),
            parse_mode="Markdown",
            reply_markup=keyboard
        )
        await message.chat.pin_message(sent_message.message_id)
        logging.info(f"Сообщение отправлено и закреплено с id: {sent_message.message_id}")
    except Exception as e:
        logging.error(f"Ошибка при обработке команды /bleski: {e}")
        await message.answer("Произошла ошибка. Попробуйте снова.")

async def update_bleski_caption(photo_message: types.Message, participants: list, callback: types.CallbackQuery, action_message: str, time: str, keyboard: InlineKeyboardMarkup):
    main_participants = participants[:10]
    extra_participants = participants[10:]

    # Логируем общее количество участников
    logging.debug(f"Идут: {len(main_participants)} человек, Желающие: {len(extra_participants)} человек")

    if not participants:
        updated_text = (
            f"☠️*Идем в блески {time}*.☠️\n\nКак обычно идут Дмитрий(МакароноВирус), Леонид(ТуманныйТор) и кто-то еще. Есть 5 мест.\n\n"
            f"⚡⚡⚡*Нажмите ➕ в сообщении для участия*⚡⚡⚡"
        )
    else:
        # Формируем текст для обновления
        main_text = ", ".join(main_participants)
        extra_text = ", ".join(extra_participants)
        updated_text = (
            f"☠️*Идем в блески {time}*.☠️\n\nКак обычно идут Дмитрий(МакароноВирус), Леонид(ТуманныйТор) и кто-то еще. Есть 5 мест.\n\n"
            f"⚡⚡⚡*Нажмите ➕ в сообщении для участия*⚡⚡⚡\n\n"
            f"😈Идут {len(main_participants)} человек: {main_text}"
        )
        if extra_participants:
            updated_text += f"\nЖелающие: {extra_text}"

    # Здесь мы обновляем только клавиатуру (если она изменилась) и участников
    if photo_message.reply_markup != keyboard:
        try:
            await photo_message.edit_caption(caption=updated_text, parse_mode="Markdown", reply_markup=keyboard)
            await callback.answer(action_message)
        except Exception as e:
            logging.error(f"Ошибка при обновлении подписи: {e}")
            await callback.answer("Не удалось обновить подпись. Попробуйте снова.")
    else:
        logging.debug("Изменений в сообщении нет, обновление пропущено.")
        await callback.answer(action_message)

# Обработчик для нажатия на кнопку "➕ Присоединиться" для команды /bleski
@router.callback_query(lambda callback: callback.data == "join_plus")
async def handle_plus_bleski(callback: types.CallbackQuery):
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

    time = extract_time_from_caption(message.caption)  # В случае с блесками, просто используем 'time' без извлечения времени
    keyboard = create_keyboard()
    await update_bleski_caption(message, participants, callback, f"Вы присоединились, {display_name}!", time, keyboard)

# Обработчик для нажатия на кнопку "➖ Не участвовать" для команды /bleski
@router.callback_query(lambda callback: callback.data == "join_minus")
async def handle_minus_bleski(callback: types.CallbackQuery):
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
    await update_bleski_caption(message, participants, callback, f"Вы больше не участвуете, {display_name}.", time, keyboard)

# Функция для создания клавиатуры
def create_keyboard():
    plus_button = InlineKeyboardButton(text="➕ Присоединиться", callback_data="join_plus")
    minus_button = InlineKeyboardButton(text="➖ Не участвовать", callback_data="join_minus")
    return InlineKeyboardMarkup(inline_keyboard=[[plus_button, minus_button]])

