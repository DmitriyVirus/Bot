import asyncio
from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command

from tgbot.sheets.take_from_sheet import (
    get_fu_data,
    get_nakol_data,
    get_klaar_data,
    get_kris_data,
    get_welcome,
    convert_drive_url
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
async def hi(message: Message):
    welcome_text = await asyncio.to_thread(get_welcome)

    await message.answer(
        welcome_text,
        parse_mode="Markdown"
    )

@router.message(Command(commands=["getid"]))
async def send_chat_id(message: types.Message):
    chat_id = message.chat.id
    await message.answer(f"Ваш Chat ID: `{chat_id}`", parse_mode="Markdown")
    logging.info(f"Chat ID ({chat_id}) отправлен пользователю {message.from_user.id}")

