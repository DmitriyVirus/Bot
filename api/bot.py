import os
import json
import random
from tgbot import tgbot
from fastapi import FastAPI
from decouple import config
from pydantic import BaseModel
from aiogram import Bot, Router, types
from fastapi.staticfiles import StaticFiles
from tgbot.gspread_client import get_gspread_client
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import FileResponse, JSONResponse, RedirectResponse, HTMLResponse

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
    return FileResponse(os.path.join(os.getcwd(), "index.html"))

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

@app.get("/api/get_sheet")
async def get_sheet():
    client = get_gspread_client()
    sheet = client.open("ourid").sheet1
    records = sheet.get_all_records()
    return JSONResponse(records)

@app.post("/api/update_sheet")
async def update_sheet(request: Request):
    data = await request.json()

    sheet = get_gspread_client().open("ourid").sheet1
    headers = sheet.row_values(1)

    for i, row in enumerate(data):
        row_index = i + 2  # ⬅️ КАК РАНЬШЕ

        for key, value in row.items():
            if key in headers:
                col_index = headers.index(key) + 1
                sheet.update_cell(row_index, col_index, value)

    return JSONResponse({"message": "Данные успешно сохранены!"})
