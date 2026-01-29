"""
Утилиты для форматирования артистов.
"""

from typing import Union


def extract_artists(by_artist: Union[dict, list, None]) -> str:
    """
    Извлекает и форматирует имена артистов из JSON-LD.

    Поддерживает:
    - Один артист (dict): {"@type": "MusicGroup", "name": "Кино"}
    - Несколько артистов (list): [{"name": "Miyagi"}, {"name": "Эндшпиль"}]

    Форматы вывода:
    - 1 артист: "Artist"
    - 2 артиста: "Artist1 feat. Artist2"
    - 3+ артистов: "Artist1 feat. Artist2, Artist3"

    Args:
        by_artist: Поле byArtist из JSON-LD

    Returns:
        Строка с артистами

    Examples:
        >>> extract_artists({"name": "Кино"})
        'Кино'

        >>> extract_artists([{"name": "Miyagi"}, {"name": "Эндшпиль"}])
        'Miyagi feat. Эндшпиль'

        >>> extract_artists([{"name": "DJ Snake"}, {"name": "Lil Jon"}, {"name": "Pitbull"}])
        'DJ Snake feat. Lil Jon, Pitbull'
    """
    if not by_artist:
        return 'Неизвестный артист'

    # Один артист (dict)
    if isinstance(by_artist, dict):
        name = by_artist.get('name', '').strip()
        return name if name else 'Неизвестный артист'

    # Несколько артистов (list)
    if isinstance(by_artist, list):
        names = []
        for artist in by_artist:
            if isinstance(artist, dict) and 'name' in artist:
                name = artist['name'].strip()
                if name:
                    names.append(name)

        if not names:
            return 'Неизвестный артист'

        if len(names) == 1:
            return names[0]

        if len(names) == 2:
            return f"{names[0]} feat. {names[1]}"

        # 3+ артистов
        return f"{names[0]} feat. {', '.join(names[1:])}"

    # Другой тип (на всякий случай)
    if isinstance(by_artist, str):
        return by_artist.strip() if by_artist.strip() else 'Неизвестный артист'

    return 'Неизвестный артист'
