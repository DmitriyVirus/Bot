import os
import json
import logging
from tgbot import tgbot
from decouple import config
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse, FileResponse

app = FastAPI()

# Монтируем директорию для статических файлов
app.mount("/static", StaticFiles(directory="static"), name="static")

# Установка webhook при старте
@app.on_event("startup")
async def on_startup():
    try:
        print("Setting webhook...")
        await tgbot.set_webhook()
    except Exception as e:
        print(f"Error setting webhook: {e}")

@app.on_event("shutdown")
async def on_shutdown():
    await tgbot.bot.session.close()
    print("Bot session closed.")

# Главная страница
@app.get("/", include_in_schema=False)
@app.head("/", include_in_schema=False)
async def read_root():
    return FileResponse(os.path.join(os.getcwd(), "static", "index.html"))
   
# Обработка webhook-запросов от Telegram
@app.post('/api/bot')
async def tgbot_webhook_route(request: Request):
    try:
        update_dict = await request.json()
        print("Received update:", json.dumps(update_dict, indent=4))  # Логирование обновления
        await tgbot.update_bot(update_dict)
        return ''
    except Exception as e:
        print(f"Error processing update: {e}")
        return {"error": str(e)}

# Обработка favicon
@app.get("/favicon.png", include_in_schema=False)
@app.head("/favicon.png", include_in_schema=False)
async def favicon():
    return FileResponse(os.path.join(os.getcwd(), "static", "favicon.ico"))


@app.get('/send_reminder', include_in_schema=False)
async def send_reminder():
    try:
        text = "Привет! Это ваше напоминание на будний день."
        photo_url = "https://upload.wikimedia.org/wikipedia/commons/thumb/4/42/Blue_sky%2C_white-gray_clouds.JPG/1920px-Blue_sky%2C_white-gray_clouds.JPG"
        # Отправка текста
        await tgbot.bot.send_message(chat_id=config('CHAT_ID'), text=text)
        # Отправка фото
        await tgbot.bot.send_photo(chat_id=config('CHAT_ID'), photo=photo_url)
        return {"status": "success", "message": "Reminder sent"}
    except Exception as e:
        logging.error(f"Ошибка при отправке напоминания: {e}")
        return {"status": "error", "message": str(e)}
        
