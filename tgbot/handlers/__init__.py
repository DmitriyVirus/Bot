# Импортируем все роутеры из отдельных файлов
from .menu import router as menu_router
from .kto import router as kto_router
from .adminka import router as adminka_router
from .getid import router as getid_router
from .triggers import router as triggers_router
from .greetings import router as greetings_router
from .sbor import router as sbor_router
from .kto import fetch_data_from_sheet
from aiogram import Router

# Создаём единый роутер для всех хэндлеров
router = Router()
router.include_router(kto_router)
router.include_router(menu_router)
router.include_router(getid_router)
router.include_router(sbor_router)
router.include_router(triggers_router)
router.include_router(greetings_router)
router.include_router(adminka_router)
