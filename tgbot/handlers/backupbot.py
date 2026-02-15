import os
import shutil
import datetime
import zipfile
import requests
import tempfile
import json
from aiogram import Router, types
from aiogram.filters import Command
from tgbot.sheets.gspread_client import creds_json
from pydrive2.auth import GoogleAuth
from pydrive2.drive import GoogleDrive

router = Router()

TEMP_DIR = "/tmp/Backup"
GITHUB_REPO_URL = "https://github.com/DmitriyVirus/Bot"
BACKUP_FOLDER_ID = os.environ.get("BACKUP_FOLDER_ID")

def download_repo_zip():
    zip_url = GITHUB_REPO_URL.rstrip('/') + "/archive/refs/heads/main.zip"
    zip_path = "/tmp/repo.zip"
    r = requests.get(zip_url, stream=True)
    r.raise_for_status()
    with open(zip_path, "wb") as f:
        for chunk in r.iter_content(1024):
            f.write(chunk)

    if os.path.exists(TEMP_DIR):
        shutil.rmtree(TEMP_DIR)
    os.makedirs(TEMP_DIR)

    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(TEMP_DIR)

    extracted_folder = os.path.join(TEMP_DIR, os.listdir(TEMP_DIR)[0])
    return extracted_folder

def create_archive(folder_path):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M")
    archive_name = f"/tmp/bot_backup_{timestamp}.zip"
    shutil.make_archive(archive_name.replace('.zip',''), 'zip', folder_path)
    return archive_name

def upload_to_gdrive(archive_name):
    if not creds_json:
        raise ValueError("Google Sheets API key is missing.")

    # Создаём временный файл с JSON сервисного аккаунта
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        f.write(creds_json)
        json_path = f.name

    # Настройка PyDrive2 через словарь
    gauth = GoogleAuth(settings={
        'client_config_backend': 'service',
        'client_config': json.load(open(json_path)),
        'save_credentials': False,
        'get_refresh_token': False,
        'oauth_scope': ['https://www.googleapis.com/auth/drive']
    })
    gauth.ServiceAuth()  # теперь без аргументов
    drive = GoogleDrive(gauth)

    file = drive.CreateFile({
        'title': os.path.basename(archive_name),
        'parents': [{'id': BACKUP_FOLDER_ID}]
    })
    file.SetContentFile(archive_name)
    file.Upload()

    os.remove(json_path)

def cleanup(archive_name):
    if os.path.exists(TEMP_DIR):
        shutil.rmtree(TEMP_DIR)
    if os.path.exists("/tmp/repo.zip"):
        os.remove("/tmp/repo.zip")
    if os.path.exists(archive_name):
        os.remove(archive_name)

@router.message(Command("backupbotnow"))
async def backup_now(message: types.Message):
    await message.answer("Начинаю бэкап репозитория...")
    try:
        repo_folder = download_repo_zip()
        archive_name = create_archive(repo_folder)
        upload_to_gdrive(archive_name)
        cleanup(archive_name)
        await message.answer("✅ Бэкап успешно создан и загружен на Google Диск!")
    except Exception as e:
        await message.answer(f"❌ Ошибка при бэкапе: {e}")
