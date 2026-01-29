"""
Утилиты для валидации данных.
"""

import re
from typing import Optional, Tuple
from urllib.parse import urlparse

from src.exceptions import (
    EmptyMessageError,
    MessageTooLongError,
    NotUrlError,
    WrongDomainError,
    WrongServiceError,
    AlbumUrlError,
    ArtistUrlError,
    PlaylistUrlError,
    InvalidTrackIdError,
)


# Regex для валидации URL треков
YANDEX_MUSIC_TRACK_PATTERN = re.compile(
    r'^https?://music\.yandex\.(ru|com|by|kz|ua)'
    r'/album/(?P<album_id>\d+)'
    r'/track/(?P<track_id>\d+)'
    r'(?:\?.*)?$'
)

# Regex для определения других типов страниц
YANDEX_MUSIC_ALBUM_PATTERN = re.compile(
    r'^https?://music\.yandex\.(ru|com|by|kz|ua)/album/\d+/?$'
)

YANDEX_MUSIC_ARTIST_PATTERN = re.compile(
    r'^https?://music\.yandex\.(ru|com|by|kz|ua)/artist/\d+'
)

YANDEX_MUSIC_PLAYLIST_PATTERN = re.compile(
    r'^https?://music\.yandex\.(ru|com|by|kz|ua)/users/.*/playlists/\d+'
)

# Константы
MAX_MESSAGE_LENGTH = 500


def validate_message(text: Optional[str]) -> str:
    """
    Валидация входящего сообщения (Этап 1).

    Args:
        text: Текст сообщения от пользователя

    Returns:
        Очищенный текст

    Raises:
        EmptyMessageError: Если сообщение пустое
        MessageTooLongError: Если сообщение слишком длинное
    """
    if not text or text.strip() == "":
        raise EmptyMessageError("Empty message")

    if len(text) > MAX_MESSAGE_LENGTH:
        raise MessageTooLongError(f"Message too long: {len(text)} chars")

    return text.strip()


def validate_yandex_music_url(url: str) -> Tuple[str, str]:
    """
    Валидация URL Яндекс.Музыки и извлечение ID альбома и трека (Этап 2).

    Args:
        url: URL для проверки

    Returns:
        Кортеж (album_id, track_id)

    Raises:
        NotUrlError: Если это не URL
        WrongDomainError: Если чужой домен
        WrongServiceError: Если домен Яндекса, но не Музыка
        AlbumUrlError: Если ссылка на альбом
        ArtistUrlError: Если ссылка на артиста
        PlaylistUrlError: Если ссылка на плейлист
        InvalidTrackIdError: Если невалидные ID

    Examples:
        >>> validate_yandex_music_url("https://music.yandex.ru/album/123/track/456")
        ('123', '456')

        >>> validate_yandex_music_url("https://music.yandex.com/album/123/track/456?from=serp")
        ('123', '456')
    """
    url = url.strip()

    # Проверка, что это вообще URL
    if not url.startswith(('http://', 'https://')):
        raise NotUrlError(f"Not a URL: {url}")

    # Парсинг URL
    try:
        parsed = urlparse(url)
    except Exception:
        raise NotUrlError(f"Invalid URL: {url}")

    # Проверка домена
    if not parsed.netloc:
        raise NotUrlError(f"No domain in URL: {url}")

    # Проверка, что это Яндекс.Музыка
    if not parsed.netloc.startswith('music.yandex.'):
        if 'yandex' in parsed.netloc:
            raise WrongServiceError(f"Not Yandex Music: {parsed.netloc}")
        else:
            raise WrongDomainError(f"Wrong domain: {parsed.netloc}")

    # Проверка типа страницы
    # Альбом
    if YANDEX_MUSIC_ALBUM_PATTERN.match(url):
        raise AlbumUrlError(f"Album URL: {url}")

    # Артист
    if YANDEX_MUSIC_ARTIST_PATTERN.match(url):
        raise ArtistUrlError(f"Artist URL: {url}")

    # Плейлист
    if YANDEX_MUSIC_PLAYLIST_PATTERN.match(url):
        raise PlaylistUrlError(f"Playlist URL: {url}")

    # Валидация URL трека
    match = YANDEX_MUSIC_TRACK_PATTERN.match(url)
    if not match:
        # Попробуем понять, почему не подошло
        if '/album/' in url and '/track/' not in url:
            raise AlbumUrlError(f"Album URL: {url}")
        elif '/track/' in url:
            raise InvalidTrackIdError(f"Invalid track ID in URL: {url}")
        else:
            raise WrongServiceError(f"Not a track URL: {url}")

    album_id = match.group('album_id')
    track_id = match.group('track_id')

    return album_id, track_id


def is_valid_yandex_music_url(url: str) -> bool:
    """
    Проверка, является ли URL валидной ссылкой на трек Яндекс.Музыки.

    Args:
        url: URL для проверки

    Returns:
        True если URL валиден, иначе False
    """
    try:
        validate_yandex_music_url(url)
        return True
    except Exception:
        return False


def is_yandex_music_url(url: str) -> bool:
    """
    Проверка, является ли URL ссылкой на Яндекс.Музыку (любого типа).

    Args:
        url: URL для проверки

    Returns:
        True если это ссылка на Яндекс.Музыку
    """
    try:
        parsed = urlparse(url.strip())
        return parsed.netloc.startswith('music.yandex.')
    except Exception:
        return False
