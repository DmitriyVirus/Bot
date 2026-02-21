import os
import json
import time
import random
import asyncio
from tgbot import tgbot
from fastapi import FastAPI
from decouple import config
from pydantic import BaseModel
from aiogram import Bot, Router, types
from fastapi.staticfiles import StaticFiles
from fastapi import FastAPI, Request, HTTPException
from tgbot.sheets.gspread_client import get_gspread_client
from tgbot.redis.redis_cash import load_all_to_redis, redis, LAST_UPDATE_KEY
from fastapi.responses import FileResponse, JSONResponse, RedirectResponse, HTMLResponse
from .backupbot import router as backup_router
from .morning import router as morning_router


app = FastAPI()
app.include_router(backup_router)
app.include_router(morning_router)


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
        print("Received update:", json.dumps(update_dict, indent=4))
        await tgbot.update_bot(update_dict)
        return ''
    except Exception as e:
        print(f"Error processing update: {e}")
        return {"error": str(e)}

# ==============================
# Основной лист "ID" в DareDevils
# ==============================
@app.get("/api/get_sheet")
async def get_sheet():
    client = get_gspread_client()
    sheet = client.open("DareDevils").worksheet("ID")  # ← Явное открытие листа "ID"
    records = sheet.get_all_records()
    return JSONResponse(records)

@app.post("/api/update_sheet")
async def update_sheet(request: Request):
    data = await request.json()
    sheet = get_gspread_client().open("DareDevils").worksheet("ID")  # ← Явное открытие листа "ID"
    headers = sheet.row_values(1)

    for i, row in enumerate(data):
        row_index = i + 2  # строки начинаются со второй
        for key, value in row.items():
            if key in headers:
                col_index = headers.index(key) + 1
                sheet.update_cell(row_index, col_index, value)

    return JSONResponse({"message": "Данные успешно сохранены!"})

@app.post("/api/delete_row")
async def delete_row(request: Request):
    data = await request.json()
    row_index = data.get("row_index")

    if not row_index:
        raise HTTPException(status_code=400, detail="row_index required")

    sheet = get_gspread_client().open("DareDevils").worksheet("ID")  # ← Явное открытие листа "ID"
    sheet.delete_rows(row_index)
    return JSONResponse({"message": "Строка удалена"})

# ==============================
# Лист Админы
# ==============================
@app.get("/api/get_admins")
def get_admins():
    client = get_gspread_client()
    sheet = client.open("DareDevils").worksheet("Админы")
    return sheet.get_all_records()

@app.post("/api/delete_admin")
def delete_admin(data: dict):
    row_index = data["row_index"]
    client = get_gspread_client()
    sheet = client.open("DareDevils").worksheet("Админы")
    sheet.delete_rows(row_index)
    return {"status": "ok"}

@app.post("/api/add_admin")
def add_admin(data: dict):
    client = get_gspread_client()
    sheet = client.open("DareDevils").worksheet("Админы")
    sheet.append_row([data["id"], data["name"]])
    return {"status": "ok"}

# ==============================
# Лист Добавление
# ==============================
@app.get("/api/get_permissions")
def get_permissions():
    client = get_gspread_client()
    sheet = client.open("DareDevils").worksheet("Добавление")
    return sheet.get_all_records()

@app.post("/api/delete_permission")
def delete_permission(data: dict):
    row_index = data["row_index"]
    client = get_gspread_client()
    sheet = client.open("DareDevils").worksheet("Добавление")
    sheet.delete_rows(row_index)
    return {"status": "ok"}

@app.post("/api/add_permission")
def add_permission(data: dict):
    client = get_gspread_client()
    sheet = client.open("DareDevils").worksheet("Добавление")
    sheet.append_row([data["id"], data["name"]])
    return {"status": "ok"}


# ==============================
# Лист Автосбор
# ==============================

@app.get("/api/get_autosbor")
def get_autosbor():
    sheet = get_gspread_client().open("DareDevils").worksheet("Автосбор")
    all_values = sheet.get_all_values()

    if not all_values or len(all_values[0]) == 0:
        return JSONResponse([])

    num_rows = 7  # <<< изменено: теперь берём 7 строк, включая первую
    num_cols = len(all_values[0])  # количество колонок по первой строке
    result = []

    for col_index in range(num_cols):
        values = []
        for row_index in range(num_rows):
            row = all_values[row_index] if row_index < len(all_values) else []
            values.append(row[col_index] if col_index < len(row) else "")

        result.append({
            "name": f"Пачка {col_index + 1}",  # <<< изменено: динамический заголовок
            "values": values
        })

    return JSONResponse(result)


# ===== POST сохранение =====
@app.post("/api/save_autosbor")
async def save_autosbor(request: Request):
    data = await request.json()

    column_index = data.get("column_index")
    values = data.get("values")

    if column_index is None or not isinstance(values, list) or len(values) != 7:  # <<< изменено: 7 строк
        raise HTTPException(400)

    sheet = get_gspread_client().open("DareDevils").worksheet("Автосбор")

    for i, value in enumerate(values):
        sheet.update_cell(i + 1, column_index + 1, value)  # <<< изменено: включаем первую строку

    return JSONResponse({"status": "ok"})


# ==============================
# Крон/внешний вызов обновления Redis
# ==============================
@app.get("/api/cron/refresh_redis")
async def cron_refresh_redis():
    """
    Эндпоинт для крон-задачи.
    Вызывает обновление всех данных в Redis.
    """
    try:
        # Выполняем блокирующую функцию в отдельном потоке
        await asyncio.to_thread(load_all_to_redis)

        # Обновляем отметку последнего обновления
        redis.set(LAST_UPDATE_KEY, int(time.time()))

        return JSONResponse({"status": "ok", "message": "✅ Redis успешно обновлён!"})
    except Exception as e:
        return JSONResponse({"status": "error", "message": f"❌ Ошибка при обновлении Redis: {e}"})



