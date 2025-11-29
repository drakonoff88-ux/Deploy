FROM python:3.10-slim

# Установка системных зависимостей
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Установка Poetry
RUN pip install poetry

# Отключение создания виртуального окружения внутри Docker
RUN poetry config virtualenvs.create false

WORKDIR /app

# Копирование файлов зависимостей
COPY pyproject.toml poetry.lock* ./

# Установка зависимостей через Poetry
RUN poetry install --no-dev

# Копирование исходного кода
COPY mysite/ ./mysite/

WORKDIR /app/mysite

# Сбор статики (если нужно)
RUN python manage.py collectstatic --noinput

# Открытие порта
EXPOSE 8000

# Запуск приложения
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]