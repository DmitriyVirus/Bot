import os
from config import config
from aiogram import Bot, Dispatcher, Router

# Импорт новых роутеров
from tgbot.handlers.menu import router as menu_router
from tgbot.handlers.greetings import router as greetings_router
from tgbot.handlers.triggers import router as triggers_router

# Дополнительные роутеры
from tgbot.handler_sbor import router as handler_sbor_router
from tgbot.handler_getidall import router as handler_getidall_router
from tgbot.google_sheets import router as google_sheets_router  # с /backup
from tgbot.google_tab import router as google_tab_router

# Функции работы с Google Sheets
from tgbot.google_sheets import add_user_to_sheet, fetch_data_from_sheet
from tgbot.gspread_client import get_gspread_client

# ===== Главный роутер =====
router = Router()

# Подключение роутеров в логическом порядке
router.include_router(menu_router)         # /bot и меню
router.include_router(greetings_router)    # приветствие / прощание / goodmorning
router.include_router(triggers_router)     # триггеры и команды

router.include_router(google_tab_router)
router.include_router(handler_sbor_router)
router.include_router(google_sheets_router)
router.include_router(handler_getidall_router)

# ===== Класс бота =====
class TGBot:
    def __init__(self, router: Router) -> None:
        token = os.getenv('TOKEN')
        self.bot = Bot(token)
        self.dp = Dispatcher()
        self.dp.include_router(router)  # подключаем главный роутер
        self.webhook_url = config('WEBHOOK_URL')

    async def update_bot(self, update: dict) -> None:
        await self.dp.feed_raw_update(self.bot, update)
        await self.bot.session.close()

    async def set_webhook(self) -> None:
        await self.bot.set_webhook(self.webhook_url)
        print(f"Webhook установлен: {self.webhook_url}")


# ===== Инициализация бота =====
tgbot = TGBot(router)
