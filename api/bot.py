from fastapi import FastAPI, Request
from tgbot import tgbot

app = FastAPI()

@app.post('/api/bot')
async def tgbot_webhook_route(request: Request):
    update_dict = await request.json()
    await tgbot.update_bot(update_dict)
    return ''
