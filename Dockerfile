FROM python:3.11-slim

# Установка системных зависимостей
RUN apt-get update && apt-get install -y \
    curl \
    systemctl \
    procps \
    && rm -rf /var/lib/apt/lists/*

# Установка Xray
RUN curl -L https://github.com/XTLS/Xray-core/releases/latest/download/Xray-linux-64.zip -o /tmp/xray.zip \
    && unzip /tmp/xray.zip -d /usr/local/bin/ \
    && chmod +x /usr/local/bin/xray \
    && rm /tmp/xray.zip

# Создание рабочей директории
WORKDIR /app

# Копирование requirements и установка зависимостей
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копирование кода бота
COPY main.py .
COPY .env.example .env

# Создание директории для конфигурации Xray
RUN mkdir -p /usr/local/etc/xray

# Создание volume для персистентных данных
VOLUME ["/usr/local/etc/xray", "/app/data"]

# Переменные окружения по умолчанию
ENV XRAY_CONFIG=/usr/local/etc/xray/config.json
ENV PYTHONUNBUFFERED=1

# Healthcheck
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import os; exit(0 if os.path.exists('/tmp/bot_healthy') else 1)"

# Запуск бота
CMD ["python", "main.py"]
