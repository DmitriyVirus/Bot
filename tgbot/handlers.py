from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command  # Импорт фильтра Command
from tgbot.triggers import TRIGGERS

router = Router()

# Обработчик команды /help
@router.message(Command(commands=["help"]))  # Используем фильтр Command
async def help_handler(message: Message):
    help_text = "Я приветствую новиков и реагирую на некоторые фразы:\n\n" \
                "Я могу ответить на следующие фразы:\n"
    
    # Перебираем триггеры
    for trigger in TRIGGERS:
        # Извлекаем часть до символа ":" или оставляем сам текст, если ":" нет
        trigger_text = trigger.split(":")[0]
        help_text += f"{i}. {trigger_text}\n"
    
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
