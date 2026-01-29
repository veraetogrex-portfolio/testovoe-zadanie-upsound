"""
Утилиты для форматирования данных.
"""

import isodate
from datetime import timedelta
from typing import Optional

from src.models.track import TrackInfo


def parse_iso_duration(iso_duration: str) -> Optional[str]:
    """
    Преобразование ISO 8601 duration в формат MM:SS.

    Args:
        iso_duration: Строка в формате ISO 8601 (например, 'PT3M45S')

    Returns:
        Строка в формате MM:SS или None при ошибке парсинга

    Examples:
        >>> parse_iso_duration('PT3M45S')
        '3:45'

        >>> parse_iso_duration('PT1H2M30S')
        '62:30'

        >>> parse_iso_duration('PT45S')
        '0:45'
    """
    try:
        duration: timedelta = isodate.parse_duration(iso_duration)
        total_seconds = int(duration.total_seconds())
        minutes = total_seconds // 60
        seconds = total_seconds % 60
        return f"{minutes}:{seconds:02d}"
    except (isodate.ISO8601Error, ValueError, AttributeError):
        return None


def format_track_message(track_info: TrackInfo) -> str:
    """
    Форматирование информации о треке для отправки пользователю.

    Args:
        track_info: Объект TrackInfo

    Returns:
        Отформатированное сообщение с эмодзи
    """
    if not isinstance(track_info, TrackInfo):
        raise TypeError("track_info должен быть экземпляром TrackInfo")

    message_parts = [
        f"🎵 <b>Название:</b> {escape_html(track_info.name)}",
        f"👤 <b>Артист:</b> {escape_html(track_info.artist)}",
        f"⏱️ <b>Длительность:</b> {track_info.duration}"
    ]

    if track_info.album:
        message_parts.insert(2, f"💿 <b>Альбом:</b> {escape_html(track_info.album)}")

    return "\n".join(message_parts)


def escape_html(text: str) -> str:
    """
    Экранирование HTML-символов для безопасной отправки в Telegram.

    Args:
        text: Текст для экранирования

    Returns:
        Экранированный текст
    """
    return (text
            .replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;"))
