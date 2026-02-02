import logging
from aiogram import Router, types
from aiogram.filters import Command, Text
from tgbot.gspread_client import get_gspread_client

router = Router()
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# FSM-словарь для хранения состояния редактирования
edit_sessions = {}

def get_sheet():
    client = get_gspread_client()
    if client:
        return client.open("ourid").sheet1
    return None

@router.message(Command("google_tab"))
async def google_tab(message: types.Message):
    """Выводит всю таблицу с кнопками для редактирования каждой ячейки"""
    sheet = get_sheet()
    if not sheet:
        await message.answer("Не удалось подключиться к Google Sheets.")
        return

    records = sheet.get_all_records()
    headers = sheet.row_values(1)

    for i, record in enumerate(records, start=2):  # start=2, первая строка - заголовки
        buttons = []
        for key in headers:
            value = record.get(key, "")
            buttons.append(
                types.InlineKeyboardButton(
                    text=str(value),
                    callback_data=f"edit|{i}|{key}"
                )
            )
        keyboard = types.InlineKeyboardMarkup(row_width=len(buttons))
        keyboard.add(*buttons)
        await message.answer(f"Строка {i-1}:", reply_markup=keyboard)


@router.callback_query(lambda c: c.data.startswith("edit"))
async def edit_callback(callback: types.CallbackQuery):
    """Обработка нажатия на ячейку для редактирования"""
    _, row, column = callback.data.split("|")
    row = int(row)
    user_id = callback.from_user.id

    # Сохраняем сессию редактирования
    edit_sessions[user_id] = {"row": row, "column": column}
    await callback.message.answer(f"Введите новое значение для '{column}' (строка {row-1}):")
    await callback.answer()


@router.message()
async def save_new_value(message: types.Message):
    """Сохраняет новое значение в таблице после ввода пользователя"""
    user_id = message.from_user.id
    if user_id not in edit_sessions:
        return  # Нет активной сессии редактирования

    sheet = get_sheet()
    if not sheet:
        await message.answer("Не удалось подключиться к Google Sheets.")
        return

    session = edit_sessions[user_id]
    row = session["row"]
    column = session["column"]
    new_value = message.text.strip()

    # Получаем индекс колонки
    headers = sheet.row_values(1)
    try:
        col_index = headers.index(column) + 1  # Google Sheets начинается с 1
    except ValueError:
        await message.answer(f"Колонка '{column}' не найдена в таблице.")
        del edit_sessions[user_id]
        return

    # Обновляем таблицу
    try:
        sheet.update_cell(row, col_index, new_value)
        await message.answer(f"✅ Значение '{column}' в строке {row-1} обновлено на '{new_value}'!")
    except Exception as e:
        logging.error(f"Ошибка обновления Google Sheets: {e}")
        await message.answer("❌ Ошибка при обновлении таблицы. Попробуйте снова.")

    # Удаляем сессию редактирования
    del edit_sessions[user_id]
