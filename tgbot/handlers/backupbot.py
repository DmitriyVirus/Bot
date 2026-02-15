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

def download_repo_zip():
    """Скачиваем репозиторий с GitHub как ZIP и распаковываем"""
    zip_url = GITHUB_REPO_URL.rstrip('/') + "/archive/refs/heads/main.zip"
    zip_path = "/tmp/repo.zip"

    # Скачиваем ZIP
    r = requests.get(zip_url, stream=True)
    r.raise_for_status()  # ошибка, если не получилось
    with open(zip_path, "wb") as f:
        for chunk in r.iter_content(1024):
            f.write(chunk)

    # Очистка TEMP_DIR и распаковка
    if os.path.exists(TEMP_DIR):
        shutil.rmtree(TEMP_DIR)
    os.makedirs(TEMP_DIR)

    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(TEMP_DIR)

    # GitHub архив создаёт папку с именем repo-main, возвращаем путь к ней
    extracted_folder = os.path.join(TEMP_DIR, os.listdir(TEMP_DIR)[0])
    return extracted_folder

def create_archive(folder_path):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M")
    archive_name = f"/tmp/bot_backup_{timestamp}.zip"
    shutil.make_archive(archive_name.replace('.zip',''), 'zip', folder_path)
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
    if os.path.exists("/tmp/repo.zip"):
        os.remove("/tmp/repo.zip")
    if os.path.exists(archive_name):
        os.remove(archive_name)

# Хендлер для команды
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
