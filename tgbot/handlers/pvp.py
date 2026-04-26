"""
tgbot/handlers/pvp.py

Логика PVP-трекера:
- Строка 1: Дата | Имя1 (2 колонки) | Имя2 (2 колонки) ...
- Строка 2: ""   | pvp | pc          | pvp | pc          ...
- Данные с строки 3.

Команды:
  /pvp 19/6   — записать pvp=19, pc=6
  /pvp        — дублировать предыдущую запись (или 0/0)
  /pvp_init   — одноразовая инициализация листа (только для админов)
  /pvp_log    — график pvp по времени
  /pc_log     — график pc по времени
"""

import os
import io
import logging
import asyncio
import datetime
from typing import Optional

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

from aiogram import Router, types
from aiogram.filters import Command
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from tgbot.sheets.gspread_client import get_gspread_client
from tgbot.redis.redis_cash import get_name, get_admins_records

logger = logging.getLogger(__name__)
router     = Router()
cron_router = APIRouter()

SHEET_NAME     = os.getenv("SHEET_NAME", "DareDevils")
CHAT_ID        = os.getenv("CHAT_ID")
CRON_SECRET    = os.getenv("CRON_SECRET", "")
ALERT_USERNAME = os.getenv("PVP_ALERT_USERNAME", "")
PVP_WORKSHEET  = "PVP"
ID_WORKSHEET   = "ID"
NO_DATA        = "нет данных"
ABSENT_DAYS    = 7

# Строки в листе
ROW_HEADERS  = 1   # Дата | Имя1 | "" | Имя2 | "" ...
ROW_SUBHEADS = 2   # ""   | pvp  | pc | pvp  | pc ...
ROW_DATA_START = 3

def _col_letter(n: int) -> str:
    """Конвертирует 1-based номер столбца в буквенное обозначение (1=A, 27=AA и т.д.)"""
    result = ''
    while n > 0:
        n, rem = divmod(n - 1, 26)
        result = chr(65 + rem) + result
    return result




# ==============================
# Подключение к листу
# ==============================

def _open_spreadsheet():
    client = get_gspread_client()
    if not client:
        raise RuntimeError("Не удалось подключиться к Google Sheets")
    return client.open(SHEET_NAME)


def _get_pvp_sheet():
    try:
        return _open_spreadsheet().worksheet(PVP_WORKSHEET)
    except Exception as e:
        logger.error(f"Ошибка открытия листа PVP: {e}")
        return None


def _today_str() -> str:
    return datetime.date.today().strftime("%d.%m.%Y")


# ==============================
# Чтение структуры листа
# ==============================

def _get_user_col(sheet, name: str) -> Optional[int]:
    """
    Возвращает 1-based номер столбца pvp для пользователя name,
    или None если пользователя нет.
    Структура: строка 1 = имя (объединяет 2 колонки), строка 2 = pvp | pc
    """
    row1 = sheet.row_values(ROW_HEADERS)
    for i, cell in enumerate(row1):
        if cell.strip() == name:
            return i + 1  # 1-based, это столбец pvp; pvp+1 = pc
    return None


def _add_user_columns(sheet, name: str) -> int:
    """
    Добавляет два столбца для нового пользователя в конец.
    Возвращает 1-based col_pvp.
    """
    row1 = sheet.row_values(ROW_HEADERS)
    # Ищем первый пустой после "Дата"
    next_col = len(row1) + 1
    for i in range(len(row1) - 1, -1, -1):
        if row1[i].strip():
            next_col = i + 2
            break

    col_pvp = next_col
    col_pc  = next_col + 1

    sheet.update_cell(ROW_HEADERS,  col_pvp, name)
    sheet.update_cell(ROW_HEADERS,  col_pc,  "")
    sheet.update_cell(ROW_SUBHEADS, col_pvp, "pvp")
    sheet.update_cell(ROW_SUBHEADS, col_pc,  "pc")
    try:
        sheet.merge_cells(
            f"{_col_letter(col_pvp)}{ROW_HEADERS}:{_col_letter(col_pc)}{ROW_HEADERS}"
        )
    except Exception as e:
        logger.warning(f"Не удалось объединить ячейки для {name}: {e}")

    return col_pvp


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
    return len(sheet.col_values(1))


def _get_last_values(sheet, col_pvp: int) -> tuple[str, str]:
    """Возвращает (last_pvp, last_pc) — последние непустые значения."""
    col_pc   = col_pvp + 1
    pvp_vals = sheet.col_values(col_pvp)[ROW_DATA_START - 1:]
    pc_vals  = sheet.col_values(col_pc)[ROW_DATA_START - 1:]

    last_pvp = last_pc = "0"
    for v in pvp_vals:
        if v and v != NO_DATA:
            last_pvp = v
    for v in pc_vals:
        if v and v != NO_DATA:
            last_pc = v
    return last_pvp, last_pc


# ==============================
# Инициализация листа
# ==============================

def init_pvp_sheet() -> tuple[bool, str]:
    """
    Создаёт лист PVP с правильной структурой и именами из листа ID.
    Одноразовая операция — если лист уже есть, возвращает ошибку.
    """
    try:
        ss = _open_spreadsheet()
    except Exception as e:
        return False, str(e)

    # Проверяем — лист уже есть?
    try:
        ss.worksheet(PVP_WORKSHEET)
        return False, "⚠️ Лист PVP уже существует. /pvp_init одноразовая команда."
    except Exception:
        pass  # листа нет — создаём

    # Читаем имена из ID
    try:
        id_sheet = ss.worksheet(ID_WORKSHEET)
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

    pvp_sheet = ss.add_worksheet(title=PVP_WORKSHEET, rows=1000, cols=200)

    # Строка 1: Дата | Имя1 | "" | Имя2 | "" ...
    row1 = ["Дата"]
    for name in names:
        row1.append(name)
        row1.append("")

    # Строка 2: "" | pvp | pc | pvp | pc ...
    row2 = [""]
    for _ in names:
        row2.append("pvp")
        row2.append("pc")

    pvp_sheet.append_row(row1)
    pvp_sheet.append_row(row2)

    # Объединяем ячейки имён в строке 1
    for i, name in enumerate(names):
        col_pvp = 2 + i * 2
        col_pc  = col_pvp + 1
        try:
            pvp_sheet.merge_cells(
                f"{_col_letter(col_pvp)}{ROW_HEADERS}:{_col_letter(col_pc)}{ROW_HEADERS}"
            )
        except Exception as e:
            logger.warning(f"Не удалось объединить ячейки для {name}: {e}")

    msg = f"✅ Лист PVP создан. Участники ({len(names)}): {', '.join(names)}"
    logger.info(msg)
    return True, msg


# ==============================
# Запись данных
# ==============================

def record_pvp(user_id: int, telegram_first_name: str,
               val_pvp: Optional[str], val_pc: Optional[str]) -> tuple[str, str, str]:
    """
    Записывает pvp/pc для пользователя на сегодня.
    val_pvp/val_pc = None → дублировать предыдущее (или 0).
    Возвращает (name, val_pvp, val_pc).
    """
    sheet = _get_pvp_sheet()
    if not sheet:
        raise RuntimeError("Лист PVP не найден. Сначала выполни /pvp_init")

    name = get_name(user_id, telegram_first_name)

    # Найти или создать столбцы пользователя
    col_pvp = _get_user_col(sheet, name)
    if col_pvp is None:
        col_pvp = _add_user_columns(sheet, name)

    col_pc = col_pvp + 1

    # Дублировать если не передано
    if val_pvp is None or val_pc is None:
        last_pvp, last_pc = _get_last_values(sheet, col_pvp)
        val_pvp = val_pvp or last_pvp
        val_pc  = val_pc  or last_pc

    today = _today_str()
    row   = _ensure_today_row(sheet, today)

    sheet.update_cell(row, col_pvp, val_pvp)
    sheet.update_cell(row, col_pc,  val_pc)

    return name, val_pvp, val_pc


# ==============================
# Ночная проверка (cron 4:00)
# ==============================

def fill_missing_pvp() -> list[str]:
    """
    Ставит NO_DATA тем кто не заполнил сегодня.
    Возвращает имена у кого 7 дней подряд нет данных.
    """
    sheet = _get_pvp_sheet()
    if not sheet:
        return []

    row1 = sheet.row_values(ROW_HEADERS)
    if not row1:
        return []

    today = _today_str()
    row   = _find_today_row(sheet, today)
    if not row:
        sheet.append_row([today])
        row = len(sheet.col_values(1))

    all_values = sheet.get_all_values()

    # Собираем пользователей: имя → (col_pvp_0based, col_pc_0based)
    user_cols = {}
    for i, cell in enumerate(row1):
        if i == 0 or not cell.strip():
            continue
        user_cols[cell.strip()] = (i, i + 1)

    absent_week = []

    for name, (ci_pvp, ci_pc) in user_cols.items():
        today_row = all_values[row - 1] if row - 1 < len(all_values) else []
        pvp_val = today_row[ci_pvp] if ci_pvp < len(today_row) else ""
        pc_val  = today_row[ci_pc]  if ci_pc  < len(today_row) else ""

        if not pvp_val and not pc_val:
            sheet.update_cell(row, ci_pvp + 1, NO_DATA)
            sheet.update_cell(row, ci_pc  + 1, NO_DATA)

        # Проверяем последние ABSENT_DAYS строк данных
        data_rows = all_values[ROW_DATA_START - 1:]
        if len(data_rows) >= ABSENT_DAYS:
            last_n = data_rows[-ABSENT_DAYS:]
            if all((r[ci_pvp] if ci_pvp < len(r) else "") == NO_DATA for r in last_n):
                absent_week.append(name)

    return absent_week


# ==============================
# Графики
# ==============================

def _build_chart(column_type: str) -> io.BytesIO:
    """
    column_type: 'pvp' или 'pc'
    """
    sheet = _get_pvp_sheet()
    if not sheet:
        raise RuntimeError("Лист PVP не найден")

    all_values = sheet.get_all_values()
    if len(all_values) < ROW_DATA_START:
        raise RuntimeError("Недостаточно данных для графика")

    row1      = all_values[ROW_HEADERS  - 1]
    row2      = all_values[ROW_SUBHEADS - 1]
    data_rows = all_values[ROW_DATA_START - 1:]

    # Парсим даты
    dates = []
    for row in data_rows:
        try:
            dates.append(datetime.datetime.strptime(row[0], "%d.%m.%Y"))
        except ValueError:
            dates.append(None)

    # Собираем пользователей и нужный столбец
    users = {}
    for i, cell in enumerate(row1):
        if i == 0 or not cell.strip():
            continue
        name = cell.strip()
        # Ищем нужный подзаголовок (pvp или pc)
        if i < len(row2) and row2[i].lower() == column_type:
            users[name] = i
        elif i + 1 < len(row2) and row2[i + 1].lower() == column_type:
            users[name] = i + 1

    def _parse(v):
        try:
            return float(v)
        except (ValueError, TypeError):
            return None

    # Строим данные
    series = {}
    for name, ci in users.items():
        vals = []
        for row in data_rows:
            vals.append(_parse(row[ci] if ci < len(row) else ""))
        series[name] = vals

    valid_dates = [d for d in dates if d is not None]

    fig, ax = plt.subplots(figsize=(14, 7))
    fig.patch.set_facecolor("#1e1e2e")
    ax.set_facecolor("#2a2a3e")
    ax.tick_params(colors="white")
    ax.yaxis.label.set_color("white")
    ax.title.set_color("white")
    ax.xaxis.label.set_color("white")
    for spine in ax.spines.values():
        spine.set_edgecolor("#555")

    colors    = plt.cm.tab20.colors
    color_map = {name: colors[i % len(colors)] for i, name in enumerate(series)}

    for name, vals in series.items():
        x = [valid_dates[i] for i, v in enumerate(vals) if v is not None and i < len(valid_dates)]
        y = [v for v in vals if v is not None]
        if x:
            ax.plot(x, y, marker="o", markersize=4, label=name,
                    color=color_map[name], linewidth=1.8)

    label = "PVP" if column_type == "pvp" else "PC"
    ax.set_title(f"График {label} по времени", fontsize=14, color="white")
    ax.set_ylabel(label, color="white")
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%d.%m"))
    ax.xaxis.set_major_locator(mdates.DayLocator(interval=2))
    plt.xticks(rotation=45, color="white")
    plt.yticks(color="white")
    ax.legend(fontsize=9, facecolor="#2a2a3e", labelcolor="white", framealpha=0.8)
    ax.grid(color="#444", linestyle="--", linewidth=0.5, alpha=0.5)

    plt.tight_layout()
    buf = io.BytesIO()
    plt.savefig(buf, format="png", dpi=130, bbox_inches="tight")
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

    val_pvp = val_pc = None

    if arg:
        if "/" in arg:
            sides = arg.split("/", 1)
            try:
                val_pvp = str(int(sides[0].strip()))
                val_pc  = str(int(sides[1].strip()))
            except ValueError:
                err = await message.answer("❌ Неверный формат. Используй: /pvp или /pvp 19/6")
                await asyncio.sleep(3)
                await message.delete()
                await err.delete()
                return
        else:
            err = await message.answer("❌ Неверный формат. Используй: /pvp или /pvp 19/6")
            await asyncio.sleep(3)
            await message.delete()
            await err.delete()
            return

    try:
        name, pvp, pc = await asyncio.to_thread(record_pvp, user_id, first_name, val_pvp, val_pc)
        confirm = await message.answer(f"✅ Добавлено")
        await message.delete()
        await asyncio.sleep(3)
        await confirm.delete()
    except Exception as e:
        logger.error(f"Ошибка записи PVP: {e}")
        err = await message.answer(f"❌ Ошибка: {e}")
        await asyncio.sleep(5)
        await message.delete()
        await err.delete()


@router.message(Command("pvp_init"))
async def pvp_init_handler(message: types.Message):
    admins = get_admins_records()
    if message.from_user.id not in admins:
        reply = await message.answer("⛔ Нет доступа.")
        await asyncio.sleep(3)
        await message.delete()
        await reply.delete()
        return

    msg = await message.answer("⏳ Создаю лист PVP...")
    try:
        ok, text = await asyncio.to_thread(init_pvp_sheet)
        await msg.edit_text(text)
    except Exception as e:
        logger.error(f"Ошибка pvp_init: {e}")
        await msg.edit_text(f"❌ Ошибка: {e}")


@router.message(Command("pvp_log"))
async def pvp_log_handler(message: types.Message):
    try:
        buf = await asyncio.to_thread(_build_chart, "pvp")
        await message.answer_photo(
            types.BufferedInputFile(buf.read(), filename="pvp_log.png"),
            caption="📊 График PVP по времени"
        )
    except Exception as e:
        logger.error(f"Ошибка pvp_log: {e}")
        await message.answer(f"❌ Не удалось построить график: {e}")


@router.message(Command("pc_log"))
async def pc_log_handler(message: types.Message):
    try:
        buf = await asyncio.to_thread(_build_chart, "pc")
        await message.answer_photo(
            types.BufferedInputFile(buf.read(), filename="pc_log.png"),
            caption="📊 График PC по времени"
        )
    except Exception as e:
        logger.error(f"Ошибка pc_log: {e}")
        await message.answer(f"❌ Не удалось построить график: {e}")


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
    """Каждый день в 4:00 — ставит нет данных, шлёт предупреждение."""
    _verify(request)
    try:
        absent_week = await asyncio.to_thread(fill_missing_pvp)

        if absent_week and CHAT_ID:
            from tgbot import tgbot
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
    """Раз в неделю — отправляет оба графика в чат."""
    _verify(request)
    try:
        if not CHAT_ID:
            return JSONResponse({"status": "error", "message": "CHAT_ID не задан"})

        from tgbot import tgbot

        for col_type, caption in [("pvp", "📊 Еженедельный график PVP"), ("pc", "📊 Еженедельный график PC")]:
            buf = await asyncio.to_thread(_build_chart, col_type)
            await tgbot.bot.send_photo(
                chat_id=int(CHAT_ID),
                photo=types.BufferedInputFile(buf.read(), filename=f"{col_type}_log.png"),
                caption=caption
            )

        return JSONResponse({"status": "ok", "message": "✅ Графики отправлены"})
    except Exception as e:
        logger.error(f"Ошибка cron_pvp_chart: {e}")
        return JSONResponse({"status": "error", "message": str(e)})
