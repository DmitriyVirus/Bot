from aiogram import Router
from .menu import router as menu_router
from .sbor import router as sbor_router
from .commands import router as commands_router
from .greetings import router as greetings_router



router = Router()
router.include_router(menu_router)
router.include_router(sbor_router)
router.include_router(commands_router)
router.include_router(greetings_router)
