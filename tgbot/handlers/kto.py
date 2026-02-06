import logging
from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from tgbot.gspread_client import get_gspread_client

router = Router()
logging.basicConfig(level=logging.INFO)

SHEET_NAME = "DareDevils"
WORKSHEET_NAME = "ID"


# Функция для получения данных из Google Таблицы
def fetch_data_from_sheet(client):
    """
    Загружает данные из Google Sheets и преобразует их в таблицу с алиасами.
    """
    try:
        sheet = client.open("DareDevils").worksheet("ID")
        records = sheet.get_all_records()
        expanded_table = {}

        for record in records:
            # Генерируем tgnick: если first_name или last_name unknown, то не выводим их
            first_name = record["first_name"]
            last_name = record["last_name"]

            if first_name.lower() == "unknown" and last_name.lower() == "unknown":
                tgnick = "Unknown"
            elif first_name.lower() == "unknown":
                tgnick = last_name.strip()
            elif last_name.lower() == "unknown":
                tgnick = first_name.strip()
            else:
                tgnick = f"{first_name} {last_name}".strip()

            # Собираем данные для пользователя
            user_data = {
                "name": record["name"],
                "tgnick": tgnick,
                "nick": record["username"],
                "about": record["about"]
            }

            # Добавляем данные в таблицу
            expanded_table[record["name"].lower()] = user_data

            # Если у пользователя есть алиасы, добавляем их
            if record["aliases"]:
                aliases = [alias.strip().lower() for alias in record["aliases"].split(",")]
                for alias in aliases:
                    expanded_table[alias] = user_data

        return expanded_table
    except Exception as e:
        logging.error(f"Error while fetching data from Google Sheets: {e}")
        return {}

@router.message(Command(commands=["kto"]))
async def who_is_this(message: Message):
    client = get_gspread_client()
    if not client:
        await message.answer("Ошибка подключения к Google Sheets.")
        return

    # Загружаем данные из Google Sheets
    expanded_table = fetch_data_from_sheet(client)
    if not expanded_table:
        await message.answer("Ошибка загрузки данных из Google Sheets.")
        return

    # Разделяем команду и аргумент
    args = message.text.split(' ', 1)

    # Если аргумент не указан
    if len(args) < 2:
        await message.answer("Пожалуйста, укажите имя после команды или 'all' для всех.")
        return

    name = args[1].strip().lower()

    # Если введено 'all', показываем информацию о всех пользователях
    if name == "all":
        response = "Список всех пользователей:\n"
        for user_name, user_info in expanded_table.items():
            if user_name == user_info["name"].lower():  # Уникальные записи
                response += (
                    f"\nИмя: {user_info['name']}\n"
                    f"{f'Имя в телеграмм: {user_info["tgnick"]}\n' if user_info['tgnick'] != 'Unknown' else ''}"
                    f"{f'Ник: @{user_info["nick"]}\n' if user_info['nick'] != 'Unknown' else ''}"
                    f"Инфо: {user_info['about']}\n"
                )
        await message.answer(response)
    else:
        # Ищем конкретного пользователя
        user_info = expanded_table.get(name)
        if user_info:
            response = (
                f"Имя: {user_info['name']}\n"
                f"{f'Имя в телеграмм: {user_info["tgnick"]}\n' if user_info['tgnick'] != 'Unknown' else ''}"
                f"{f'Ник: @{user_info["nick"]}\n' if user_info['nick'] != 'Unknown' else ''}"
                f"Инфо: {user_info['about']}"
            )
            await message.answer(response)
        else:
            await message.answer(f"Информация о пользователе '{args[1]}' не найдена.")

