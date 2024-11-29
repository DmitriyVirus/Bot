from aiogram import Router
from aiogram.types import Message
from tgbot.triggers import TRIGGERS

router = Router()

# Обработчик команды /help
@router.message(commands=["help"])
async def help_handler(message: Message):
    help_text = (
        "Я приветствую новиков и реагирую на некоторые фразы:\n\n"
        "Я могу ответить на следующие фразы:\n"
        f"{''.join(f'*{trigger}* - {response if isinstance(response, str) else response.get('text', '')}\n' for trigger, response in TRIGGERS.items())}"
    )
    await message.answer(help_text, parse_mode="Markdown")

@router.message()
async def trigger_handler(message: Message):
    message_text = message.text.lower()  # Преобразуем текст в нижний регистр
    for trigger, response in TRIGGERS.items():
        if trigger in message_text:
            if isinstance(response, dict):  # Если ответ это словарь (с текстом, изображением или gif)
                # Отправляем текст
                if "text" in response:
                    await message.answer(response["text"])
                
                # Отправляем изображение, если есть
                if "image" in response:
                    await message.answer_photo(response["image"])
                
                # Отправляем gif, если есть
                if "gif" in response:
                    await message.answer_animation(response["gif"])
            
            else:
                await message.answer(response)  # Отправляем текст
            break  # Прекращаем проверку после первого совпадения
