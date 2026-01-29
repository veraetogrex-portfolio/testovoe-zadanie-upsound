"""
Базовый класс для парсеров.
"""

from abc import ABC, abstractmethod
from typing import Optional
from bs4 import BeautifulSoup

from src.models.track import TrackInfo


class BaseParser(ABC):
    """Базовый класс для всех парсеров"""

    @property
    @abstractmethod
    def name(self) -> str:
        """Имя парсера для логирования"""
        pass

    @property
    @abstractmethod
    def priority(self) -> int:
        """Приоритет парсера (меньше = выше приоритет)"""
        pass

    @abstractmethod
    def parse(self, soup: BeautifulSoup, url: str) -> Optional[TrackInfo]:
        """
        Парсит HTML и возвращает информацию о треке.

        Args:
            soup: Распарсенный HTML
            url: URL страницы

        Returns:
            TrackInfo или None если парсинг не удался
        """
        pass

    def can_parse(self, soup: BeautifulSoup) -> bool:
        """
        Проверяет, может ли парсер обработать данную страницу.

        Args:
            soup: Распарсенный HTML

        Returns:
            True если парсер может обработать страницу
        """
        return True
