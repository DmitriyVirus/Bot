import logging
import asyncio
from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command

from tgbot.triggers import TRIGGERS, COMMANDS_LIST, WELCOME_TEXT
from tgbot.sheets.take_from_sheet import get_fu_data, get_nakol_data, convert_drive_url


router = Router()
logger = logging.getLogger(__name__)

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
    # получаем подпись и ссылку на видео
    caption, video_url = await asyncio.to_thread(get_nakol_data)

    if not video_url:
        await message.answer("Видео не найдено")
        return

    # конвертируем Google Drive ссылку в прямую, если нужно
    video_url = convert_drive_url(video_url)

    # отправляем видео с подписью
    await message.answer_video(
        video_url,
        caption=caption,
        parse_mode="Markdown"
    )

# ===== КОМАНДА /klaar =====
@router.message(Command(commands=["klaar"]))
async def klaar_handler(message: Message):
    video_file_id = "BAACAgIAAxkBAAM7aXYW5bPrARfNhJmmEm99P7U-E2UAAiyPAAImO7FLQnyALHSZCl84BA"
    try:
        await message.answer_video(video_file_id)
        print(f"Видео отправлено пользователю {message.from_user.id}")
    except Exception as e:
        await message.answer(f"Ошибка при отправке видео: {e}")
        print(f"Ошибка при отправке видео: {e}")


# ===== КОМАНДА /kris =====
@router.message(Command(commands=["kris"]))
async def kris_handler(message: Message):
    photo_url = "https://i.redd.it/xces20zltm3b1.jpg"
    caption = "Спасайтесь, это Крис!"
    try:
        await message.answer_photo(photo_url, caption=caption)
        print(f"Изображение отправлено пользователю {message.from_user.id}")
    except Exception as e:
        await message.answer(f"Ошибка при отправке изображения: {e}")
        print(f"Ошибка при отправке изображения: {e}")


@router.message(Command("hi"))
async def hi(message: Message):
    await message.answer(WELCOME_TEXT, parse_mode="Markdown")


@router.message(lambda m: m.text and any(t in m.text.lower() for t in TRIGGERS))
async def triggers(message: Message):
    text = message.text.lower()
    for trigger, response in TRIGGERS.items():
        if trigger in text:
            if isinstance(response, dict):
                if "text" in response:
                    await message.answer(response["text"], parse_mode="Markdown")
                if "image" in response:
                    await message.answer_photo(response["image"])
                if "gif" in response:
                    await message.answer_animation(response["gif"])
            else:
                await message.answer(response, parse_mode="Markdown")
            break
