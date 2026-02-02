import logging
from aiogram import Router, types
from aiogram.filters import Command

router = Router()
logging.basicConfig(level=logging.INFO)

WEBAPP_URL = "https://bot-virus-l2.vercel.app/google_tab"

@router.message(Command("google_tab"))
async def google_tab(message: types.Message):
    logging.info(f"Handler /google_tab called by user {message.from_user.id}")

    # Создаем Web App кнопку
    keyboard = types.InlineKeyboardMarkup(
        inline_keyboard=[
            [types.InlineKeyboardButton(
                text="Редактировать таблицу имен",
                web_app=types.WebAppInfo(url=WEBAPP_URL)
            )]
        ]
    )

    if message.chat.type != "private":
        # Если команда вызвана в группе
        await message.reply(
            f"{message.from_user.mention}, я отправил тебе ссылку в личку для редактирования таблицы."
        )

    # Отправляем ссылку в личку пользователя
    await message.bot.send_message(
        chat_id=message.from_user.id,
        text="Таблицы для редактирования:",
        reply_markup=keyboard
    )
