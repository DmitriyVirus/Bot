from celery_config import celery_app
from datetime import datetime
import time
import logging

# Задача для имитации задержки
@celery_app.task
def send_delayed_reminder():
    try:
        # Имитация задержки (например, 5 секунд)
        logging.info("Задача началась...")
        time.sleep(5)
        logging.info("Задача завершена! Отправка напоминания...")
        # Ваш код для отправки напоминания сюда
        # Например, вызов send_reminder()
        # send_reminder()
    except Exception as e:
        logging.error(f"Ошибка при выполнении задачи: {e}")
