import logging
from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from tgbot.gspread_client import get_gspread_client

router = Router()
logging.basicConfig(level=logging.INFO)

SHEET_NAME = "DareDevils"
WORKSHEET_NAME = "ID"


def fetch_data_from_sheet():
    client = get_gspread_client()
    sheet = client.open(SHEET_NAME).worksheet(WORKSHEET_NAME)

    records = sheet.get_all_records()
    people = {}

    for row in records:
        name = row.get("name", "").strip()
        aliases = row.get("aliases", "")

        keys = [name.lower()] if name else []

        if aliases:
            keys.extend([a.strip().lower() for a in aliases.split(",")])

        for key in keys:
            people[key] = row

    return people


@router.message(Command("kto"))
async def kto_command(message: Message):
    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        await message.answer("Используй: /kto имя или /kto all")
        return

    query = args[1].lower()

    people = fetch_data_from_sheet()

    if query == "all":
        unique = {}
        for person in people.values():
            name = person.get("name", "Unknown")
            unique[name.lower()] = person

        text = "📋 Все участники:\n\n"
        for p in unique.values():
            text += f"• {p.get('name', 'Unknown')}\n"

        await message.answer(text)
        return

    person = people.get(query)
    if not person:
        await message.answer("❌ Человек не найден")
        return

    text = (
        f"👤 {person.get('name', 'Unknown')}\n"
        f"📛 @{person.get('username', '-')}\n"
        f"🆔 {person.get('user_id')}\n"
        f"📝 {person.get('about', '-')}"
    )

    await message.answer(text)
