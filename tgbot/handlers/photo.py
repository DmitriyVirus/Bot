from aiogram import Router, F, types
from tgbot.services.ocr_service_free_compress import extract_text_from_telegram_photo

router = Router()

async def handle_photo_message(message: types.Message, bot):
    photo = message.photo[-1]
    text = await extract_text_from_telegram_photo(bot, photo.file_id)
    await message.answer(f"📄 Распознанный текст:\n{text}")


async def handle_photo_channel_post(message: types.Message, bot):
    photo = message.photo[-1]
    text = await extract_text_from_telegram_photo(bot, photo.file_id)
    await bot.send_message(chat_id=message.chat.id, text=f"📄 Распознанный текст:\n{text}")


# Роутер: личка и группы
router.message(F.photo)(handle_photo_message)

# Роутер: канал (если бот админ)
router.channel_post(F.photo)(handle_photo_channel_post)
