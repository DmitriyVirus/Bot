import json
import logging
import os
from dotenv import load_dotenv
from aiogram import Bot, Router, types
from aiogram.filters import Command
from aiogram.types import Message
import gspread
from google.auth.transport.requests import Request
from google.oauth2.service_account import Credentials

# Настроим логирование
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(asctime)s - %(message)s')

# Инициализация роутера
router = Router()

# Получаем ключ из переменной окружения
creds_json = os.getenv('GOOGLE_SHEET_KEY')
logging.info(f"GOOGLE_SHEET_KEY: {creds_json}")

if creds_json is None:
    logging.error("Google Sheets API key is missing. Make sure to set the GOOGLE_SHEET_KEY environment variable on Vercel.")
else:
    logging.info("Google Sheets API key found in environment variables.")

# Конфигурация для Google Sheets API
def get_gspread_client():
    try:
        logging.info("Attempting to authenticate with Google Sheets API.")
        
        if creds_json is None:
            logging.error("Google Sheets API key is missing.")
            return None
        
        credentials = Credentials.from_service_account_info(
            json.loads(creds_json),
            scopes=["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        )
        client = gspread.authorize(credentials)
        logging.info("Google Sheets API authentication successful.")
        return client
    except Exception as e:
        logging.error(f"Error while authenticating with Google Sheets API: {e}")
        return None

# Проверка, существует ли пользователь в таблице
def is_user_exists(client, user_id: int) -> bool:
    logging.info(f"Checking if user {user_id} exists in the sheet.")
    try:
        sheet = client.open("ourid").sheet1
        records = sheet.get_all_records()
        for record in records:
            if record.get('user_id') == user_id:
                logging.info(f"User {user_id} exists in the sheet.")
                return True
        logging.info(f"User {user_id} does not exist in the sheet.")
        return False
    except Exception as e:
        logging.error(f"Error while checking if user exists: {e}")
        return False

# Функция для добавления пользователя в таблицу
def add_user_to_sheet(user_id: int, username: str, first_name: str, last_name: str):
    logging.info(f"Started adding user {username} ({user_id}) to Google Sheets.")
    client = get_gspread_client()
    if client is None:
        logging.error("Failed to authenticate with Google Sheets.")
        return
    try:
        sheet = client.open("ourid").sheet1
        # Проверяем, существует ли пользователь
        if is_user_exists(client, user_id):
            logging.info(f"User {user_id} already exists. No action needed.")
            return  # Никаких действий не требуется
        
        # Если пользователь не существует, добавляем его с дефолтными значениями
        logging.info("User does not exist. Adding to sheet...")
        sheet.append_row([
            user_id,         # user_id
            username,        # username
            first_name,      # first_name
            last_name,       # last_name
            "выясняем",      # name
            "выясняем",      # aliases
            "выясняем"       # about
        ])
        logging.info(f"User {username} ({user_id}) successfully added with default data.")
    except Exception as e:
        logging.error(f"An error occurred while adding the user: {e}")

# Функция для получения данных из Google Таблицы
def fetch_data_from_sheet(client):
    """
    Загружает данные из Google Sheets и преобразует их в таблицу с алиасами.
    """
    try:
        sheet = client.open("ourid").sheet1
        records = sheet.get_all_records()
        expanded_table = {}

        for record in records:
            # Генерируем tgnick
            first_name = record["first_name"]
            last_name = record["last_name"]
            tgnick = f"{first_name} {last_name}".strip() if first_name.lower() != "unknown" or last_name.lower() != "unknown" else "Unknown"

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

# Обработчик для сообщений
@router.message()
async def handle_message(message: Message):
    logging.info("Received a new message.")
    user_id = message.from_user.id
    username = message.from_user.username or "Unknown"
    first_name = message.from_user.first_name or "Unknown"
    last_name = message.from_user.last_name or "Unknown"
    
    logging.info(f"Processing message from user {username} ({user_id}).")
    try:
        add_user_to_sheet(user_id, username, first_name, last_name)
    except Exception as e:
        logging.error(f"Error while processing message: {e}")
