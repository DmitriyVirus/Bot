"""
api/sheets_api.py — REST-эндпоинты для работы с Google Sheets.
Вынесено из bot.py чтобы не смешивать webhook-логику с CRUD.
"""
import logging
from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import JSONResponse

from tgbot.sheets.gspread_client import get_gspread_client

logger = logging.getLogger(__name__)
router = APIRouter()


def _open_sheet(spreadsheet: str, worksheet: str):
    """Вспомогательная функция — открывает нужный лист."""
    return get_gspread_client().open(spreadsheet).worksheet(worksheet)


# ==============================
# Лист "ID"
# ==============================
@router.get("/api/get_sheet")
async def get_sheet():
    sheet   = _open_sheet("DareDevils", "ID")
    records = sheet.get_all_records()
    return JSONResponse(records)


@router.post("/api/update_sheet")
async def update_sheet(request: Request):
    data    = await request.json()
    sheet   = _open_sheet("DareDevils", "ID")
    headers = sheet.row_values(1)

    for i, row in enumerate(data):
        row_index = i + 2
        for key, value in row.items():
            if key in headers:
                col_index = headers.index(key) + 1
                sheet.update_cell(row_index, col_index, value)

    return JSONResponse({"message": "Данные успешно сохранены!"})


@router.post("/api/delete_row")
async def delete_row(request: Request):
    data      = await request.json()
    row_index = data.get("row_index")
    if not row_index:
        raise HTTPException(status_code=400, detail="row_index required")

    _open_sheet("DareDevils", "ID").delete_rows(row_index)
    return JSONResponse({"message": "Строка удалена"})


# ==============================
# Лист "Админы"
# ==============================
@router.get("/api/get_admins")
def get_admins():
    return _open_sheet("DareDevils", "Админы").get_all_records()


@router.post("/api/delete_admin")
def delete_admin(data: dict):
    _open_sheet("DareDevils", "Админы").delete_rows(data["row_index"])
    return {"status": "ok"}


@router.post("/api/add_admin")
def add_admin(data: dict):
    _open_sheet("DareDevils", "Админы").append_row([data["id"], data["name"]])
    return {"status": "ok"}


# ==============================
# Лист "Добавление"
# ==============================
@router.get("/api/get_permissions")
def get_permissions():
    return _open_sheet("DareDevils", "Добавление").get_all_records()


@router.post("/api/delete_permission")
def delete_permission(data: dict):
    _open_sheet("DareDevils", "Добавление").delete_rows(data["row_index"])
    return {"status": "ok"}


@router.post("/api/add_permission")
def add_permission(data: dict):
    _open_sheet("DareDevils", "Добавление").append_row([data["id"], data["name"]])
    return {"status": "ok"}


# ==============================
# Лист "Автосбор"
# ==============================
@router.get("/api/get_autosbor")
def get_autosbor():
    sheet      = _open_sheet("DareDevils", "Автосбор")
    all_values = sheet.get_all_values()

    if not all_values or len(all_values[0]) == 0:
        return JSONResponse([])

    num_rows = 7
    num_cols = len(all_values[0])
    result   = []

    for col_index in range(num_cols):
        values = []
        for row_index in range(num_rows):
            row = all_values[row_index] if row_index < len(all_values) else []
            values.append(row[col_index] if col_index < len(row) else "")
        result.append({"name": f"Пачка {col_index + 1}", "values": values})

    return JSONResponse(result)


@router.post("/api/save_autosbor")
async def save_autosbor(request: Request):
    data         = await request.json()
    column_index = data.get("column_index")
    values       = data.get("values")

    if column_index is None or not isinstance(values, list) or len(values) != 7:
        raise HTTPException(status_code=400)

    sheet = _open_sheet("DareDevils", "Автосбор")
    for i, value in enumerate(values):
        sheet.update_cell(i + 1, column_index + 1, value)

    return JSONResponse({"status": "ok"})
