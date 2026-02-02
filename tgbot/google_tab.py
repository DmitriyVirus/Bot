import logging
from aiogram import Router, types
from aiogram.filters import Command

router = Router()
logging.basicConfig(level=logging.INFO)

# Ссылка на веб-приложение
WEBAPP_URL = "https://bot-virus-l2.vercel.app/google_tab"

@router.message(Command("google_tab"))
async def google_tab(message: types.Message):
    """
    Отправляет кнопку для открытия Web App, где пользователь сможет редактировать таблицу.
    """
    logging.info(f"Handler /google_tab called by user {message.from_user.id}")

    webapp_button = types.WebAppInfo(url=WEBAPP_URL)
    keyboard = types.InlineKeyboardMarkup(
        inline_keyboard=[
            [types.InlineKeyboardButton(
                text="Редактировать таблицу имен",
                web_app=webapp_button
            )]
        ]
    )

    await message.answer(
        "Нажмите кнопку ниже, чтобы открыть таблицу для редактирования:",
        reply_markup=keyboard
    )
