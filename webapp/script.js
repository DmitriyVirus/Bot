from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
import os
import json
from tgbot.gspread_client import get_gspread_client
from tgbot import tgbot

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/", include_in_schema=False)
async def root():
    return FileResponse(os.path.join(os.getcwd(), "index.html"))

@app.post("/api/bot")
async def telegram_webhook(request: Request):
    update = await request.json()
    await tgbot.update_bot(update)
    return {}

@app.get("/api/get_sheet")
async def get_sheet():
    sheet = get_gspread_client().open("ourid").sheet1
    return sheet.get_all_records()

@app.post("/api/update_sheet")
async def update_sheet(request: Request):
    updates = await request.json()

    sheet = get_gspread_client().open("ourid").sheet1
    headers = sheet.row_values(1)
    records = sheet.get_all_records()

    updated_count = 0

    for upd in updates:
        uid = str(upd.get("user_id"))

        for i, row in enumerate(records):
            if str(row.get("user_id")) == uid:
                real_row = i + 2

                for key in ("name", "aliases", "about"):
                    if key in upd:
                        col = headers.index(key) + 1
                        sheet.update_cell(real_row, col, upd[key])

                updated_count += 1
                break

    return JSONResponse({
        "status": "ok",
        "updated": updated_count
    })

@app.post("/api/delete_row")
async def delete_row(request: Request):
    data = await request.json()
    uid = str(data.get("user_id"))

    sheet = get_gspread_client().open("ourid").sheet1
    records = sheet.get_all_records()

    for i, row in enumerate(records):
        if str(row.get("user_id")) == uid:
            sheet.delete_row(i + 2)
            return {"status": "deleted"}

    raise HTTPException(status_code=404, detail="User not found")
