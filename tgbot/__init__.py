import os
from config import config
from aiogram import Bot, Dispatcher, Router

# Роутеры
from tgbot.handlers import router as handlers_router
from tgbot.sheets import router as sheets_router
from tgbot.handler_sbor import router as handler_sbor_router
from tgbot.handler_getidall import router as handler_getidall_router
from tgbot.google_tab import router as google_tab_router
from tgbot.gspread_client import get_gspread_client

# Главный роутер
router = Router()

# Подключаем все роутеры
router.include_router(sheets_router)          # автодобавление пользователей
router.include_router(google_tab_router)
router.include_router(handlers_router)
router.include_router(handler_sbor_router)
router.include_router(handler_getidall_router)
router.include_router(google_sheets_router)


# Класс бота
class TGBot:
    def __init__(self, router: Router) -> None:
        token = os.getenv("TOKEN")
        if not token:
            raise RuntimeError("TOKEN is not set in environment variables")

        self.bot = Bot(token)
        self.dp = Dispatcher()
        self.dp.include_router(router)

        self.webhook_url = config("WEBHOOK_URL")

    async def update_bot(self, update: dict) -> None:
        await self.dp.feed_raw_update(self.bot, update)
        await self.bot.session.close()

    async def set_webhook(self) -> None:
        await self.bot.set_webhook(self.webhook_url)
        print(f"Webhook set to {self.webhook_url}")

# Инициализация бота
tgbot = TGBot(router)

