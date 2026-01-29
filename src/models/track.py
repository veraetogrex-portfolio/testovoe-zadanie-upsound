"""
Модели данных для треков.
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class TrackInfo:
    """
    Информация о треке Яндекс.Музыки.

    Attributes:
        name: Название трека
        artist: Имя артиста (или список артистов через запятую)
        duration: Длительность в формате MM:SS
        album: Название альбома (опционально)
        url: URL трека (опционально)
    """
    name: str
    artist: str
    duration: str
    album: Optional[str] = None
    url: Optional[str] = None

    def __str__(self) -> str:
        """Человекочитаемое представление трека."""
        return f"{self.artist} - {self.name} ({self.duration})"
