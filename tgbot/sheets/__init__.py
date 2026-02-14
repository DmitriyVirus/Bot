# Импортируем все роутеры из отдельных файлов
from .autoget import router as autoget_router
from .gspread_client import get_gspread_client
from .autoget import add_user_to_sheet
from aiogram import Router

# Импортируем функции для работы с Google Sheets
from .take_from_sheet import (
    get_info_column_by_header,
    get_bot_commands,
    get_bot_deb_cmd,
    fetch_participants,
    get_admins_records,
    get_welcome,
    get_hello,
    get_about_bot,
    get_hello_image,
    get_about_bot_image,
    get_cmd_info,
    get_fu_data,
    get_nakol_data,
    convert_drive_url,
    get_klaar_data,
    get_kris_data
)

# Создаём единый роутер для всех хэндлеров
router = Router()
router.include_router(autoget_router)

