import os
import shutil
import subprocess
import datetime
from aiogram import Router, types
from aiogram.filters import Command
from pydrive2.auth import GoogleAuth
from pydrive2.drive import GoogleDrive

router = Router()

# Путь для временной папки
TEMP_DIR = "/tmp/Backup"

# Переменные окружения
GITHUB_REPO_URL = "https://github.com/DmitriyVirus/Bot"
BACKUP_FOLDER_ID = os.environ.get("BACKUP_FOLDER_ID")
CREDENTIALS_JSON = os.environ.get("GOOGLE_SHEET_KEY")  # можно положить JSON в проект

# Вспомогательные функции
def clone_repo():
    if os.path.exists(TEMP_DIR):
        shutil.rmtree(TEMP_DIR)
    os.makedirs(TEMP_DIR)
    subprocess.run(["git", "clone", GITHUB_REPO_URL, TEMP_DIR], check=True)

def create_archive():
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M")
    archive_name = f"/tmp/bot_backup_{timestamp}.zip"
    shutil.make_archive(archive_name.replace('.zip',''), 'zip', TEMP_DIR)
    return archive_name

def upload_to_gdrive(archive_name):
    gauth = GoogleAuth()
    gauth.ServiceAuthSettings['client_json_file'] = CREDENTIALS_JSON
    gauth.ServiceAuth()
    drive = GoogleDrive(gauth)

    file = drive.CreateFile({
        'title': os.path.basename(archive_name),
        'parents': [{'id': BACKUP_FOLDER_ID}]
    })
    file.SetContentFile(archive_name)
    file.Upload()

def cleanup(archive_name):
    if os.path.exists(TEMP_DIR):
        shutil.rmtree(TEMP_DIR)
    if os.path.exists(archive_name):
        os.remove(archive_name)

# Хендлер
@router.message(Command("backupbotnow"))
async def backup_now(message: types.Message):
    await message.answer("Начинаю бэкап репозитория...")
    try:
        clone_repo()
        archive_name = create_archive()
        upload_to_gdrive(archive_name)
        cleanup(archive_name)
        await message.answer("✅ Бэкап успешно создан и загружен на Google Диск!")
    except Exception as e:
        await message.answer(f"❌ Ошибка при бэкапе: {e}")
