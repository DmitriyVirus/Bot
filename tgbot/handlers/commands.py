import asyncio
import logging
from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command

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


@router.message(Command("fu"))
async def fu_handler(message: Message):
    caption, image_url = await asyncio.to_thread(get_fu_data)

    if not image_url:
        await message.answer("Картинка не найдена")
        return

    await message.answer_photo(
        image_url,
        caption=caption,
        parse_mode="Markdown"
    )


@router.message(Command("nakol"))
async def nakol_handler(message: Message):
    caption, video_url = await asyncio.to_thread(get_nakol_data)

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
    caption, video_url = await asyncio.to_thread(get_klaar_data)

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
    caption, image_url = await asyncio.to_thread(get_kris_data)

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
    welcome_text = await asyncio.to_thread(get_welcome)

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
    participants = fetch_participants()
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
                response += (
                    f"\nИмя: {user_info['name']}\n"
                    f"{f'Имя в телеграмм: {user_info['tgnick']}\n' if user_info['tgnick'] != 'Unknown' else ''}"
                    f"{f'Ник: @{user_info['nick']}\n' if user_info['nick'] != 'Unknown' else ''}"
                    f"Инфо: {user_info['about']}\n"
                )
        await message.answer(response)
    else:
        user_info = participants.get(name)
        if user_info:
            response = (
                f"Имя: {user_info['name']}\n"
                f"{f'Имя в телеграмм: {user_info['tgnick']}\n' if user_info['tgnick'] != 'Unknown' else ''}"
                f"{f'Ник: @{user_info['nick']}\n' if user_info['nick'] != 'Unknown' else ''}"
                f"Инфо: {user_info['about']}"
            )
            await message.answer(response)
        else:
            await message.answer(f"Информация о пользователе '{args[1]}' не найдена.")

