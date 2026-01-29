"""
HTML/CSS парсер (приоритет 3).
"""

import logging
from typing import Optional
from bs4 import BeautifulSoup

from src.parsers.base import BaseParser
from src.models.track import TrackInfo


logger = logging.getLogger(__name__)


class HtmlCssParser(BaseParser):
    """Парсер HTML-элементов по CSS-селекторам"""

    # Селекторы для различных элементов страницы
    # ВАЖНО: эти селекторы могут меняться при редизайне Яндекс.Музыки
    SELECTORS = {
        'track_name': [
            'h1.track__title',
            '.d-track__title',
            '[data-testid="track-title"]',
            '.track-heading__title',
            'h1.page-track__title',
        ],
        'artist': [
            '.d-track__artists a',
            '.track__artists a',
            '[data-testid="track-artist"]',
            '.page-track__artists a',
            'a.deco-link.track__artists-item',
        ],
        'duration': [
            '.d-track__duration',
            '.track__duration',
            '[data-testid="track-duration"]',
            '.page-track__duration',
        ],
        'album': [
            '.d-track__album a',
            '.track__album a',
            '[data-testid="track-album"]',
        ],
    }

    @property
    def name(self) -> str:
        return "HTML/CSS"

    @property
    def priority(self) -> int:
        return 3

    def parse(self, soup: BeautifulSoup, url: str) -> Optional[TrackInfo]:
        """
        Парсит HTML-элементы по CSS-селекторам.

        Пробует селекторы по порядку до первого успешного.
        """
        try:
            # Извлечение названия трека
            track_name = self._extract_by_selectors(soup, self.SELECTORS['track_name'])
            if not track_name:
                logger.debug(f"Название трека не найдено для {url}")
                return None

            # Извлечение артистов
            artist_elements = self._extract_all_by_selectors(soup, self.SELECTORS['artist'])
            if artist_elements:
                artist_name = ', '.join([a.get_text(strip=True) for a in artist_elements])
            else:
                artist_name = "Неизвестный артист"

            # Извлечение длительности
            duration = self._extract_by_selectors(soup, self.SELECTORS['duration']) or "—"

            # Извлечение альбома (опционально)
            album_name = self._extract_by_selectors(soup, self.SELECTORS['album'])

            logger.info(f"✅ {self.name} успешно распарсил трек: {track_name}")

            return TrackInfo(
                name=track_name,
                artist=artist_name,
                duration=duration,
                album=album_name,
                url=url
            )

        except Exception as e:
            logger.error(f"Ошибка в {self.name} парсере: {e}")
            return None

    def _extract_by_selectors(self, soup: BeautifulSoup, selectors: list[str]) -> Optional[str]:
        """
        Пробует селекторы по порядку и возвращает первый найденный текст.

        Args:
            soup: Распарсенный HTML
            selectors: Список CSS-селекторов

        Returns:
            Текст элемента или None
        """
        for selector in selectors:
            try:
                element = soup.select_one(selector)
                if element:
                    text = element.get_text(strip=True)
                    if text:
                        return text
            except Exception as e:
                logger.debug(f"Ошибка селектора '{selector}': {e}")
                continue

        return None

    def _extract_all_by_selectors(self, soup: BeautifulSoup, selectors: list[str]) -> list:
        """
        Пробует селекторы и возвращает все найденные элементы.

        Args:
            soup: Распарсенный HTML
            selectors: Список CSS-селекторов

        Returns:
            Список элементов
        """
        for selector in selectors:
            try:
                elements = soup.select(selector)
                if elements:
                    return elements
            except Exception as e:
                logger.debug(f"Ошибка селектора '{selector}': {e}")
                continue

        return []
