from fastapi import FastAPI, Request
from tgbot import tgbot

app = FastAPI()

@app.get("/")
async def read_root():
    return {"message": "Привет, мир!"}


@app.post('/api/bot')
async def tgbot_webhook_route(request: Request):
    update_dict = await request.json()
    await tgbot.update_bot(update_dict)
    return ''
