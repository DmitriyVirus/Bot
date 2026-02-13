import os
import random
import datetime
import logging
import asyncio

from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command

from tgbot.sheets.take_from_sheet import get_welcome

router = Router()
logger = logging.getLogger(__name__)


@router.message(lambda m: m.new_chat_members)
async def greet(message: Message):
    # получаем текст из Google Sheets в отдельном потоке
    welcome_text = await asyncio.to_thread(get_welcome)

    for user in message.new_chat_members:
        if user.is_bot:
            continue

        text = (
            f"⚡⚡⚡Привет, *{user.first_name}*!⚡⚡⚡\n\n"
            f"{welcome_text}\n\n"
            f"Используй /bot"
        )

        await message.answer(text, parse_mode="Markdown")


@router.message(lambda m: m.left_chat_member)
async def goodbye(message: Message):
    user = message.left_chat_member
    if not user.is_bot:
        await message.answer(f"Прощай, {user.first_name}! 👋")


@router.message(Command("goodmornigeverydayGG"))
async def good_morning(message: Message):
    day = datetime.datetime.now().weekday()

    mapping = {
        0: ("Понедельник… держимся 💀", "mond_url.txt"),
        4: ("ПЯТНИЦА!!! 🎉", "fri_url.txt"),
        5: ("Выходныеее 😎", "weekend_url.txt"),
        6: ("Выходныеее 😎", "weekend_url.txt"),
    }

    text, file_name = mapping.get(
        day, ("Доброе утро ☀️", "workdays_url.txt")
    )

    path = os.path.join(os.getcwd(), "urls", file_name)
    if not os.path.exists(path):
        await message.answer("Файл не найден")
        return

    with open(path) as f:
        urls = [u.strip() for u in f if u.strip()]

    await message.answer_photo(
        random.choice(urls),
        caption=text
    )
