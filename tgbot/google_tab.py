import logging
from aiogram import Router, types
from aiogram.filters import Command
from tgbot.gspread_client import get_gspread_client

# Настройка логирования
logging.basicConfig(level=logging.INFO)

# Инициализация роутера
router = Router()

# -----------------------------
# Команда /google_tab
# -----------------------------
@router.message(Command("google_tab"))
async def google_tab(message: types.Message):
    """
    Выводит первую строку Google Таблицы, каждое значение в отдельной строке
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

        # Берём первую строку
        record = records[0]
        lines = [f"{key}: {record.get(key, '')}" for key in headers]

        # Формируем текст для отправки
        text = "\n".join(lines)
        await message.answer(text)

    except Exception as e:
        logging.error(f"Ошибка при получении данных из Google Sheets: {e}")
        await message.answer("Произошла ошибка при получении данных из таблицы.")
