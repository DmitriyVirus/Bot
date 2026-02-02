import logging
from aiogram import Router, types
from aiogram.filters import Command
from tgbot.gspread_client import get_gspread_client

router = Router()
logging.basicConfig(level=logging.INFO)

ROWS_PER_PAGE = 1  # показываем по одной строке (можно увеличить)

# FSM-словарь для хранения состояния редактирования
edit_sessions = {}

# -----------------------------
# Команда /google_tab
# -----------------------------
@router.message(Command("google_tab"))
async def google_tab(message: types.Message):
    await send_row(message, row_number=2)  # row 1 = заголовки, row 2 = первая строка


# -----------------------------
# Функция для отправки строки
# -----------------------------
async def send_row(message_or_callback, row_number: int, edit_text=None):
    """
    Отправляет указанную строку таблицы в сообщении с возможностью редактирования
    """
    client = get_gspread_client()
    if not client:
        await message_or_callback.answer("Ошибка подключения к Google Sheets.")
        return

    try:
        sheet = client.open("ourid").sheet1
        headers = sheet.row_values(1)
        all_rows = sheet.get_all_records()
        max_row_index = len(all_rows) + 1  # +1 для row_number (т.к. 1 = заголовки)

        if row_number < 2:
            row_number = 2
        elif row_number > max_row_index:
            row_number = max_row_index

        record_index = row_number - 2  # индекс в records
        record = all_rows[record_index] if 0 <= record_index < len(all_rows) else {}

        # Формируем текст сообщения
        text_lines = []
        for key in headers:
            value = record.get(key, "")
            if edit_text and key in edit_text:
                value = edit_text[key]
            text_lines.append(f"{key}: {value}")
        text_lines.append("\nВведите новые значения в формате 'Имя: НовоеЗначение'")
        text = "\n".join(text_lines)

        # Кнопки
        keyboard = types.InlineKeyboardMarkup(row_width=3)
        keyboard.add(
            types.InlineKeyboardButton("⬅ Назад", callback_data=f"prev|{row_number}"),
            types.InlineKeyboardButton("➡ Вперед", callback_data=f"next|{row_number}"),
            types.InlineKeyboardButton("✅ ОК", callback_data=f"ok|{row_number}")
        )

        # Отправка сообщения или редактирование существующего
        if isinstance(message_or_callback, types.CallbackQuery):
            await message_or_callback.message.edit_text(text, reply_markup=keyboard)
        else:
            await message_or_callback.answer(text, reply_markup=keyboard)

    except Exception as e:
        logging.error(f"Ошибка при отправке строки: {e}")
        await message_or_callback.answer("Произошла ошибка при получении данных из таблицы.")


# -----------------------------
# Callback: ОК
# -----------------------------
@router.callback_query(lambda c: c.data.startswith("ok"))
async def ok_callback(callback: types.CallbackQuery):
    client = get_gspread_client()
    if not client:
        await callback.message.answer("Ошибка подключения к Google Sheets.")
        return

    try:
        sheet = client.open("ourid").sheet1
        row_number = int(callback.data.split("|")[1])
        headers = sheet.row_values(1)
        old_record = sheet.row_values(row_number)

        # Берём текст из сообщения
        lines = callback.message.text.split("\n")
        new_values = {}
        for line in lines:
            if ": " in line:
                key, val = line.split(": ", 1)
                if key in headers:
                    new_values[key] = val.strip()

        # Обновляем только изменённые значения
        for i, key in enumerate(headers, start=1):
            old_val = old_record[i - 1] if i - 1 < len(old_record) else ""
            new_val = new_values.get(key, old_val)
            if old_val != new_val:
                sheet.update_cell(row_number, i, new_val)

        await callback.message.answer(f"✅ Строка {row_number-1} обновлена!")
        await callback.answer()

    except Exception as e:
        logging.error(f"Ошибка обновления Google Sheets: {e}")
        await callback.message.answer("❌ Ошибка при обновлении таблицы.")
        await callback.answer()


# -----------------------------
# Callback: Назад
# -----------------------------
@router.callback_query(lambda c: c.data.startswith("prev"))
async def prev_callback(callback: types.CallbackQuery):
    row_number = int(callback.data.split("|")[1])
    await send_row(callback, row_number=row_number - 1)


# -----------------------------
# Callback: Вперед
# -----------------------------
@router.callback_query(lambda c: c.data.startswith("next"))
async def next_callback(callback: types.CallbackQuery):
    row_number = int(callback.data.split("|")[1])
    await send_row(callback, row_number=row_number + 1)
