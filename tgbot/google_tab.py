import logging
from aiogram import Router, types
from aiogram.filters import Command
from tgbot.gspread_client import get_gspread_client

router = Router()
logging.basicConfig(level=logging.INFO)

WEBAPP_URL = "https://bot-virus-l2.vercel.app/google_tab"  # сюда вставь ссылку на веб-приложение

@router.message(Command("google_tab"))
async def google_tab(message: types.Message):
    """
    Отправляет первую строку таблицы с кнопкой для открытия Web App
    """
    logging.info(f"Handler /google_tab called by user {message.from_user.id}")

    client = get_gspread_client()
    if not client:
        await message.answer("Ошибка подключения к Google Sheets.")
        return

    try:
        sheet = client.open("ourid").sheet1
        records = sheet.get_all_records()
        headers = sheet.row_values(1)

        if not records:
            await message.answer("Таблица пустая.")
            return

        record = records[0]  # берем первую строку
        text = "\n".join([f"{key}: {record.get(key, '')}" for key in headers])

        # Кнопка Web App
        webapp_button = types.WebAppInfo(url=WEBAPP_URL)
        keyboard = types.InlineKeyboardMarkup(
            inline_keyboard=[
                [types.InlineKeyboardButton(text="Редактировать первую строку", web_app=webapp_button)]
            ]
        )

        await message.answer(text, reply_markup=keyboard)

    except Exception as e:
        logging.error(f"Ошибка при получении данных из Google Sheets: {e}")
        await message.answer("Произошла ошибка при получении данных из таблицы.")
