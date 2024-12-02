# Используем официальный Python образ
FROM python:3.10-slim

# Устанавливаем рабочую директорию
WORKDIR /app

# Копируем файлы проекта в контейнер
COPY . /app

# Устанавливаем зависимости
RUN pip install --no-cache-dir -r requirements.txt

# Запускаем сервер и Celery worker
CMD ["sh", "-c", "celery -A celery_config.celery_app worker & uvicorn api.bot:app --host 0.0.0.0 --port 8000"]
