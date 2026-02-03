import logging
from aiogram import Router, types
from aiogram.filters import Command, CommandStart

router = Router()
logging.basicConfig(level=logging.INFO)

WEBAPP_URL = "https://bot-virus-l2.vercel.app/google_tab"
BOT_USERNAME = "DDvirus_bot"  # ← ЗАМЕНИ на username бота, без @

ALLOWED_USER_IDS = {
    1141764502
}

# =========================
# Команда в группе / личке
# =========================
@router.message(Command("google_tab"))
async def google_tab(message: types.Message):
    user_id = message.from_user.id
    logging.info(f"/google_tab called by {user_id}")

    # 🔒 Проверка доступа
    if user_id not in ALLOWED_USER_IDS:
        await message.answer("⛔ У тебя нет доступа.")
        return

    # Кнопка, открывающая ЛС с ботом
    keyboard = types.InlineKeyboardMarkup(
        inline_keyboard=[
            [
                types.InlineKeyboardButton(
                    text="Открыть в боте",
                    url=f"https://t.me/DDvirus_bot?start=google_tab"
                )
            ]
        ]
    )

    await message.answer(
        "Для редактирования таблицы открой бота в личных сообщениях:",
        reply_markup=keyboard
    )


# =========================
# Обработка deep-link в ЛС
# =========================
@router.message(CommandStart())
async def start_handler(message: types.Message):
    user_id = message.from_user.id
    args = message.text.split(maxsplit=1)

    # интересует только start=google_tab
    if len(args) == 2 and args[1] == "google_tab":

        # 🔒 Проверка доступа
        if user_id not in ALLOWED_USER_IDS:
            await message.answer("⛔ У тебя нет доступа.")
            return

        keyboard = types.InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    types.InlineKeyboardButton(
                        text="Редактировать таблицу имен",
                        web_app=types.WebAppInfo(url=WEBAPP_URL)
                    )
                ]
            ]
        )

        await message.answer(
            "Открывай таблицу:",
            reply_markup=keyboard
        )
        return

    # обычный /start
    await message.answer("Привет!")
