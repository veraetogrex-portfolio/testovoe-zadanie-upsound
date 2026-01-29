"""
Модуль конфигурации бота.
Загружает переменные окружения и определяет константы.
"""

import os
from dotenv import load_dotenv

# Загрузка переменных окружения из .env файла
load_dotenv()

# Конфигурация бота
BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN не найден в переменных окружения")

# Конфигурация HTTP-клиента
REQUEST_TIMEOUT = 10  # секунды
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

# Настройки логирования
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

# Константы для форматирования
MAX_MESSAGE_LENGTH = 4096  # Максимальная длина сообщения в Telegram

# Retry-политика
MAX_RETRIES = 2  # Максимальное количество повторных попыток
RETRY_DELAY = 1.0  # Задержка между попытками (секунды)
RETRY_STATUS_CODES = (502, 503, 504)  # HTTP-коды для retry
