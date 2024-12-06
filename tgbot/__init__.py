import asyncio
from config import config  # Используем конфигурацию для токена
from aiogram import Bot, Dispatcher, Router, types  # Добавляем импорт types
from tgbot.handlers import router as handlers_router  # Убедитесь, что импортируете router из handlers
from tgbot.handler_sbor import router as handler_sbor_router
from tgbot.handler_getidall import router as handler_getidall_router

router = Router()
router.include_router(handlers_router)  # Подключаем хендлеры
router.include_router(handler_sbor_router)
router.include_router(handler_getidall_router)

class TGBot:
    def __init__(self, router: Router) -> None:
        token = config('TOKEN')
        self.bot = Bot(token)
        self.dp = Dispatcher.from_bot(self.bot)  # Используем from_bot для создания Dispatcher
        self.dp.include_router(router)  # Подключаем роутер
        self.webhook_url = config('WEBHOOK_URL')

    async def update_bot(self, update: dict) -> None:
        # Преобразуем словарь обновления в объект типа Update
        update_obj = types.Update(**update)  # Преобразуем словарь в объект Update
        await self.dp.feed_update(update_obj)  # Передаем обновление для обработки

    async def set_webhook(self) -> None:
        await self.bot.set_webhook(self.webhook_url)
        print(f"Webhook set to {self.webhook_url}")

    async def close(self) -> None:
        await self.bot.close()  # Правильный способ закрытия сессии

    async def start_polling(self):
        # Теперь передаем bot в polling
        await self.dp.start_polling(self.bot)

# Инициализация tgbot с импортированным router
tgbot = TGBot(router)
