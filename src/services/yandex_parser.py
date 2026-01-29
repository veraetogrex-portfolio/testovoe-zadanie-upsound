"""
Сервис для парсинга треков Яндекс.Музыки.

v1.1: Интегрирует fallback-парсинг, защиту от блокировок, кэширование.
"""

import logging
from typing import Optional
import httpx

from src.config import REQUEST_TIMEOUT, MAX_RETRIES
from src.models.track import TrackInfo
from src.services.request_manager import RequestManager
from src.services.cache import TrackCache
from src.parsers.cascade import CascadeParser
from src.exceptions import (
    get_http_error,
    ConnectTimeoutError,
    ReadTimeoutError,
    ConnectionError as BotConnectionError,
    SSLError as BotSSLError,
    RemoteProtocolError,
    ParsingError,
)


logger = logging.getLogger(__name__)


class YandexMusicParser:
    """
    Парсер для извлечения информации о треках с Яндекс.Музыки.

    v1.1 возможности:
    - 4-этапная валидация (тип → URL → HTTP → парсинг)
    - Fallback-парсинг: JSON-LD → Open Graph → HTML/CSS
    - Защита от блокировок: User-Agent rotation, browser headers, exponential backoff
    - In-memory кэш с TTL для снижения нагрузки
    - HTTP/2 поддержка для более быстрых запросов
    """

    def __init__(
        self,
        cache_maxsize: int = 1000,
        cache_ttl: int = 3600,
        max_retries: int = MAX_RETRIES,
    ):
        """
        Инициализация парсера.

        Args:
            cache_maxsize: Максимальное количество треков в кэше
            cache_ttl: Время жизни записи в кэше (секунды)
            max_retries: Максимум попыток при HTTP-запросах
        """
        # HTTP-запросы с защитой от блокировок
        self.request_manager = RequestManager(
            timeout=REQUEST_TIMEOUT,
            max_retries=max_retries,
        )

        # Каскадный парсер с fallback-стратегией
        self.cascade_parser = CascadeParser()

        # In-memory кэш с TTL
        self.cache = TrackCache(maxsize=cache_maxsize, ttl=cache_ttl)

        logger.info(
            f"Инициализирован YandexMusicParser v1.1: "
            f"cache={cache_maxsize}/{cache_ttl}s, retries={max_retries}"
        )

    async def get_track_info(self, url: str, track_id: Optional[str] = None) -> Optional[TrackInfo]:
        """
        Получение информации о треке по URL.

        Этапы:
        1. Проверка кэша
        2. HTTP-запрос с retry и защитой от блокировок (RequestManager)
        3. Каскадный парсинг: JSON-LD → Open Graph → HTML/CSS
        4. Сохранение в кэш

        Args:
            url: URL трека на Яндекс.Музыке
            track_id: Опциональный ID трека для кэширования (формат: "album_id:track_id")

        Returns:
            TrackInfo объект или None при критической ошибке

        Raises:
            HttpError: При ошибках HTTP-запроса
            NetworkError: При сетевых ошибках
            ParsingError: При ошибках парсинга
        """
        try:
            # Этап 1: Проверка кэша
            if track_id:
                cached_track = self.cache.get(track_id)
                if cached_track:
                    logger.info(f"✅ Трек найден в кэше: {track_id}")
                    return cached_track

            logger.info(f"Получение трека: {url}")

            # Этап 2: HTTP-запрос с защитой от блокировок
            html = await self._fetch_with_retry(url)

            # Этап 3: Каскадный парсинг (JSON-LD → Open Graph → HTML/CSS)
            track_info = self.cascade_parser.parse(html, url)

            if not track_info:
                logger.error(f"Все парсеры провалились для {url}")
                raise ParsingError("Не удалось извлечь информацию о треке")

            # Этап 4: Сохранение в кэш
            if track_id:
                self.cache.set(track_id, track_info)

            return track_info

        except Exception as e:
            # Логируем и пробрасываем дальше
            logger.error(f"Ошибка при получении трека {url}: {e.__class__.__name__}: {e}")
            raise

    async def _fetch_with_retry(self, url: str) -> str:
        """
        Выполнение HTTP-запроса с retry-политикой через RequestManager.

        Args:
            url: URL для запроса

        Returns:
            HTML содержимое страницы

        Raises:
            HttpError: При ошибках HTTP
            NetworkError: При сетевых ошибках
        """
        try:
            # RequestManager уже реализует retry, exponential backoff, User-Agent rotation
            response = await self.request_manager.fetch(url)
            return response.text

        except httpx.ConnectTimeout as e:
            logger.error(f"Connect timeout для {url}: {e}")
            raise ConnectTimeoutError(str(e))

        except httpx.ReadTimeout as e:
            logger.error(f"Read timeout для {url}: {e}")
            raise ReadTimeoutError(str(e))

        except httpx.ConnectError as e:
            logger.error(f"Connection error для {url}: {e}")
            raise BotConnectionError(str(e))

        except httpx.RemoteProtocolError as e:
            logger.error(f"Remote protocol error для {url}: {e}")
            raise RemoteProtocolError(str(e))

        except httpx.HTTPStatusError as e:
            # Маппинг HTTP-ошибок на наши исключения
            status_code = e.response.status_code
            error_class = get_http_error(status_code)
            logger.error(f"HTTP {status_code} для {url}")
            raise error_class(status_code)

        except Exception as e:
            if "ssl" in str(e).lower():
                logger.error(f"SSL error для {url}: {e}")
                raise BotSSLError(str(e))
            raise

    def get_cache_stats(self) -> dict:
        """
        Возвращает статистику кэша.

        Returns:
            Dict с метриками кэша (size, hits, misses, hit_rate)
        """
        return self.cache.stats()

    def get_parser_stats(self) -> dict:
        """
        Возвращает статистику парсеров.

        Returns:
            Dict с информацией о парсерах
        """
        return self.cascade_parser.get_parser_stats()

    def clear_cache(self):
        """Очищает кэш треков."""
        self.cache.clear()
        logger.info("Кэш очищен")

    async def close(self):
        """Закрытие HTTP-клиента и вывод статистики."""
        # Логируем финальную статистику кэша
        stats = self.cache.stats()
        logger.info(
            f"Финальная статистика кэша: "
            f"size={stats['size']}/{stats['maxsize']}, "
            f"hits={stats['hits']}, misses={stats['misses']}, "
            f"hit_rate={stats['hit_rate']}"
        )

        # Закрываем HTTP-клиент
        await self.request_manager.close()
        logger.info("YandexMusicParser закрыт")
