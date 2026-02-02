import logging
from aiogram import Router, types
from aiogram.filters import Command
from tgbot.gspread_client import get_gspread_client

router = Router()
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# FSM-словарь для хранения состояния редактирования
edit_sessions = {}

ROWS_PER_PAGE = 5  # количество строк на страницу

def get_sheet():
    client = get_gspread_client()
    if client:
        return client.open("ourid").sheet1
    return None

@router.message(Command("google_tab"))
async def google_tab(message: types.Message):
    """
    /google_tab 1 - первые 5 строк
    /google_tab 2 - следующие 5 строк и т.д.
    """
    sheet = get_sheet()
    if not sheet:
        await message.answer("Не удалось подключиться к Google Sheets.")
        return

    # Получаем номер страницы из команды
    text = message.text.strip()
    parts = text.split()
    page = 1
    if len(parts) > 1 and parts[1].isdigit():
        page = int(parts[1])
        if page < 1:
            page = 1

    start_row = (page - 1) * ROWS_PER_PAGE + 2  # пропускаем заголовок
    end_row = start_row + ROWS_PER_PAGE

    records = sheet.get_all_records()
    headers = sheet.row_values(1)
    total_rows = len(records)

    if start_row - 2 >= total_rows:
        await message.answer(f"❌ Страница {page} пуста. Всего строк: {total_rows}")
        return

    # Ограничиваем вывод страницей
    for i, record in enumerate(records[start_row - 2:end_row - 2], start=start_row):
        buttons = [
            types.InlineKeyboardButton(
                text=str(record.get(key, "")),
                callback_data=f"edit|{i}|{key}"
            )
            for key in headers
        ]
        keyboard = types.InlineKeyboardMarkup(row_width=len(buttons))
        keyboard.add(*buttons)
        await message.answer(f"Строка {i-1}:", reply_markup=keyboard)

    # Информация о страницах
    total_pages = (total_rows + ROWS_PER_PAGE - 1) // ROWS_PER_PAGE
    await message.answer(f"Страница {page}/{total_pages}. Всего строк: {total_rows}")


@router.callback_query(lambda c: c.data.startswith("edit"))
async def edit_callback(callback: types.CallbackQuery):
    """Обработка нажатия на ячейку для редактирования"""
    _, row, column = callback.data.split("|")
    row = int(row)
    user_id = callback.from_user.id

    edit_sessions[user_id] = {"row": row, "column": column}
    await callback.message.answer(f"Введите новое значение для '{column}' (строка {row-1}):")
    await callback.answer()


@router.message(lambda message: message.from_user.id in edit_sessions)
async def save_new_value(message: types.Message):
    """Сохраняет новое значение в таблице после ввода пользователя"""
    user_id = message.from_user.id
    session = edit_sessions[user_id]
    row = session["row"]
    column = session["column"]
    new_value = message.text.strip()

    sheet = get_sheet()
    if not sheet:
        await message.answer("Не удалось подключиться к Google Sheets.")
        return

    headers = sheet.row_values(1)
    try:
        col_index = headers.index(column) + 1
    except ValueError:
        await message.answer(f"Колонка '{column}' не найдена.")
        del edit_sessions[user_id]
        return

    try:
        sheet.update_cell(row, col_index, new_value)
        await message.answer(f"✅ Значение '{column}' в строке {row-1} обновлено на '{new_value}'!")
    except Exception as e:
        logging.error(f"Ошибка обновления Google Sheets: {e}")
        await message.answer("❌ Ошибка при обновлении таблицы. Попробуйте снова.")

    del edit_sessions[user_id]
