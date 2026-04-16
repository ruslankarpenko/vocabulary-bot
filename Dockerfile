FROM python:3.11-slim

WORKDIR /app

# Встановлюємо системні залежності
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Копіюємо requirements.txt
COPY requirements.txt .

# Встановлюємо Python залежності
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Копіюємо всі файли проекту
COPY . .

# Відкриваємо порт для health checks
EXPOSE 10000

# Запускаємо бота
CMD ["python", "main.py"]
