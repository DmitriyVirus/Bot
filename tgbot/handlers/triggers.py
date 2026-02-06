import logging
from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command

from tgbot.triggers import TRIGGERS, COMMANDS_LIST, WELCOME_TEXT

router = Router()
logger = logging.getLogger(__name__)


@router.message(Command("help"))
async def help_cmd(message: Message):
    await message.answer(
        "\n".join(COMMANDS_LIST),
        parse_mode="Markdown"
    )


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
