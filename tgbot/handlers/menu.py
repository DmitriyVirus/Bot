import os
import logging
from aiogram import Router, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from tgbot.sheets.take_from_sheet import (
    get_welcome_text,
    get_hello_text,
    get_about_bot_text,
    get_bot_commands,
    get_bot_deb_cmd,
    fetch_participants,
    get_admins_records,
    get_image_from_cell
)

router = Router()
logger = logging.getLogger(__name__)

WEBAPP_URL = os.environ.get("WEBAPP_URL")

# ===== ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ =====
def format_commands(commands):
    return "\n".join(commands)

def is_user_allowed(user_id: int) -> bool:
    records = get_admins_records()
    if not records:
        return False
    return any(str(record.get("id")) == str(user_id) for record in records)

# ===== КЛАВИАТУРЫ =====
def create_main_menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="👽 Участники чата", callback_data="menu_participants")],
        [InlineKeyboardButton(text="🤖 Команды для бота", callback_data="menu_commands")],
        [InlineKeyboardButton(text="ℹ️ Информация о боте", callback_data="menu_about_bot")]
    ])

def create_about_menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⚙️ Настройки", callback_data="menu_settings")],
        [InlineKeyboardButton(text="🏃 Назад", callback_data="back_to_main")]
    ])

def create_back_menu(back="back_to_main"):
    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="🏃 Назад", callback_data=back)]]
    )

def create_settings_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Редактировать таблицу участников", web_app=types.WebAppInfo(url=f"{WEBAPP_URL}/google_tab"))],
        [InlineKeyboardButton(text="Права добавления", web_app=types.WebAppInfo(url=f"{WEBAPP_URL}/permissions"))],
        [InlineKeyboardButton(text="Автосбор", web_app=types.WebAppInfo(url=f"{WEBAPP_URL}/autosbor"))],
        [InlineKeyboardButton(text="Админы", web_app=types.WebAppInfo(url=f"{WEBAPP_URL}/admins"))],
        [InlineKeyboardButton(text="🛠 Сервис", callback_data="menu_service")]
    ])

# ===== ХЕНДЛЕРЫ =====
@router.message(Command("bot"))
async def bot_menu(message: types.Message):
    welcome_text = get_welcome_text()
    image_url = get_image_from_cell("B20")

    if image_url:
        await message.answer_photo(photo=image_url, caption=welcome_text, reply_markup=create_main_menu())
    else:
        await message.answer(welcome_text, reply_markup=create_main_menu(), parse_mode="Markdown")

@router.callback_query(lambda c: c.data == "menu_participants")
async def participants(callback: types.CallbackQuery):
    expanded_table = fetch_participants()
    if not expanded_table:
        await callback.message.edit_text("Ошибка загрузки данных из Google Sheets.", reply_markup=create_back_menu())
        return

    response = "Список всех участников:\n"
    for user_name, user_info in expanded_table.items():
        if user_name == user_info["name"].lower():
            response += (
                f"\nИмя: {user_info['name']}\n"
                f"{f'Имя в телеграмм: {user_info['tgnick']}\n' if user_info['tgnick'] != 'Unknown' else ''}"
                f"{f'Ник: @{user_info['nick']}\n' if user_info['nick'] != 'Unknown' else ''}"
                f"Инфо: {user_info['about']}\n"
            )
    await callback.message.edit_text(response, reply_markup=create_back_menu())

@router.callback_query(lambda c: c.data == "menu_commands")
async def commands(callback: types.CallbackQuery):
    await callback.message.edit_text(format_commands(get_bot_commands()), reply_markup=create_back_menu())

@router.callback_query(lambda c: c.data == "menu_about_bot")
async def about_bot(callback: types.CallbackQuery):
    about_text = get_about_bot_text()
    await callback.message.edit_text(about_text, reply_markup=create_about_menu(), disable_web_page_preview=True)

@router.callback_query(lambda c: c.data == "menu_settings")
async def settings(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    if not is_user_allowed(user_id):
        await callback.answer("⛔ Нет доступа", show_alert=True)
        return
    await callback.bot.send_message(chat_id=user_id, text="Открывай таблицу:", reply_markup=create_settings_keyboard())
    await callback.answer()

@router.callback_query(lambda c: c.data == "menu_service")
async def service_menu(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    if not is_user_allowed(user_id):
        await callback.answer("⛔ Нет доступа", show_alert=True)
        return
    commands_text = "\n".join(get_bot_deb_cmd())
    await callback.message.edit_text(f"🛠 Сервисные команды:\n\n{commands_text}", reply_markup=create_back_menu("menu_settings"))

@router.callback_query(lambda c: c.data == "back_to_main")
async def back(callback: types.CallbackQuery):
    hello_text = get_hello_text()
    await callback.message.edit_text(hello_text, reply_markup=create_main_menu())
