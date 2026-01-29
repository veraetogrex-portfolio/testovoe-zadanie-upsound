"""
Кэш для информации о треках.
"""

import logging
from typing import Optional
from cachetools import TTLCache

from src.models.track import TrackInfo


logger = logging.getLogger(__name__)


class TrackCache:
    """
    In-memory кэш для треков с TTL (Time To Live).

    Использует cachetools.TTLCache для автоматического удаления устаревших записей.
    """

    def __init__(self, maxsize: int = 1000, ttl: int = 3600):
        """
        Инициализация кэша.

        Args:
            maxsize: Максимальное количество записей в кэше
            ttl: Время жизни записи в секундах (по умолчанию 1 час)
        """
        self._cache = TTLCache(maxsize=maxsize, ttl=ttl)
        self._hits = 0
        self._misses = 0

        logger.info(f"Инициализирован кэш: maxsize={maxsize}, ttl={ttl}с")

    def get(self, track_id: str) -> Optional[TrackInfo]:
        """
        Получает трек из кэша.

        Args:
            track_id: ID трека (формат: "album_id:track_id")

        Returns:
            TrackInfo или None если не найдено
        """
        result = self._cache.get(track_id)

        if result:
            self._hits += 1
            logger.debug(f"✅ Cache HIT: {track_id}")
        else:
            self._misses += 1
            logger.debug(f"❌ Cache MISS: {track_id}")

        return result

    def set(self, track_id: str, info: TrackInfo):
        """
        Сохраняет трек в кэш.

        Args:
            track_id: ID трека (формат: "album_id:track_id")
            info: Информация о треке
        """
        self._cache[track_id] = info
        logger.debug(f"💾 Сохранено в кэш: {track_id}")

    def clear(self):
        """Очищает весь кэш."""
        self._cache.clear()
        logger.info("Кэш очищен")

    def stats(self) -> dict:
        """
        Возвращает статистику кэша.

        Returns:
            Dict с метриками:
            - size: Текущее количество записей
            - maxsize: Максимальная вместимость
            - ttl: Время жизни записей
            - hits: Количество попаданий
            - misses: Количество промахов
            - hit_rate: Процент попаданий
        """
        total_requests = self._hits + self._misses
        hit_rate = (self._hits / total_requests * 100) if total_requests > 0 else 0.0

        return {
            'size': len(self._cache),
            'maxsize': self._cache.maxsize,
            'ttl': self._cache.ttl,
            'hits': self._hits,
            'misses': self._misses,
            'hit_rate': f"{hit_rate:.1f}%",
        }

    def reset_stats(self):
        """Сбрасывает статистику hits/misses."""
        self._hits = 0
        self._misses = 0
        logger.info("Статистика кэша сброшена")
