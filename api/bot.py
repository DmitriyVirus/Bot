from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from tgbot import tgbot

app = FastAPI()

# Монтируем директорию для статических файлов
app.mount("/static", StaticFiles(directory="static"), name="static")

# Обработка favicon
@app.get("/favicon.png", include_in_schema=False)
@app.head("/favicon.png", include_in_schema=False)
async def favicon():
    return RedirectResponse(url="/static/favicon.png")

# Установка webhook при старте
@app.on_event("startup")
async def on_startup():
    try:
        print("Setting webhook...")
        webhook_info = await tgbot.bot.get_webhook_info()
        if webhook_info.url != tgbot.webhook_url:
            await tgbot.set_webhook()
            print(f"Webhook set to {tgbot.webhook_url}")
        else:
            print("Webhook already set")
    except Exception as e:
        print(f"Error setting webhook: {e}")

# Главная страница
@app.get("/", include_in_schema=False)
@app.head("/", include_in_schema=False)
async def read_root():
    return {"message": "Привет, мир!"}


# Обработка webhook-запросов от Telegram
@app.post('/api/bot')
async def tgbot_webhook_route(request: Request):
    try:
        update_dict = await request.json()
        await tgbot.update_bot(update_dict)
        return ''
    except Exception as e:
        return {"error": str(e)}
