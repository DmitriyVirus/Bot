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
    Отправляет кнопку для открытия веб-сайта, где пользователь сможет редактировать таблицу.
    Работает в личке и в группах.
    """
    logging.info(f"Handler /google_tab called by user {message.from_user.id}")

    # Простая кнопка-ссылка вместо WebApp
    keyboard = types.InlineKeyboardMarkup(
        inline_keyboard=[
            [types.InlineKeyboardButton(
                text="Редактировать таблицу имен",
                url=WEBAPP_URL  # обычная ссылка вместо web_app
            )]
        ]
    )

    await message.answer(
        "Таблицы для редактирования:",
        reply_markup=keyboard
    )
