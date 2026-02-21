import os
import random
import datetime
import logging
import asyncio
from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command
from tgbot.redis.redis_cash import get_welcome

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
