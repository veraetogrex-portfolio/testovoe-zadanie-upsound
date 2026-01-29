"""
Обработчики команд и сообщений бота.
"""

import logging
from aiogram import Router, F
from aiogram.filters import Command, CommandStart
from aiogram.types import Message
from aiogram.enums import ParseMode

from src.services.yandex_parser import YandexMusicParser
from src.utils.validators import validate_yandex_music_url, is_yandex_music_url
from src.utils.formatters import format_track_message
from src.exceptions import (
    YandexMusicBotError,
    ValidationError,
    HttpError,
    NetworkError,
    ParsingError,
)


logger = logging.getLogger(__name__)
router = Router()

# Глобальный экземпляр парсера
parser = YandexMusicParser()


@router.message(CommandStart())
async def cmd_start(message: Message):
    """
    Обработчик команды /start.

    Отправляет приветственное сообщение с инструкцией.
    """
    welcome_text = (
        "👋 <b>Привет!</b>\n\n"
        "Я бот для получения информации о треках Яндекс.Музыки.\n\n"
        "📝 <b>Как пользоваться:</b>\n"
        "Просто отправь мне ссылку на трек в формате:\n"
        "<code>https://music.yandex.ru/album/{album_id}/track/{track_id}</code>\n\n"
        "Я верну тебе название трека, артиста и длительность.\n\n"
        "Для получения дополнительной помощи используй /help"
    )

    await message.answer(welcome_text, parse_mode=ParseMode.HTML)
    logger.info(f"Пользователь {message.from_user.id} запустил бота")


@router.message(Command("help"))
async def cmd_help(message: Message):
    """
    Обработчик команды /help.

    Отправляет подробную справку.
    """
    help_text = (
        "ℹ️ <b>Справка по использованию бота</b>\n\n"
        "<b>Доступные команды:</b>\n"
        "/start - Начать работу с ботом\n"
        "/help - Показать эту справку\n\n"
        "<b>Как получить информацию о треке:</b>\n"
        "1. Зайди на сайт music.yandex.ru\n"
        "2. Найди нужный трек\n"
        "3. Скопируй ссылку на трек\n"
        "4. Отправь ссылку мне в чат\n\n"
        "<b>Пример ссылки:</b>\n"
        "<code>https://music.yandex.ru/album/12345/track/67890</code>\n\n"
        "<b>Что я верну:</b>\n"
        "🎵 Название трека\n"
        "👤 Артист\n"
        "⏱️ Длительность\n"
        "💿 Альбом (если доступно)\n\n"
        "❓ <b>Возникли проблемы?</b>\n"
        "Убедись, что ссылка корректна и трек доступен на Яндекс.Музыке."
    )

    await message.answer(help_text, parse_mode=ParseMode.HTML)
    logger.info(f"Пользователь {message.from_user.id} запросил справку")


@router.message(F.text)
async def handle_message(message: Message):
    """
    Обработчик всех текстовых сообщений.

    Реализует 4-этапную валидацию:
    - Этап 1: Валидация текста сообщения
    - Этап 2: Валидация формата URL
    - Этап 3: HTTP-запрос (в парсере)
    - Этап 4: Парсинг данных (в парсере)
    """
    url = message.text.strip() if message.text else ""
    user_id = message.from_user.id

    # Быстрая проверка: это вообще ссылка на Яндекс.Музыку?
    if not is_yandex_music_url(url):
        hint_text = (
            "🤔 <b>Не понимаю, что ты хочешь</b>\n\n"
            "Отправь мне ссылку на трек с Яндекс.Музыки или используй:\n"
            "/help - Справка по использованию\n"
            "/start - Начать заново"
        )
        await message.answer(hint_text, parse_mode=ParseMode.HTML)
        logger.debug(f"Неизвестное сообщение от пользователя {user_id}: {url[:50]}")
        return

    logger.info(f"Пользователь {user_id} отправил URL: {url}")

    try:
        # Этап 2: Валидация URL и извлечение ID
        album_id, track_id = validate_yandex_music_url(url)
        logger.debug(f"Извлечены ID: album={album_id}, track={track_id}")

        # Формируем cache_key для кэширования
        cache_key = f"{album_id}:{track_id}"

        # Отправка индикатора "печатает..."
        await message.bot.send_chat_action(message.chat.id, "typing")

        # Этапы 3-4: Парсинг трека (с кэшированием, retry и fallback-парсингом)
        track_info = await parser.get_track_info(url, track_id=cache_key)

        if track_info:
            response_text = format_track_message(track_info)
            await message.answer(response_text, parse_mode=ParseMode.HTML)
            logger.info(f"Успешно отправлена информация о треке пользователю {user_id}")
        else:
            # Не должно произойти (парсер бросает исключения)
            await send_error_message(message, "⚠️ Не удалось получить информацию о треке")

    except ValidationError as e:
        # Этап 2: Ошибки валидации URL
        await send_error_message(message, e.user_message)
        logger.debug(f"Ошибка валидации от пользователя {user_id}: {e.__class__.__name__}: {e}")

    except HttpError as e:
        # Этап 3: Ошибки HTTP-запроса
        await send_error_message(message, e.user_message)
        logger.info(f"HTTP ошибка для пользователя {user_id}: {e.__class__.__name__} (status={e.status_code})")

    except NetworkError as e:
        # Этап 3: Сетевые ошибки
        await send_error_message(message, e.user_message)
        logger.warning(f"Сетевая ошибка для пользователя {user_id}: {e.__class__.__name__}: {e}")

    except ParsingError as e:
        # Этап 4: Ошибки парсинга
        await send_error_message(message, e.user_message)
        logger.error(f"Ошибка парсинга для пользователя {user_id}: {e.__class__.__name__}: {e}")

    except YandexMusicBotError as e:
        # Базовый класс (на всякий случай)
        await send_error_message(message, e.user_message)
        logger.error(f"Ошибка бота для пользователя {user_id}: {e.__class__.__name__}: {e}")

    except Exception as e:
        # Непредвиденные ошибки
        await send_error_message(
            message,
            "⚠️ <b>Произошла неожиданная ошибка</b>\n\n"
            "Попробуйте позже или обратитесь к администратору."
        )
        logger.exception(f"Критическая ошибка для пользователя {user_id}: {e}")


async def send_error_message(message: Message, error_text: str):
    """
    Отправка сообщения об ошибке пользователю.

    Args:
        message: Сообщение пользователя
        error_text: Текст ошибки
    """
    try:
        await message.answer(error_text, parse_mode=ParseMode.HTML)
    except Exception as e:
        logger.error(f"Не удалось отправить сообщение об ошибке: {e}")
        # Попытка отправить без HTML
        try:
            await message.answer(error_text.replace("<b>", "").replace("</b>", "").replace("<code>", "").replace("</code>", ""))
        except Exception:
            logger.error("Не удалось отправить сообщение даже без HTML")


async def shutdown_parser():
    """Graceful shutdown парсера."""
    await parser.close()
    logger.info("Парсер остановлен")
