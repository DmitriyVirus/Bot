import asyncio
import logging
from aiogram import Router, types
from aiogram.types import Message
from aiogram.filters import Command
from tgbot.redis.redis_cash import (
    load_sheet_users_to_redis,
    is_user_in_sheet,
    add_user_to_sheet_and_redis,
    load_allowed_users_to_redis,
    load_event_data_to_redis,
    load_autosbor_to_redis
)

from tgbot.sheets.take_from_sheet import (
    get_fu_data,
    get_nakol_data,
    get_klaar_data,
    get_kris_data,
    get_welcome,
    convert_drive_url,
    fetch_participants
)

router = Router()

@router.message(Command("exist"))
async def check_exist(message: types.Message):
    user_id = message.from_user.id
    username = message.from_user.username or "Unknown"
    first_name = message.from_user.first_name or "Unknown"
    last_name = message.from_user.last_name or "Unknown"

    if is_user_in_sheet(user_id):
        await message.answer("✅ Вы есть в таблице.")
    else:
        await message.answer("❌ Вас нет в таблице, добавляем...")
        await asyncio.to_thread(add_user_to_sheet_and_redis, user_id, username, first_name, last_name)
        await message.answer("✅ Пользователь добавлен!")


async def safe_fetch(func, *args):
    """Обёртка для безопасного вызова блокирующих функций в отдельном потоке"""
    try:
        return await asyncio.to_thread(func, *args)
    except Exception as e:
        logging.exception(f"Ошибка при вызове {func.__name__}: {e}")
        return None



@router.message(Command("refresh"))
async def refresh_redis_command(message: types.Message):
    """
    Команда /refresh — вручную обновляет данные в Redis.
    """
    sent_msg = await message.answer("Обновление Redis... ⏳")
    try:
        await asyncio.to_thread(load_sheet_users_to_redis)
        await asyncio.to_thread(load_allowed_users_to_redis)
        await asyncio.to_thread(load_event_data_to_redis)
        await asyncio.to_thread(load_autosbor_to_redis)
        await sent_msg.edit_text("✅ Redis успешно обновлён вручную!")
    except Exception as e:
        await sent_msg.edit_text(f"❌ Ошибка при обновлении Redis: {e}")



@router.message(Command("fu"))
async def fu_handler(message: Message):
    result = await safe_fetch(get_fu_data)
    if not result:
        await message.answer("Произошла ошибка при получении данных.")
        return

    caption, image_url = result
    if not image_url:
        await message.answer("Картинка не найдена")
        return

    image_url = convert_drive_url(image_url)

    await message.answer_photo(
        image_url,
        caption=caption,
        parse_mode="Markdown"
    )


@router.message(Command("nakol"))
async def nakol_handler(message: Message):
    result = await safe_fetch(get_nakol_data)
    if not result:
        await message.answer("Произошла ошибка при получении данных.")
        return

    caption, video_url = result
    if not video_url:
        await message.answer("Видео не найдено")
        return

    video_url = convert_drive_url(video_url)

    await message.answer_video(
        video_url,
        caption=caption,
        parse_mode="Markdown"
    )


@router.message(Command("klaar"))
async def klaar_handler(message: Message):
    result = await safe_fetch(get_klaar_data)
    if not result:
        await message.answer("Произошла ошибка при получении данных.")
        return

    caption, video_url = result
    if not video_url:
        await message.answer("Видео не найдено")
        return

    video_url = convert_drive_url(video_url)

    await message.answer_video(
        video_url,
        caption=caption,
        parse_mode="Markdown"
    )


@router.message(Command("kris"))
async def kris_handler(message: Message):
    result = await safe_fetch(get_kris_data)
    if not result:
        await message.answer("Произошла ошибка при получении данных.")
        return

    caption, image_url = result
    if not image_url:
        await message.answer("Картинка не найдена")
        return

    image_url = convert_drive_url(image_url)

    await message.answer_photo(
        image_url,
        caption=caption,
        parse_mode="Markdown"
    )


@router.message(Command("hi"))
async def hi_handler(message: Message):
    welcome_text = await safe_fetch(get_welcome)
    if not welcome_text:
        await message.answer("Произошла ошибка при получении приветственного текста.")
        return

    await message.answer(
        welcome_text,
        parse_mode="Markdown"
    )


@router.message(Command(commands=["getid"]))
async def send_chat_id(message: Message):
    chat_id = message.chat.id
    await message.answer(f"Ваш Chat ID: `{chat_id}`", parse_mode="Markdown")
    logging.info(f"Chat ID ({chat_id}) отправлен пользователю {message.from_user.id}")


@router.message(Command(commands=["kto"]))
async def who_is_this(message: Message):
    participants = await safe_fetch(fetch_participants)
    if not participants:
        await message.answer("Ошибка загрузки данных из Google Sheets.")
        return

    args = message.text.split(' ', 1)
    if len(args) < 2:
        await message.answer("Пожалуйста, укажите имя после команды или 'all' для всех.")
        return

    name = args[1].strip().lower()

    if name == "all":
        response = "Список всех пользователей:\n"
        for user_name, user_info in participants.items():
            # Показываем только уникальные записи по основному имени
            if user_name == user_info["name"].lower():
                tgnick_line = f"Имя в телеграмм: {user_info['tgnick']}\n" if user_info['tgnick'] != 'Unknown' else ''
                nick_line = f"Ник: @{user_info['nick']}\n" if user_info['nick'] != 'Unknown' else ''
                response += f"\nИмя: {user_info['name']}\n{tgnick_line}{nick_line}Инфо: {user_info['about']}\n"
        await message.answer(response)
    else:
        user_info = participants.get(name)
        if user_info:
            tgnick_line = f"Имя в телеграмм: {user_info['tgnick']}\n" if user_info['tgnick'] != 'Unknown' else ''
            nick_line = f"Ник: @{user_info['nick']}\n" if user_info['nick'] != 'Unknown' else ''
            response = f"Имя: {user_info['name']}\n{tgnick_line}{nick_line}Инфо: {user_info['about']}"
            await message.answer(response)
        else:
            await message.answer(f"Информация о пользователе '{args[1]}' не найдена.")
