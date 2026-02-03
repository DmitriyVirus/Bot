import logging
from aiogram import Router, types
from aiogram.filters import Command, CommandStart

router = Router()
logging.basicConfig(level=logging.INFO)

WEBAPP_URL = "https://bot-virus-l2.vercel.app/google_tab"
BOT_USERNAME = "DDvirus_bot"  # без @

ALLOWED_USER_IDS = {
    1141764502, 6392141586
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
        return  # тихо игнорируем

    # Кнопка, открывающая ЛС с ботом
    keyboard = types.InlineKeyboardMarkup(
        inline_keyboard=[[
            types.InlineKeyboardButton(
                text="Открыть в боте",
                url=f"https://t.me/{BOT_USERNAME}?start=google_tab"
            )
        ]]
    )

    # Отправляем только кнопку, без текста
    await message.answer(text="⠀", reply_markup=keyboard)  # "⠀" — пустой символ, чтобы сообщение не было пустым


# =========================
# Обработка deep-link в ЛС
# =========================
@router.message(CommandStart())
async def start_handler(message: types.Message):
    user_id = message.from_user.id
    args = message.text.split(maxsplit=1)

    # Проверяем только start=google_tab
    if len(args) == 2 and args[1] == "google_tab":
        if user_id not in ALLOWED_USER_IDS:
            return  # ничего не пишем

        keyboard = types.InlineKeyboardMarkup(
            inline_keyboard=[[
                types.InlineKeyboardButton(
                    text="Редактировать таблицу участников",
                    web_app=types.WebAppInfo(url=WEBAPP_URL)
                )
            ]]
        )

        # Только кнопка, без текста
        await message.answer(text="⠀", reply_markup=keyboard)
        return

    # обычный /start — для всех остальных
    await message.answer("Привет!")
