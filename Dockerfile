FROM python:3.11-slim

WORKDIR /app

# Установка системных зависимостей для PostgreSQL
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Копирование зависимостей
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копирование кода приложения
COPY *.py ./

# Команда запуска
CMD ["python", "bot.py"]