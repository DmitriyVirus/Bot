from decouple import config

# Основные переменные
TOKEN = config("TOKEN")
WEBHOOK_URL = config("WEBHOOK_URL")
CHAT_ID = config("CHAT_ID")
REDIS_URL = config("REDIS_URL")
