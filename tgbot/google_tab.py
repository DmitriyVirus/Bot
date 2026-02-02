import logging
from aiogram import Router, types
from aiogram.filters import Command
from tgbot.gspread_client import get_gspread_client

router = Router()
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Сессии редактирования: user_id -> {row: int, edits: {column: new_value}}
edit_sessions = {}

def get_sheet():
    client = get_gspread_client()
    if client:
        return client.open("ourid").sheet1
    return None

@router.message(Command("google_tab"))
async def google_tab(message: types.Message):
    """Выводим первую строку и создаем сессию редактирования"""
    user_id = message.from_user.id
    sheet = get_sheet()
    if not sheet:
        await message.answer("Не удалось подключиться к Google Sheets.")
        return

    records = sheet.get_all_records()
    headers = sheet.row_values(1)

    if not records:
        await message.answer("Таблица пуста.")
        return

    record = records[0]  # Первая строка
    row_index = 2        # индекс в Google Sheets (1 — заголовки)

    # Инициализируем сессию
    edit_sessions[user_id] = {"row": row_index, "edits": {}}

    text = "Редактирование строки 1:\n\n"
    keyboard = types.InlineKeyboardMarkup(row_width=1)

    for col in headers:
        value = record.get(col, "")
        text += f"{col}: {value}\n"
        keyboard.add(types.InlineKeyboardButton(
            text=f"Изменить {col}",
            callback_data=f"edit|{col}"
        ))

    keyboard.add(types.InlineKeyboardButton(text="✅ ОК", callback_data="save"))
    await message.answer(text, reply_markup=keyboard)

@router.callback_query(lambda c: c.data.startswith("edit"))
async def edit_column(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    col = callback.data.split("|")[1]

    if user_id not in edit_sessions:
        await callback.answer("Сессия редактирования не найдена.", show_alert=True)
        return

    # Сохраняем, что сейчас редактируется эта колонка
    edit_sessions[user_id]["current_col"] = col
    await callback.message.answer(f"Введите новое значение для {col}:")
    await callback.answer()

@router.message(lambda m: m.from_user.id in edit_sessions)
async def save_edit(message: types.Message):
    user_id = message.from_user.id
    session = edit_sessions[user_id]

    if "current_col" not in session:
        return  # пока не выбирали колонку для редактирования

    col = session["current_col"]
    session["edits"][col] = message.text.strip()
    del session["current_col"]

    await message.answer(f"Значение для {col} обновлено на '{session['edits'][col]}'.")

@router.callback_query(lambda c: c.data == "save")
async def save_row(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    if user_id not in edit_sessions:
        await callback.answer("Сессия редактирования не найдена.", show_alert=True)
        return

    session = edit_sessions[user_id]
    sheet = get_sheet()
    if not sheet:
        await callback.message.answer("Не удалось подключиться к Google Sheets.")
        return

    headers = sheet.row_values(1)
    row = session["row"]

    for col, new_value in session["edits"].items():
        try:
            col_index = headers.index(col) + 1
            sheet.update_cell(row, col_index, new_value)
        except Exception as e:
            logging.error(f"Ошибка обновления Google Sheets: {e}")
            await callback.message.answer(f"Ошибка при обновлении {col}.")

    await callback.message.answer("✅ Строка успешно обновлена!")
    del edit_sessions[user_id]
    await callback.answer()
