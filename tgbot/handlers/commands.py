import asyncio
import logging
from aiogram import Router, types
from aiogram.types import Message
from aiogram.filters import Command
from api.backupbot import backup_repo 
from tgbot.sheets.take_from_sheet import fetch_participants
from tgbot.redis.redis_cash import (
    redis,
    refresh_redis,
    get_fu_data,
    get_nakol_data,
    get_klaar_data,
    get_kris_data,
    convert_drive_url,
    is_user_in_sheet,
    add_user_to_sheet_and_redis,
    load_all_to_redis,
    get_allowed_user_ids,
    get_name,
    get_welcome
)


router = Router()

@router.message(Command("exist"))
async def check_exist(message: types.Message):
    user_id = message.from_user.id
    username = message.from_user.username or "Unknown"
    first_name = message.from_user.first_name or "Unknown"
    last_name = message.from_user.last_name or "Unknown"

    if is_user_in_sheet(user_id):
        await message.answer("✅ Вы есть в таблице.")
    else:
        await message.answer("❌ Вас нет в таблице, добавляем...")
        await asyncio.to_thread(add_user_to_sheet_and_redis, user_id, username, first_name, last_name)
        await message.answer("✅ Пользователь добавлен!")


async def safe_fetch(func, *args):
    """Обёртка для безопасного вызова блокирующих функций в отдельном потоке"""
    try:
        return await asyncio.to_thread(func, *args)
    except Exception as e:
        logging.exception(f"Ошибка при вызове {func.__name__}: {e}")
        return None


@router.message(Command("refresh"))
async def refresh_redis_command(message: types.Message):
    """
    Хендлер для команды /refresh
    """
    sent_msg = await message.answer("Обновление Redis... ⏳")
    try:
        result_text = await refresh_redis()
        await sent_msg.edit_text(result_text)
    except Exception as e:
        await sent_msg.edit_text(f"❌ Ошибка при обновлении Redis: {e}")

@router.message(Command("backupbotnow"))
async def cmd_backupbotnow(message: types.Message):
    await message.reply("⚙️ Начинаю бэкап репозитория...")

    try:
        backup_repo()
        await message.reply("✅ Бэкап выполнен успешно!")
    except Exception as e:
        logger.exception("Ошибка при бэкапе")
        await message.reply(f"❌ Ошибка при бэкапе: {e}")


@router.message(Command("fu"))
async def fu_handler(message: Message):
    result = await safe_fetch(get_fu_data)
    if not result:
        await message.answer("Произошла ошибка при получении данных.")
        return

    caption, image_url = result
    if not image_url:
        await message.answer("Картинка не найдена")
        return

    image_url = convert_drive_url(image_url)

    await message.answer_photo(
        image_url,
        caption=caption,
        parse_mode="Markdown"
    )


@router.message(Command("nakol"))
async def nakol_handler(message: Message):
    result = await safe_fetch(get_nakol_data)
    if not result:
        await message.answer("Произошла ошибка при получении данных.")
        return

    caption, video_url = result
    if not video_url:
        await message.answer("Видео не найдено")
        return

    video_url = convert_drive_url(video_url)

    await message.answer_video(
        video_url,
        caption=caption,
        parse_mode="Markdown"
    )


@router.message(Command("klaar"))
async def klaar_handler(message: Message):
    result = await safe_fetch(get_klaar_data)
    if not result:
        await message.answer("Произошла ошибка при получении данных.")
        return

    caption, video_url = result
    if not video_url:
        await message.answer("Видео не найдено")
        return

    video_url = convert_drive_url(video_url)

    await message.answer_video(
        video_url,
        caption=caption,
        parse_mode="Markdown"
    )


@router.message(Command("kris"))
async def kris_handler(message: Message):
    result = await safe_fetch(get_kris_data)
    if not result:
        await message.answer("Произошла ошибка при получении данных.")
        return

    caption, image_url = result
    if not image_url:
        await message.answer("Картинка не найдена")
        return

    image_url = convert_drive_url(image_url)

    await message.answer_photo(
        image_url,
        caption=caption,
        parse_mode="Markdown"
    )


@router.message(Command("hi"))
async def hi_handler(message: Message):
    welcome_text = await safe_fetch(get_welcome)
    if not welcome_text:
        await message.answer("Произошла ошибка при получении приветственного текста.")
        return

    await message.answer(
        welcome_text,
        parse_mode="Markdown"
    )


@router.message(Command(commands=["getid"]))
async def send_chat_id(message: Message):
    chat_id = message.chat.id
    await message.answer(f"Ваш Chat ID: `{chat_id}`", parse_mode="Markdown")
    logging.info(f"Chat ID ({chat_id}) отправлен пользователю {message.from_user.id}")


@router.message(Command(commands=["kto"]))
async def who_is_this(message: Message):
    participants = await safe_fetch(fetch_participants)
    if not participants:
        await message.answer("Ошибка загрузки данных из Google Sheets.")
        return

    args = message.text.split(' ', 1)
    if len(args) < 2:
        await message.answer("Пожалуйста, укажите имя после команды или 'all' для всех.")
        return

    name = args[1].strip().lower()

    if name == "all":
        response = "Список всех пользователей:\n"
        for user_name, user_info in participants.items():
            # Показываем только уникальные записи по основному имени
            if user_name == user_info["name"].lower():
                tgnick_line = f"Имя в телеграмм: {user_info['tgnick']}\n" if user_info['tgnick'] != 'Unknown' else ''
                nick_line = f"Ник: @{user_info['nick']}\n" if user_info['nick'] != 'Unknown' else ''
                response += f"\nИмя: {user_info['name']}\n{tgnick_line}{nick_line}Инфо: {user_info['about']}\n"
        await message.answer(response)
    else:
        user_info = participants.get(name)
        if user_info:
            tgnick_line = f"Имя в телеграмм: {user_info['tgnick']}\n" if user_info['tgnick'] != 'Unknown' else ''
            nick_line = f"Ник: @{user_info['nick']}\n" if user_info['nick'] != 'Unknown' else ''
            response = f"Имя: {user_info['name']}\n{tgnick_line}{nick_line}Инфо: {user_info['about']}"
            await message.answer(response)
        else:
            await message.answer(f"Информация о пользователе '{args[1]}' не найдена.")

# ==========================
# Команда /list
# ==========================
@router.message(lambda message: message.text and message.text.startswith("/list"))
async def handle_list_command(message: types.Message):
    user_id = message.from_user.id

    # 1️⃣ Проверка allowed_users
    if user_id not in get_allowed_user_ids():
        await message.answer("❌ Недостаточно прав для выполнения команды.")
        return

    parts = message.text.split()
    input_names = parts[1:]
    redis_key = f"list_{user_id}"

    # =====================================
    # 🔹 Если просто /list — показать лист
    # =====================================
    if len(input_names) == 0:
        try:
            existing_list = redis.lrange(redis_key, 0, -1)

            if not existing_list:
                await message.answer(
                    "Чтобы сделать лист впиши:\n"
                    "/list имя1 имя2 имя3 ..."
                )
                return

            existing_list = [
                v.decode() if isinstance(v, bytes) else v
                for v in existing_list
            ]

            creator = existing_list[0]
            participants = existing_list[1:]

            await message.answer(
                f"📋 Твой текущий лист:\n\n"
                f"Создатель: {creator}\n"
                f"Участники ({len(participants)}): "
                f"{', '.join(participants) if participants else 'нет'}"
            )

        except Exception as e:
            logger.error(f"Ошибка чтения {redis_key}: {e}")
            await message.answer("❌ Ошибка при получении списка.")
        return

    # =====================================
    # 🔹 Создание / обновление листа
    # =====================================

    if len(input_names) > 6:
        await message.answer("❌ Можно указать не более 6 имён.")
        return

    creator_name = get_name(user_id, message.from_user.first_name)

    try:
        pipe = redis.pipeline()
        pipe.delete(redis_key)

        pipe.rpush(redis_key, creator_name)
        pipe.rpush(redis_key, *input_names)

        pipe.exec()

        await message.answer(
            f"✅ Лист обновлён.\n\n"
            f"Создатель: {creator_name}\n"
            f"Участники ({len(input_names)}): {', '.join(input_names)}"
        )

    except Exception as e:
        logger.error(f"Ошибка при создании {redis_key}: {e}")
        await message.answer("❌ Ошибка при сохранении списка.")

