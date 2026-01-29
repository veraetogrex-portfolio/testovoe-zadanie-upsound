"""
Каскадный парсер - объединяет несколько парсеров с приоритетами.
"""

import logging
from typing import Optional
from bs4 import BeautifulSoup

from src.models.track import TrackInfo
from src.parsers.base import BaseParser
from src.parsers.json_ld import JsonLdParser
from src.parsers.open_graph import OpenGraphParser
from src.parsers.html_css import HtmlCssParser


logger = logging.getLogger(__name__)


class CascadeParser:
    """
    Каскадный парсер с fallback-стратегией.

    Пробует парсеры по порядку приоритета:
    1. JSON-LD (приоритет 1)
    2. Open Graph (приоритет 2)
    3. HTML/CSS (приоритет 3)

    Возвращает результат первого успешного парсера.
    """

    def __init__(self, parsers: Optional[list[BaseParser]] = None):
        """
        Инициализация каскадного парсера.

        Args:
            parsers: Список парсеров. Если None - используются дефолтные
        """
        if parsers is None:
            parsers = [
                JsonLdParser(),
                OpenGraphParser(),
                HtmlCssParser(),
            ]

        # Сортируем по приоритету (меньше = выше)
        self.parsers = sorted(parsers, key=lambda p: p.priority)

        logger.info(
            f"Инициализирован каскадный парсер с {len(self.parsers)} парсерами: "
            f"{', '.join([p.name for p in self.parsers])}"
        )

    def parse(self, html: str, url: str) -> Optional[TrackInfo]:
        """
        Парсит HTML используя каскад парсеров.

        Args:
            html: HTML содержимое страницы
            url: URL страницы

        Returns:
            TrackInfo от первого успешного парсера или None

        Raises:
            Exception: Если все парсеры вернули None
        """
        soup = BeautifulSoup(html, 'lxml')  # lxml быстрее чем html.parser

        for parser in self.parsers:
            try:
                logger.debug(f"Попытка парсинга с {parser.name}...")

                # Проверяем, может ли парсер обработать страницу
                if not parser.can_parse(soup):
                    logger.debug(f"{parser.name} не может обработать страницу, пропускаем")
                    continue

                # Пытаемся распарсить
                result = parser.parse(soup, url)

                if result:
                    logger.info(f"✅ Парсинг успешен с помощью {parser.name}")
                    return result
                else:
                    logger.debug(f"{parser.name} вернул None")

            except Exception as e:
                logger.warning(f"Ошибка в парсере {parser.name}: {e}", exc_info=True)
                continue

        # Все парсеры провалились
        logger.error("❌ Все парсеры провалились для URL: {url}")
        return None

    def get_parser_stats(self) -> dict:
        """
        Возвращает статистику парсеров.

        Returns:
            Dict с информацией о парсерах
        """
        return {
            'parsers_count': len(self.parsers),
            'parsers': [
                {
                    'name': p.name,
                    'priority': p.priority,
                }
                for p in self.parsers
            ]
        }
