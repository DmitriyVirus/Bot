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
    records = sheet.get_all_records()

    for updated in data:
        uid = updated.get("user_id")
        if not uid:
            continue

        for i, row in enumerate(records):
            if row.get("user_id") == uid:
                real_row = i + 2
                for key in ["name", "aliases", "about"]:
                    if key in updated:
                        col = headers.index(key) + 1
                        sheet.update_cell(real_row, col, updated[key])
                break

    return JSONResponse({"message": "Сохранено"})


@app.post("/api/delete_row")
async def delete_row(request: Request):
    data = await request.json()
    user_id = data.get("user_id")

    if not user_id:
        raise HTTPException(status_code=400, detail="user_id required")

    sheet = get_gspread_client().open("ourid").sheet1
    records = sheet.get_all_records()

    for i, row in enumerate(records):
        if row.get("user_id") == user_id:
            sheet.delete_row(i + 2)
            return JSONResponse({"message": "Удалено"})

    raise HTTPException(status_code=404, detail="Не найден")
