"""
Open Graph парсер (приоритет 2).
"""

import logging
from typing import Optional
from bs4 import BeautifulSoup

from src.parsers.base import BaseParser
from src.models.track import TrackInfo


logger = logging.getLogger(__name__)


class OpenGraphParser(BaseParser):
    """Парсер Open Graph meta-тегов"""

    @property
    def name(self) -> str:
        return "Open Graph"

    @property
    def priority(self) -> int:
        return 2

    def can_parse(self, soup: BeautifulSoup) -> bool:
        """Проверяет наличие OG-тегов"""
        return soup.find('meta', property='og:title') is not None

    def parse(self, soup: BeautifulSoup, url: str) -> Optional[TrackInfo]:
        """
        Парсит Open Graph meta-теги.

        Ищет:
        - og:title → "Track Name - Artist" или "Track Name"
        - og:audio:artist → artist (если есть)
        - music:duration → duration в секундах
        """
        try:
            # og:title - обычно содержит "Трек - Артист"
            title_tag = soup.find('meta', property='og:title')
            if not title_tag or not title_tag.get('content'):
                logger.debug(f"og:title не найден для {url}")
                return None

            title = title_tag['content'].strip()

            # Парсинг title (может быть "Трек - Артист" или "Трек — Артист")
            track_name, artist_name = self._parse_title(title)

            # Попытка найти артиста отдельно
            artist_tag = soup.find('meta', property='og:audio:artist')
            if artist_tag and artist_tag.get('content'):
                artist_name = artist_tag['content'].strip()

            # Длительность (music:duration в секундах)
            duration = self._parse_duration(soup)

            # Альбом
            album_name = None
            album_tag = soup.find('meta', property='music:album')
            if album_tag and album_tag.get('content'):
                album_name = album_tag['content'].strip()

            if not track_name:
                logger.debug("Не удалось извлечь название трека из OG")
                return None

            logger.info(f"✅ {self.name} успешно распарсил трек: {track_name}")

            return TrackInfo(
                name=track_name,
                artist=artist_name or "Неизвестный артист",
                duration=duration,
                album=album_name,
                url=url
            )

        except Exception as e:
            logger.error(f"Ошибка в {self.name} парсере: {e}")
            return None

    def _parse_title(self, title: str) -> tuple[str, str]:
        """
        Парсит title в формате "Трек - Артист" или "Трек — Артист"

        Returns:
            (track_name, artist_name)
        """
        # Попробуем разделители
        for sep in [' — ', ' - ', ' – ']:
            if sep in title:
                parts = title.split(sep, 1)
                if len(parts) == 2:
                    return parts[0].strip(), parts[1].strip()

        # Если не удалось распарсить - считаем всё названием трека
        return title, "Неизвестный артист"

    def _parse_duration(self, soup: BeautifulSoup) -> str:
        """
        Парсит длительность из music:duration (в секундах)

        Returns:
            Длительность в формате MM:SS или "—"
        """
        duration_tag = soup.find('meta', property='music:duration')
        if not duration_tag or not duration_tag.get('content'):
            return "—"

        try:
            seconds = int(duration_tag['content'])
            minutes = seconds // 60
            secs = seconds % 60
            return f"{minutes}:{secs:02d}"
        except (ValueError, TypeError):
            return "—"
