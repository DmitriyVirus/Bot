import asyncio
from aiogram import Bot, Dispatcher, Router
from config import config
from tgbot.handlers import router

class TGBot:
    def __init__(self, router: Router) -> None:
        self.token = config('TOKEN')
        self.webhook_url = config('WEBHOOK_URL')
        self.bot = Bot(self.token)
        self.dp = Dispatcher()
        self.dp.include_router(router)

    async def update_bot(self, update: dict) -> None:
        await self.dp.feed_raw_update(self.bot, update)

    async def set_webhook(self) -> None:
        await self.bot.set_webhook(self.webhook_url)

tgbot = TGBot(router)
