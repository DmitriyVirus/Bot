from decouple import config
from celery import Celery

# Получаем URL для Redis из переменной окружения
redis_url = config('REDIS_URL')  # Переменная окружения должна быть настроена на вашем сервере

# Инициализация Celery с использованием Redis как брокера и бэкэнда
celery_app = Celery(
    "tgbot",
    broker=redis_url,
    backend=redis_url,
)
