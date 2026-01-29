"""
Точка входа приложения - инициализация и запуск бота.
"""

import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from src.config import BOT_TOKEN, LOG_LEVEL, LOG_FORMAT
from src.handlers.common import router, shutdown_parser


# Настройка логирования
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL),
    format=LOG_FORMAT
)
logger = logging.getLogger(__name__)


async def main():
    """
    Главная функция - инициализация и запуск бота.
    """
    logger.info("Запуск бота...")

    # Инициализация бота с настройками по умолчанию
    bot = Bot(
        token=BOT_TOKEN,
        default=DefaultBotProperties(
            parse_mode=ParseMode.HTML
        )
    )

    # Инициализация диспетчера
    dp = Dispatcher()

    # Регистрация роутеров
    dp.include_router(router)

    # Регистрация shutdown хука
    dp.shutdown.register(shutdown_parser)

    try:
        # Удаление вебхуков (если были установлены)
        await bot.delete_webhook(drop_pending_updates=True)
        logger.info("Вебхуки удалены")

        # Запуск polling
        logger.info("Бот запущен и готов к работе")
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())

    except Exception as e:
        logger.exception(f"Критическая ошибка: {e}")

    finally:
        await bot.session.close()
        logger.info("Бот остановлен")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Бот остановлен пользователем")
    except Exception as e:
        logger.exception(f"Неожиданная ошибка: {e}")
