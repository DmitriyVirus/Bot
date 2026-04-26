"""
tgbot/handlers/pvp.py

Функционал PVP-трекера:
- /pvp             — дублировать предыдущую запись (или 0/0 если первый раз)
- /pvp 20/30       — записать свои значения
- /pvp_chart       — отправить график в чат вручную
- /pvp_init        — создать лист PVP и заполнить участниками из ID (только для админов)
- cron 4:00        — проставить "нет данных" тем кто не написал,
                     предупредить в чат тех у кого 7 дней подряд "нет данных"
- cron еженедельно — отправить график всех участников в чат
"""

import os
import io
import logging
import datetime
import asyncio
from typing import Optional

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

from aiogram import Router, types
from aiogram.filters import Command
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from tgbot import tgbot
from tgbot.sheets.gspread_client import get_gspread_client
from tgbot.redis.redis_cash import get_name, get_admins_records

logger = logging.getLogger(__name__)
router = Router()
cron_router = APIRouter()

SHEET_NAME    = os.getenv("SHEET_NAME", "DareDevils")
CHAT_ID       = os.getenv("CHAT_ID")
CRON_SECRET   = os.getenv("CRON_SECRET", "")
ALERT_USERNAME = os.getenv("PVP_ALERT_USERNAME", "")  # ник кому слать алерт, например "Pavel1234455"
PVP_WORKSHEET = "PVP"
ID_WORKSHEET  = "ID"
NO_DATA       = "нет данных"
ABSENT_DAYS   = 7


# ==============================
# Вспомогательные
# ==============================

def _get_pvp_sheet():
    client = get_gspread_client()
    if not client:
        return None
    try:
        return client.open(SHEET_NAME).worksheet(PVP_WORKSHEET)
    except Exception as e:
        logger.error(f"Ошибка открытия листа PVP: {e}")
        return None


def _today_str() -> str:
    return datetime.date.today().strftime("%d.%m.%Y")


def _ensure_pvp_sheet(sheet) -> list:
    headers = sheet.row_values(1)
    if not headers:
        sheet.append_row(["Дата"])
        headers = ["Дата"]
    return headers


def _ensure_user_columns(sheet, headers: list, name: str) -> tuple[int, int]:
    col_pc_header  = f"{name}_pc"
    col_pvp_header = f"{name}_pvp"

    if col_pc_header not in headers:
        next_col = len(headers) + 1
        sheet.update_cell(1, next_col,     col_pc_header)
        sheet.update_cell(1, next_col + 1, col_pvp_header)
        headers.append(col_pc_header)
        headers.append(col_pvp_header)

    col_pc  = headers.index(col_pc_header)  + 1
    col_pvp = headers.index(col_pvp_header) + 1
    return col_pc, col_pvp


def _find_today_row(sheet, today: str) -> Optional[int]:
    dates = sheet.col_values(1)
    for i, d in enumerate(dates):
        if d == today:
            return i + 1
    return None


def _ensure_today_row(sheet, today: str) -> int:
    row = _find_today_row(sheet, today)
    if row:
        return row
    sheet.append_row([today])
    dates = sheet.col_values(1)
    return len(dates)


def _get_last_values(sheet, col_pc: int, col_pvp: int) -> tuple[str, str]:
    col_pc_vals  = sheet.col_values(col_pc)
    col_pvp_vals = sheet.col_values(col_pvp)
    last_pc = last_pvp = "0"
    for v in col_pc_vals[1:]:
        if v and v != NO_DATA:
            last_pc = v
    for v in col_pvp_vals[1:]:
        if v and v != NO_DATA:
            last_pvp = v
    return last_pc, last_pvp


def _write_pvp(sheet, row: int, col_pc: int, col_pvp: int, val_pc: str, val_pvp: str):
    sheet.update_cell(row, col_pc,  val_pc)
    sheet.update_cell(row, col_pvp, val_pvp)


# ==============================
# Инициализация листа PVP
# ==============================

def init_pvp_sheet() -> tuple[bool, str]:
    """
    Создаёт лист PVP если его нет.
    Берёт имена из листа ID и добавляет столбцы Name_pc / Name_pvp.
    Если лист уже есть — добавляет только отсутствующих участников.
    """
    client = get_gspread_client()
    if not client:
        return False, "Не удалось подключиться к Google Sheets"

    try:
        spreadsheet = client.open(SHEET_NAME)
    except Exception as e:
        return False, f"Не удалось открыть таблицу {SHEET_NAME}: {e}"

    # Создаём лист PVP если нет
    try:
        pvp_sheet = spreadsheet.worksheet(PVP_WORKSHEET)
        created   = False
    except Exception:
        pvp_sheet = spreadsheet.add_worksheet(title=PVP_WORKSHEET, rows=1000, cols=200)
        created   = True
        logger.info("Лист PVP создан")

    # Читаем имена из листа ID
    try:
        id_sheet = spreadsheet.worksheet(ID_WORKSHEET)
        records  = id_sheet.get_all_records()
        names = [
            str(r["name"]).strip()
            for r in records
            if r.get("name") and str(r["name"]).strip() not in ("", "выясняем")
        ]
    except Exception as e:
        return False, f"Ошибка чтения листа ID: {e}"

    if not names:
        return False, "В листе ID нет участников с заполненным именем"

    # Читаем текущие заголовки
    headers = pvp_sheet.row_values(1)

    if not headers:
        # Лист пустой — пишем всё с нуля одним запросом
        header_row = ["Дата"]
        for name in names:
            header_row.append(f"{name}_pc")
            header_row.append(f"{name}_pvp")
        pvp_sheet.append_row(header_row)
        added = names
    else:
        # Лист уже есть — добавляем только новых участников
        existing = {h[:-3] for h in headers if h.endswith("_pc")}
        added    = []
        next_col = len(headers) + 1
        for name in names:
            if name not in existing:
                pvp_sheet.update_cell(1, next_col,     f"{name}_pc")
                pvp_sheet.update_cell(1, next_col + 1, f"{name}_pvp")
                next_col += 2
                added.append(name)

    action = "создан" if created else "обновлён"
    if added:
        msg = f"✅ Лист PVP {action}. Добавлены участники ({len(added)}): {', '.join(added)}"
    else:
        msg = f"✅ Лист PVP {action}. Новых участников нет."
    logger.info(msg)
    return True, msg


# ==============================
# Запись PVP
# ==============================

def record_pvp(user_id: int, telegram_first_name: str, val_pc: Optional[str], val_pvp: Optional[str]):
    sheet = _get_pvp_sheet()
    if not sheet:
        raise RuntimeError("Не удалось открыть лист PVP")

    name    = get_name(user_id, telegram_first_name)
    headers = _ensure_pvp_sheet(sheet)
    col_pc, col_pvp = _ensure_user_columns(sheet, headers, name)

    today = _today_str()
    row   = _ensure_today_row(sheet, today)

    if val_pc is None or val_pvp is None:
        last_pc, last_pvp = _get_last_values(sheet, col_pc, col_pvp)
        val_pc  = val_pc  or last_pc
        val_pvp = val_pvp or last_pvp

    _write_pvp(sheet, row, col_pc, col_pvp, val_pc, val_pvp)
    return name, val_pc, val_pvp


# ==============================
# Ночная проверка
# ==============================

def fill_missing_pvp() -> list[str]:
    sheet = _get_pvp_sheet()
    if not sheet:
        return []

    headers = sheet.row_values(1)
    if not headers:
        return []

    today = _today_str()
    row   = _find_today_row(sheet, today)
    if not row:
        sheet.append_row([today])
        row = len(sheet.col_values(1))

    all_values = sheet.get_all_values()

    user_cols = {}
    i = 1
    while i < len(headers):
        h = headers[i]
        if h.endswith("_pc") and i + 1 < len(headers) and headers[i + 1].endswith("_pvp"):
            user_cols[h[:-3]] = (i, i + 1)
            i += 2
        else:
            i += 1

    absent_week = []

    for name, (ci_pc, ci_pvp) in user_cols.items():
        today_row_data = all_values[row - 1] if row - 1 < len(all_values) else []
        pc_val  = today_row_data[ci_pc]  if ci_pc  < len(today_row_data) else ""
        pvp_val = today_row_data[ci_pvp] if ci_pvp < len(today_row_data) else ""

        if not pc_val and not pvp_val:
            sheet.update_cell(row, ci_pc  + 1, NO_DATA)
            sheet.update_cell(row, ci_pvp + 1, NO_DATA)

        data_rows = all_values[1:]
        if len(data_rows) >= ABSENT_DAYS:
            last_n = data_rows[-ABSENT_DAYS:]
            if all((r[ci_pc] if ci_pc < len(r) else "") == NO_DATA for r in last_n):
                absent_week.append(name)

    return absent_week


# ==============================
# График
# ==============================

def build_pvp_chart() -> io.BytesIO:
    sheet = _get_pvp_sheet()
    if not sheet:
        raise RuntimeError("Не удалось открыть лист PVP")

    all_values = sheet.get_all_values()
    if len(all_values) < 2:
        raise RuntimeError("Недостаточно данных для графика")

    headers   = all_values[0]
    data_rows = all_values[1:]

    dates = []
    for row in data_rows:
        try:
            dates.append(datetime.datetime.strptime(row[0], "%d.%m.%Y"))
        except ValueError:
            dates.append(None)

    users = {}
    i = 1
    while i < len(headers):
        h = headers[i]
        if h.endswith("_pc") and i + 1 < len(headers) and headers[i + 1].endswith("_pvp"):
            users[h[:-3]] = {"ci_pc": i, "ci_pvp": i + 1, "pc": [], "pvp": []}
            i += 2
        else:
            i += 1

    def _parse(v):
        try:
            return int(v)
        except (ValueError, TypeError):
            return None

    for row in data_rows:
        for name, d in users.items():
            d["pc"].append(_parse(row[d["ci_pc"]]  if d["ci_pc"]  < len(row) else ""))
            d["pvp"].append(_parse(row[d["ci_pvp"]] if d["ci_pvp"] < len(row) else ""))

    valid_dates = [d for d in dates if d is not None]

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 10), sharex=True)
    fig.patch.set_facecolor("#1e1e2e")
    for ax in (ax1, ax2):
        ax.set_facecolor("#2a2a3e")
        ax.tick_params(colors="white")
        ax.yaxis.label.set_color("white")
        ax.title.set_color("white")
        for spine in ax.spines.values():
            spine.set_edgecolor("#555")

    colors    = plt.cm.tab20.colors
    color_map = {name: colors[i % len(colors)] for i, name in enumerate(users)}

    for name, d in users.items():
        color = color_map[name]
        x_pc  = [valid_dates[i] for i, v in enumerate(d["pc"])  if v is not None and i < len(valid_dates)]
        y_pc  = [v for v in d["pc"]  if v is not None]
        x_pvp = [valid_dates[i] for i, v in enumerate(d["pvp"]) if v is not None and i < len(valid_dates)]
        y_pvp = [v for v in d["pvp"] if v is not None]
        if x_pc:
            ax1.plot(x_pc, y_pc, marker="o", markersize=4, label=name, color=color, linewidth=1.5)
        if x_pvp:
            ax2.plot(x_pvp, y_pvp, marker="o", markersize=4, label=name, color=color, linewidth=1.5)

    ax1.set_title("PVP — PC",  fontsize=13, color="white")
    ax2.set_title("PVP — PVP", fontsize=13, color="white")
    ax1.set_ylabel("Значение", color="white")
    ax2.set_ylabel("Значение", color="white")
    ax2.xaxis.set_major_formatter(mdates.DateFormatter("%d.%m"))
    ax2.xaxis.set_major_locator(mdates.DayLocator(interval=3))
    plt.xticks(rotation=45, color="white")

    handles, labels = ax1.get_legend_handles_labels()
    fig.legend(handles, labels, loc="upper right", fontsize=8,
               facecolor="#2a2a3e", labelcolor="white", framealpha=0.8)

    plt.tight_layout()
    buf = io.BytesIO()
    plt.savefig(buf, format="png", dpi=120, bbox_inches="tight")
    plt.close(fig)
    buf.seek(0)
    return buf


# ==============================
# Aiogram хендлеры
# ==============================

@router.message(Command("pvp"))
async def pvp_handler(message: types.Message):
    user_id    = message.from_user.id
    first_name = message.from_user.first_name or "Unknown"

    parts = message.text.strip().split(maxsplit=1)
    arg   = parts[1].strip() if len(parts) > 1 else ""

    val_pc = val_pvp = None

    if arg:
        if "/" in arg:
            sides = arg.split("/", 1)
            try:
                val_pc  = str(int(sides[0].strip()))
                val_pvp = str(int(sides[1].strip()))
            except ValueError:
                await message.answer("❌ Неверный формат. Используй: /pvp или /pvp 20/30")
                return
        else:
            await message.answer("❌ Неверный формат. Используй: /pvp или /pvp 20/30")
            return

    try:
        name, pc, pvp = await asyncio.to_thread(record_pvp, user_id, first_name, val_pc, val_pvp)
        await message.answer(f"✅ {name}: {pc} / {pvp} записано!")
    except Exception as e:
        logger.error(f"Ошибка записи PVP: {e}")
        await message.answer("❌ Ошибка при записи данных.")


@router.message(Command("pvp_init"))
async def pvp_init_handler(message: types.Message):
    """Создать/обновить лист PVP. Только для админов."""
    user_id = message.from_user.id
    admins  = get_admins_records()
    if user_id not in admins:
        await message.answer("⛔ Нет доступа.")
        return

    msg = await message.answer("⏳ Инициализирую лист PVP...")
    try:
        ok, text = await asyncio.to_thread(init_pvp_sheet)
        await msg.edit_text(text)
    except Exception as e:
        logger.error(f"Ошибка pvp_init: {e}")
        await msg.edit_text(f"❌ Ошибка: {e}")


@router.message(Command("pvp_chart"))
async def pvp_chart_handler(message: types.Message):
    try:
        buf = await asyncio.to_thread(build_pvp_chart)
        await message.answer_photo(
            types.BufferedInputFile(buf.read(), filename="pvp_chart.png"),
            caption="📊 График PVP"
        )
    except Exception as e:
        logger.error(f"Ошибка графика PVP: {e}")
        await message.answer("❌ Не удалось построить график.")


# ==============================
# Cron защита
# ==============================

def _verify(request: Request):
    if CRON_SECRET and request.headers.get("X-Cron-Secret") != CRON_SECRET:
        from fastapi import HTTPException
        raise HTTPException(status_code=403, detail="Forbidden")


# ==============================
# Cron эндпоинты
# ==============================

@cron_router.get("/api/cron/pvp_check")
async def cron_pvp_check(request: Request):
    """Каждый день в 4:00."""
    _verify(request)
    try:
        absent_week = await asyncio.to_thread(fill_missing_pvp)

        if absent_week and CHAT_ID:
            names_str = ", ".join(absent_week)
            mention   = f"@{ALERT_USERNAME} " if ALERT_USERNAME else ""
            await tgbot.bot.send_message(
                chat_id=int(CHAT_ID),
                text=f"{mention}те кто не следит за своей кармой — {names_str}"
            )

        return JSONResponse({"status": "ok", "absent_week": absent_week})
    except Exception as e:
        logger.error(f"Ошибка cron_pvp_check: {e}")
        return JSONResponse({"status": "error", "message": str(e)})


@cron_router.get("/api/cron/pvp_chart")
async def cron_pvp_chart(request: Request):
    """Раз в неделю."""
    _verify(request)
    try:
        if not CHAT_ID:
            return JSONResponse({"status": "error", "message": "CHAT_ID не задан"})
        buf = await asyncio.to_thread(build_pvp_chart)
        await tgbot.bot.send_photo(
            chat_id=int(CHAT_ID),
            photo=types.BufferedInputFile(buf.read(), filename="pvp_chart.png"),
            caption="📊 Еженедельный график PVP"
        )
        return JSONResponse({"status": "ok", "message": "✅ График отправлен"})
    except Exception as e:
        logger.error(f"Ошибка cron_pvp_chart: {e}")
        return JSONResponse({"status": "error", "message": str(e)})


@cron_router.get("/api/cron/pvp_init")
async def cron_pvp_init(request: Request):
    """Разовый вызов для создания листа PVP через cron или вручную."""
    _verify(request)
    try:
        ok, msg = await asyncio.to_thread(init_pvp_sheet)
        return JSONResponse({"status": "ok" if ok else "error", "message": msg})
    except Exception as e:
        logger.error(f"Ошибка cron_pvp_init: {e}")
        return JSONResponse({"status": "error", "message": str(e)})
