# Импортируем все роутеры из отдельных файлов
from .menu import router as menu_router
from .kto import router as kto_router
from .commands import router as commands_router
from .greetings import router as greetings_router
from .sbor import router as sbor_router
from .kto import fetch_data_from_sheet
from aiogram import Router

# Создаём единый роутер для всех хэндлеров
router = Router()
router.include_router(kto_router)
router.include_router(menu_router)
router.include_router(sbor_router)
router.include_router(commands_router)
router.include_router(greetings_router)
