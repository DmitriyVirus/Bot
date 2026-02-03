import logging
from aiogram import Router, types
from aiogram.filters import Command, CommandStart
from tgbot.gspread_client import get_gspread_client

router = Router()
logging.basicConfig(level=logging.INFO)

WEBAPP_URL = "https://bot-virus-l2.vercel.app/google_tab"
BOT_USERNAME = "DDvirus_bot"  # ← ЗАМЕНИ на username бота, без @

# =========================
# Проверка доступа по листу "Админы"
# =========================
def is_user_allowed(user_id: int) -> bool:
    """
    Проверяет, есть ли user_id во втором листе "Админы" Google Sheets.
    Лист должен содержать два столбца: 'id' и 'name'.
    """
    client = get_gspread_client()
    if not client:
        logging.warning("Google Sheets client not available")
        return False
    try:
        sheet = client.open("ourid").worksheet("Админы")
        records = sheet.get_all_records()
        for record in records:
            if str(record.get("id")) == str(user_id):
                logging.info(f"User {user_id} is allowed ({record.get('name')})")
                return True
        logging.info(f"User {user_id} is NOT allowed")
        return False
    except Exception as e:
        logging.error(f"Error checking allowed user: {e}")
        return False

# =========================
# Команда /google_tab
# =========================
@router.message(Command("google_tab"))
async def google_tab(message: types.Message):
    user_id = message.from_user.id
    logging.info(f"/google_tab called by {user_id}")

    if not is_user_allowed(user_id):
        await message.answer("⛔ У тебя нет доступа.")
        return

    keyboard = types.InlineKeyboardMarkup(
        inline_keyboard=[
            [
                types.InlineKeyboardButton(
                    text="Открыть в боте",
                    url=f"https://t.me/{BOT_USERNAME}?start=google_tab"
                )
            ]
        ]
    )

    await message.answer(
        "Для редактирования таблицы ТЫК:",
        reply_markup=keyboard
    )

# =========================
# Обработка deep-link /start
# =========================
@router.message(CommandStart())
async def start_handler(message: types.Message):
    user_id = message.from_user.id
    args = message.text.split(maxsplit=1)

    # Проверяем только deep-link start=google_tab
    if len(args) == 2 and args[1] == "google_tab":

        if not is_user_allowed(user_id):
            await message.answer("⛔ У тебя нет доступа.")
            return

        keyboard = types.InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    types.InlineKeyboardButton(
                        text="Редактировать таблицу участников",
                        web_app=types.WebAppInfo(url=WEBAPP_URL)
                    )
                ]
            ]
        )

        await message.answer(
            "Открывай таблицу:",
            reply_markup=keyboard
        )
