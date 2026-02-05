import os
import asyncio
from config import config  # Используем конфигурацию для токена
from aiogram import Bot, Dispatcher, Router

from tgbot.handlers import router as handlers_router
from tgbot.handler_sbor import router as handler_sbor_router
from tgbot.handler_getidall import router as handler_getidall_router
from tgbot.google_sheets import router as google_sheets_router  # Новый роутер с /backup
from tgbot.google_sheets import add_user_to_sheet, fetch_data_from_sheet  # Импорт функций работы с Google Sheets
from tgbot.gspread_client import get_gspread_client
from tgbot.google_tab import router as google_tab_router

# Главный роутер
router = Router()
router.include_router(google_sheets_router)
router.include_router(google_tab_router)
router.include_router(handlers_router)  # Подключаем стандартные хендлеры
router.include_router(handler_sbor_router)
router.include_router(handler_getidall_router)

# Класс бота
class TGBot:
    def __init__(self, router: Router) -> None:
        token = os.getenv('TOKEN')
        self.bot = Bot(token)
        self.dp = Dispatcher()
        self.dp.include_router(router)  # Подключаем роутер
        self.webhook_url = config('WEBHOOK_URL')

    async def update_bot(self, update: dict) -> None:
        await self.dp.feed_raw_update(self.bot, update)
        await self.bot.session.close()

    async def set_webhook(self) -> None:
        await self.bot.set_webhook(self.webhook_url)
        print(f"Webhook set to {self.webhook_url}")

# Инициализация tgbot с импортированным router
tgbot = TGBot(router)

