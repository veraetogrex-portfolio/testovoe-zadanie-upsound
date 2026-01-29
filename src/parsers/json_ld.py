"""
JSON-LD парсер (приоритет 1).
"""

import json
import logging
from typing import Optional
from bs4 import BeautifulSoup

from src.parsers.base import BaseParser
from src.models.track import TrackInfo
from src.utils.formatters import parse_iso_duration
from src.utils.artists import extract_artists


logger = logging.getLogger(__name__)


class JsonLdParser(BaseParser):
    """Парсер структурированных данных Schema.org"""

    @property
    def name(self) -> str:
        return "JSON-LD"

    @property
    def priority(self) -> int:
        return 1

    def can_parse(self, soup: BeautifulSoup) -> bool:
        """Проверяет наличие JSON-LD на странице"""
        return soup.find('script', {'type': 'application/ld+json'}) is not None

    def parse(self, soup: BeautifulSoup, url: str) -> Optional[TrackInfo]:
        """
        Парсит JSON-LD метаданные.

        Ищет <script type="application/ld+json"> с @type="MusicRecording"
        """
        try:
            # Поиск JSON-LD тега
            json_ld_script = soup.find('script', {'type': 'application/ld+json'})

            if not json_ld_script or not json_ld_script.string:
                logger.debug(f"JSON-LD не найден для {url}")
                return None

            # Парсинг JSON
            try:
                data = json.loads(json_ld_script.string)
            except json.JSONDecodeError as e:
                logger.warning(f"Невалидный JSON-LD: {e}")
                return None

            # Проверка типа схемы
            if data.get('@type') != 'MusicRecording':
                logger.debug(f"Неподходящий тип схемы: {data.get('@type')}")
                return None

            # Извлечение данных
            track_name = data.get('name')
            if not track_name:
                logger.warning("Отсутствует поле 'name' в JSON-LD")
                return None

            # Извлечение артистов (может быть объект или массив)
            artist_name = extract_artists(data.get('byArtist'))

            # Извлечение длительности
            iso_duration = data.get('duration', '')
            duration = parse_iso_duration(iso_duration) or "—"

            # Извлечение альбома (опционально)
            album_data = data.get('inAlbum', {})
            album_name = album_data.get('name') if isinstance(album_data, dict) else None

            logger.info(f"✅ {self.name} успешно распарсил трек: {track_name}")

            return TrackInfo(
                name=track_name.strip(),
                artist=artist_name,
                duration=duration,
                album=album_name,
                url=url
            )

        except Exception as e:
            logger.error(f"Ошибка в {self.name} парсере: {e}")
            return None
