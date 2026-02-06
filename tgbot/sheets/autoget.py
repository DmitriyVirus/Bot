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
from tgbot.gspread_client import get_gspread_client

# Настроим логирование
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(asctime)s - %(message)s')

# Инициализация роутера
router = Router()

# Использование клиента
client = get_gspread_client()
if client:
    sheet = client.open("DareDevils").worksheet("ID")  # Явное открытие листа "ID"

# Проверка, существует ли пользователь в таблице
def is_user_exists(client, user_id: int) -> bool:
    logging.info(f"Checking if user {user_id} exists in the sheet.")
    try:
        sheet = client.open("DareDevils").worksheet("ID")
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
        sheet = client.open("DareDevils").worksheet("ID")
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
