from aiogram import Router
from aiogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.filters import Command  # Импорт фильтра Command
from tgbot.triggers import TRIGGERS

router = Router()

# Обработчик команды /help
@router.message(Command(commands=["help"]))  # Используем фильтр Command
async def help_handler(message: Message):
    help_text = "Я приветствую новичков и реагирую на следующие фразы:\n\n" \
                "Я могу ответить на следующие фразы:\n"
    
    # Создаем InlineKeyboardMarkup
    keyboard = InlineKeyboardMarkup()

    # Перебираем триггеры и добавляем их как кнопки
    for i, trigger in enumerate(TRIGGERS, 1):
        # Извлекаем часть до символа ":" и делаем первую букву заглавной
        trigger_text = trigger.split(":")[0].capitalize()
        
        # Добавляем кнопку для каждого триггера с номером
        button = InlineKeyboardButton(
            text=f"{i}. **{trigger_text}**", 
            callback_data=f"trigger_{trigger}"
        )
        keyboard.add(button)
    
    # Формируем текст с нумерацией и жирным шрифтом
    help_text += "\n".join([f"{i}. **{trigger.split(':')[0].capitalize()}**" for i, trigger in enumerate(TRIGGERS, 1)])

    # Отправляем сообщение с кнопками
    await message.answer(help_text, reply_markup=keyboard, parse_mode="Markdown")

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
