import json
import gspread
import logging
from google.oauth2.service_account import Credentials
from aiogram import Router
from aiogram.types import Message
import asyncio

# Настроим логирование
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

router = Router()

# JSON-строка с данными учетных записей для Google Sheets
creds_json = '''{
  "type": "service_account",
  "project_id": "pro-pulsar-443515-f9",
  "private_key_id": "4c94cb45b5ef827d7116eeff9a95e3fa9190fb16",
  "private_key": "-----BEGIN PRIVATE KEY-----\nMIIEvAIBADANBgkqhkiG9w0BAQEFAASCBKYwggSiAgEAAoIBAQC0/5x3w3gvg/bN\nbVHzB8r3duXqIxdsxsZI1NcHjrwkywbUbfU3/XB7j4VCg0paGxYheWN1knwUWLNg\nxycbZ9YJ5qcwoMBAggGLQkrKvr4zySTDSgSOP23l7pv7RPBaTT9q5RMnFWMPWXlz\nrbXM+oiTeG8KUi9L5+mnYy/YVAaq3yEsEFQJ9o7RUJPrhJWJG2vGoa45ukE2UfnC\nFLvnYLJdzvrBhSf7VmVYbGIiYEdp46HXX2yFxtflRSUS9LoeuFJJkxAXwdsodl6T\nu612tZV/iJNnB88lhFPi3VX7Sa+rkWQKkFNdo7YhDVkfDwAObDtFSAyxv+gb1oEm\ncNViW+lTAgMBAAECggEAV8MnedTgdl2s8p/i4A4zxrkys0xvo9FgPNljKGl35flB\n5wgoIo1zmJ4XNhCWIUnH+dQzu0MbgfwegjsexcWb/bIG+GfBwKWpHP64aEWD0XVj\nK4Q84EJ2RcrkfDpJtueE7A6GMmnG3h766nHc2LbUOXlokh8Wit45J+5KuUDI+Nmm\nMDPFg/0FXMJpLfthR27cO7w25GsqK96Bf0dMYDxzFKd1EiQiJc7NXulB3Z/QIFrD\noJtd5HxZ7OJHjptxJaIIVqVaZpp0deITI3o+6KZDXfP9hYPT3Krod/LgIkWcE7Ng\nZD0BiSW3t+DuGskpdeiCaYDXv5VzYMoy3BZFsK4/oQKBgQDmUTb0YRQnHWueNbed\n18NMOYA5ujHSkgYBLLR39fcbnCkdqmfc3rB+2zQ9rgOvrWZ0eSsBgwmoWpliagc9\npleG5Q51Jwg+cXFKRUmwiy1IPcv5TzQPribopYtVDBtRDV4hr9y5FrUeFaqvnPnW\nhM6/vj3SjX3MLm+cUJ9qntj+swKBgQDJLoLatpZengc014v8UotA4NVFuEh3ep0P\nVuY2JZWpKeFeGTgsizils3F8phHkLKdb0OPl7TD0k+vvYTWCS0uSN7mZ8h2pz6/k\nDOwvwRyyjSZ1SgRveFdvq+cH/HSaaD7VvwgxT1xPU3o78tk+YL5DjuibeqES3c4L\nwWxU/BK64QKBgAGiV+J6AduZMNdJiEj9a+xRiCBgutPEp3hAqfMj8qHmhMAqIlyF\n0/jCc2dwoaQQdeajqXN0S5A/PFFfcTe1w284ltar9ToEMgqV3UT8Z9DYZ2cYccUe\ntjX2Xru2v0be8mkIx2ckyxowiyp90aP9Az6HCgdBa8AUIESaqdbm06FTAoGAFoEY\nbCTOj0j4H2YZJ6GIKDq+QK1LlenmVcfvupDbu++OYTtK+FiefpKjGEFvcOm50uB8\nDcVJm6JMWxuxo6COlI2dOmZGAS/VShpT9UeR0TtO2QHtmxaIGVrOXitUU81jcf+L\niBCLj+gTnU8eFAc4YVBEHthJ2lVrbg818g+8fKECgYBOl16zZr2M3MTnkS+espIx\nVfKjqi2eWbRZIWtqb/UE75ucfebM5LwJc7DdFflB+IfUbjEy//cKEAa4w6BeWBq8\nISfaZMfuKmFr6XavvXApeb2rX9FEc5bcsBODbsJxKLo1A0U8/cJljjseT7aPUrzz\nXt/fdttv/2N1DWa1Vfng5Q==\n-----END PRIVATE KEY-----\n",
  "client_email": "telegrambotserviceaccount@pro-pulsar-443515-f9.iam.gserviceaccount.com",
  "client_id": "107135112450702030216",
  "auth_uri": "https://accounts.google.com/o/oauth2/auth",
  "token_uri": "https://oauth2.googleapis.com/token",
  "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
  "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/telegrambotserviceaccount%40pro-pulsar-443515-f9.iam.gserviceaccount.com",
  "universe_domain": "googleapis.com"
}'''

# Конфигурация для Google Sheets API
def get_gspread_client():
    try:
        scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        creds = Credentials.from_service_account_info(json.loads(creds_json), scopes=scope)
        client = gspread.authorize(creds)
        logging.info("Successfully authenticated with Google Sheets API.")
        return client
    except Exception as e:
        logging.error(f"Error while authenticating with Google Sheets API: {e}")
        return None

# Проверка, существует ли пользователь в таблице
def is_user_exists(client, user_id: int) -> bool:
    try:
        sheet = client.open("ourid").sheet1
        records = sheet.get_all_records()
        for record in records:
            if record.get('user_id') == user_id:
                logging.info(f"User ID {user_id} already exists in the sheet.")
                return True
        logging.info(f"User ID {user_id} does not exist in the sheet.")
        return False
    except Exception as e:
        logging.error(f"Error while checking user existence: {e}")
        return False

# Функция для добавления пользователя в таблицу
def add_user_to_sheet(user_id: int, username: str):
    client = get_gspread_client()
    if client is None:
        logging.error("Failed to authenticate with Google Sheets.")
        return
    try:
        sheet = client.open("ourid").sheet1
        if not is_user_exists(client, user_id):
            sheet.append_row([user_id, username])
            logging.info(f"User {username} ({user_id}) added to Google Sheets.")
        else:
            logging.info(f"User {username} ({user_id}) already exists in Google Sheets.")
    except Exception as e:
        logging.error(f"An error occurred while adding the user: {e}")

# Асинхронная версия функции добавления пользователя
async def add_user_to_sheet_async(user_id: int, username: str):
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, add_user_to_sheet, user_id, username)

# Обработчик для сообщений
@router.message()
async def handle_message(message: Message):
    user_id = message.from_user.id
    username = message.from_user.username or "Unknown"  # Используем "Unknown", если username отсутствует
   
