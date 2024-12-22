import json
import logging
import os
from aiogram import Bot, Router, types
from aiogram.types import Message
import gspread
from google.auth.transport.requests import Request
from google.oauth2.service_account import Credentials

# Настроим логирование
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Инициализация роутера
router = Router()

# Получаем ключ из переменной окружения
creds_json = os.getenv('GOOGLE_SHEET_KEY')

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
def add_user_to_sheet(user_id: int, username: str):
    logging.info(f"Started adding user {username} ({user_id}) to Google Sheets.")
    client = get_gspread_client()
    if client is None:
        logging.error("Failed to authenticate with Google Sheets.")
        return
    try:
        sheet = client.open("ourid").sheet1
        if not is_user_exists(client, user_id):
            logging.info("User does not exist. Adding to sheet...")
            sheet.append_row([user_id, username])
            logging.info(f"User {username} ({user_id}) successfully added.")
        else:
            logging.info(f"User {username} ({user_id}) already exists.")
    except Exception as e:
        logging.error(f"An error occurred while adding the user: {e}")


# Обработчик для сообщений
@router.message()
async def handle_message(message: Message):
    logging.info("Received a new message.")
    user_id = message.from_user.id
    username = message.from_user.username or "Unknown"
    logging.info(f"Processing message from user {username} ({user_id}).")
    try:
        add_user_to_sheet(user_id, username)
    except Exception as e:
        logging.error(f"Error while processing message: {e}")
