from aiogram import Router
from aiogram.types import Message
import telebot
import os

TOKEN = os.getenv("TOKEN")
bot = telebot.TeleBot(TOKEN)

# Словарь с триггерами
TRIGGERS = {
    "кому ты служишь": "Мой хояин слишком известен, чтобы его называть! Можете звать его просто - Солнцеликий!",
    "кто у нас тут главный": "Наша великая насяльника и глава клана Elisan, в простонародье - Анна.",
    "основные наши правила": (
        "1. Не носить серьгу Линдвиора, если носишь её, то получаешь анальное зондирование.\n"
        "2. Не заливать вар никому.\n"
        "3. Не ругаться с КЛ.\n"
        "4. Уважать мнение солнцеликого ЕГО."
    ),
    "код красный тут матюки": {
        "text": "У нас так не принято, подонок!\n", 
        "image": "https://memepedia.ru/wp-content/uploads/2021/02/bonk-mem-bonk-8.jpg"  
    },
    "на кол посадить": {
        "text": "Вот так примерно?\n",
        "gif": "https://lastfm.freetls.fastly.net/i/u/ar0/4192f84a3d4a4828c8c836229da960df.gif"
    },
}

# Обработчик команды /help
async def send_help(message):
    help_text = (
        "Я приветствую новиков и реагирую на некоторые фразы:\n"
        "Я могу ответить на следующие фразы:\n"
        "*'кому ты служишь' - расскажет, кто хозяин бота.*\n"
        "*'кто у нас тут главный' - расскажет, кто у нас главный.*\n"
        "*'основные наши правила' - покажет основные правила.*\n"
        "*'код красный тут матюки' - покажет картинку с собачкой.*\n"
        "*'на кол посадить' - покажет gif с наказанием.*\n"
    )
    bot.send_message(message.chat.id, help_text, parse_mode='Markdown')

# Функция для приветствия новых пользователей
async def welcome_new_user(message):
    for new_user in message.new_chat_members:
        bot.send_message(
            message.chat.id, 
            "Привет, {}! Нам нужно свежее мясцо!".format(new_user.first_name)
        )

# Ответы на триггеры
async def text_trigger_handler(message):
    message_text = message.text.lower()  # Преобразуем в нижний регистр
    for trigger, response in TRIGGERS.items():
        if trigger in message_text:
            if isinstance(response, dict):  # Если ответ это словарь (содержит текст, картинку или gif)
                # Отправляем текст
                bot.send_message(message.chat.id, response["text"])
                
                # Отправляем картинку, если есть
                if "image" in response:
                    bot.send_photo(message.chat.id, response["image"])
                   
                # Отправляем gif, если есть
                if "gif" in response:
                    bot.send_animation(message.chat.id, response["gif"])
                   
            elif isinstance(response, str):  # Если это просто строка
                bot.send_message(message.chat.id, response)  # Отправляем текст
            break  # Останавливаем поиск, если триггер найден
