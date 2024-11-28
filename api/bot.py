from tgbot import tgbot
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles

app = FastAPI()

@app.get("/favicon.png")
async def favicon():
    return RedirectResponse(url="/static/favicon.png")

@app.on_event("startup")
async def on_startup():
    print("Setting webhook...")
    webhook_info = await tgbot.bot.get_webhook_info()
    if webhook_info.url != tgbot.webhook_url:
        await tgbot.set_webhook()
        print(f"Webhook set to {tgbot.webhook_url}")
    else:
        print("Webhook already set")
    
@app.get("/")
async def read_root():
    return {"message": "Привет, мир!"}


@app.post('/api/bot')
async def tgbot_webhook_route(request: Request):
    update_dict = await request.json()
    await tgbot.update_bot(update_dict)
    return ''
