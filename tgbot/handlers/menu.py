import os
import asyncio
import logging
from aiogram import Router, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from tgbot.sheets.take_from_sheet import fetch_participants
from tgbot.redis.redis_cash import (
    get_admins_records,
    get_hello,
    get_about_bot,
    get_hello_image,
    get_about_bot_image,
    get_cmd_info,
    get_bot_commands,
    get_bot_deb_cmd
)


router = Router()
WEBAPP_URL = os.environ.get("WEBAPP_URL")


# ===== ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ =====

async def safe_fetch(func, *args):
    """Асинхронный вызов блокирующих функций"""
    try:
        return await asyncio.to_thread(func, *args)
    except Exception as e:
        logging.exception(f"Ошибка при вызове {func.__name__}: {e}")
        return None


def format_commands(commands):
    return "\n".join(commands)


async def is_user_allowed(user_id: int) -> bool:
    records = await safe_fetch(get_admins_records)
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
        [InlineKeyboardButton(text="Редактировать таблицу участников",
                              web_app=WebAppInfo(url=f"{WEBAPP_URL}/google_tab"))],
        [InlineKeyboardButton(text="Права добавления",
                              web_app=WebAppInfo(url=f"{WEBAPP_URL}/permissions"))],
        [InlineKeyboardButton(text="Автосбор",
                              web_app=WebAppInfo(url=f"{WEBAPP_URL}/autosbor"))],
        [InlineKeyboardButton(text="Админы",
                              web_app=WebAppInfo(url=f"{WEBAPP_URL}/admins"))],
        [InlineKeyboardButton(text="🛠 Сервис", callback_data="menu_service")]
    ])


# ===== ХЕНДЛЕР /bot =====

@router.message(Command("bot"))
async def bot_menu(message: types.Message):
    image_url = await safe_fetch(get_hello_image)
    text = await safe_fetch(get_hello) or "Привет!"
    
    if image_url:
        await message.answer_photo(
            photo=image_url,
            caption=text,
            reply_markup=create_main_menu(),
            parse_mode="Markdown"
        )
    else:
        await message.answer(
            text,
            reply_markup=create_main_menu(),
            parse_mode="Markdown"
        )


# ===== CALLBACK ХЕНДЛЕРЫ =====

@router.callback_query(lambda c: c.data == "menu_participants")
async def participants(callback: types.CallbackQuery):
    expanded_table = await safe_fetch(fetch_participants)
    await callback.message.delete()

    if not expanded_table:
        await callback.message.answer(
            "Ошибка загрузки данных из Google Sheets.",
            reply_markup=create_back_menu()
        )
        return

    response = "Список всех участников:\n"
    for user_name, user_info in expanded_table.items():
        if user_name == user_info["name"].lower():
            tgnick_line = f"Имя в телеграмм: {user_info['tgnick']}\n" if user_info['tgnick'] != 'Unknown' else ''
            nick_line = f"Ник: @{user_info['nick']}\n" if user_info['nick'] != 'Unknown' else ''
            response += f"\nИмя: {user_info['name']}\n{tgnick_line}{nick_line}Инфо: {user_info['about']}\n"

    await callback.message.answer(
        response,
        reply_markup=create_back_menu()
    )


@router.callback_query(lambda c: c.data == "menu_commands")
async def commands(callback: types.CallbackQuery):
    await callback.message.delete()
    commands_list = await safe_fetch(get_bot_commands) or []
    extra_text = await safe_fetch(get_cmd_info) or ""
    full_text = f"{format_commands(commands_list)}\n\n{extra_text}"

    await callback.message.answer(
        full_text,
        reply_markup=create_back_menu(),
        disable_web_page_preview=True
    )


@router.callback_query(lambda c: c.data == "menu_about_bot")
async def about_bot(callback: types.CallbackQuery):
    await callback.message.delete()
    image_url = await safe_fetch(get_about_bot_image)
    text = await safe_fetch(get_about_bot) or "Информация о боте отсутствует."

    if image_url:
        await callback.message.answer_photo(
            photo=image_url,
            caption=text,
            reply_markup=create_about_menu(),
            parse_mode="Markdown"
        )
    else:
        await callback.message.answer(
            text,
            reply_markup=create_about_menu(),
            parse_mode="Markdown",
            disable_web_page_preview=True
        )


@router.callback_query(lambda c: c.data == "menu_settings")
async def settings(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    if not await is_user_allowed(user_id):
        await callback.answer("⛔ Нет доступа", show_alert=True)
        return

    await callback.message.delete()
    await callback.bot.send_message(
        chat_id=user_id,
        text="Открывай таблицу:",
        reply_markup=create_settings_keyboard()
    )
    await callback.answer()


@router.callback_query(lambda c: c.data == "menu_service")
async def service_menu(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    if not await is_user_allowed(user_id):
        await callback.answer("⛔ Нет доступа", show_alert=True)
        return

    commands_list = await safe_fetch(get_bot_deb_cmd) or []
    text = "\n".join(commands_list)

    await callback.message.delete()
    await callback.message.answer(
        f"🛠 Сервисные команды:\n\n{text}",
        reply_markup=create_back_menu("menu_settings")
    )


@router.callback_query(lambda c: c.data == "back_to_main")
async def back(callback: types.CallbackQuery):
    await callback.message.delete()
    image_url = await safe_fetch(get_hello_image)
    text = await safe_fetch(get_hello) or "Привет!"

    if image_url:
        await callback.message.answer_photo(
            photo=image_url,
            caption=text,
            reply_markup=create_main_menu(),
            parse_mode="Markdown"
        )
    else:
        await callback.message.answer(
            text,
            reply_markup=create_main_menu(),
            parse_mode="Markdown"
        )
