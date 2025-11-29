FROM python:3.10-slim

# Установка системных зависимостей
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Копирование файлов зависимостей
COPY requirements.txt .

# Установка зависимостей через pip
RUN pip install -r requirements.txt

# Копирование исходного кода
COPY mysite/ ./mysite/

WORKDIR /app/mysite

# Открытие порта
EXPOSE 8000

# Запуск приложения с collectstatic при старте
CMD ["sh", "-c", "python manage.py collectstatic --noinput && python manage.py runserver 0.0.0.0:8000"]