"""
Иерархия исключений бота.
"""


class YandexMusicBotError(Exception):
    """Базовый класс ошибок бота"""
    user_message: str = "Произошла ошибка"

    def __init__(self, message: str = None, user_message: str = None):
        self.message = message or self.__class__.__name__
        if user_message:
            self.user_message = user_message
        super().__init__(self.message)


# ═══════════════════════════════════════════════════════════
# Ошибки валидации входных данных (Этап 1)
# ═══════════════════════════════════════════════════════════

class ValidationError(YandexMusicBotError):
    """Ошибки валидации пользовательского ввода"""


class EmptyMessageError(ValidationError):
    user_message = "❌ Отправьте ссылку на трек"


class MessageTooLongError(ValidationError):
    user_message = "❌ Сообщение слишком длинное"


class NotUrlError(ValidationError):
    user_message = "❌ Это не похоже на ссылку. Отправьте ссылку на трек из Яндекс.Музыки"


class WrongDomainError(ValidationError):
    user_message = (
        "❌ Я работаю только с Яндекс.Музыкой. Отправьте ссылку вида:\n"
        "<code>https://music.yandex.ru/album/.../track/...</code>"
    )


class WrongServiceError(ValidationError):
    user_message = (
        "❌ Это не Яндекс.Музыка. Нужна ссылка вида:\n"
        "<code>https://music.yandex.ru/album/.../track/...</code>"
    )


class NotTrackUrlError(ValidationError):
    user_message = "❌ Это не ссылка на трек. Отправьте ссылку на конкретный трек"


class AlbumUrlError(NotTrackUrlError):
    user_message = (
        "❌ Это ссылка на альбом, а не на трек.\n"
        "Откройте конкретный трек и скопируйте ссылку на него"
    )


class ArtistUrlError(NotTrackUrlError):
    user_message = "❌ Это ссылка на артиста. Мне нужна ссылка на конкретный трек"


class PlaylistUrlError(NotTrackUrlError):
    user_message = "❌ Это ссылка на плейлист. Отправьте ссылку на конкретный трек"


class InvalidTrackIdError(ValidationError):
    user_message = "❌ Неверный формат ссылки. ID альбома и трека должны быть числами"


# ═══════════════════════════════════════════════════════════
# Ошибки HTTP-запросов (Этап 3)
# ═══════════════════════════════════════════════════════════

class HttpError(YandexMusicBotError):
    """Ошибки HTTP-запросов"""

    def __init__(self, status_code: int = None, message: str = None):
        self.status_code = status_code
        super().__init__(message)


class TrackNotFoundError(HttpError):
    user_message = "❌ Трек не найден. Возможно, он был удалён или ссылка неверна"


class TrackDeletedError(HttpError):
    user_message = "❌ Трек был удалён из Яндекс.Музыки"


class ForbiddenError(HttpError):
    user_message = "🔒 Доступ к треку ограничен (возможно, геоблокировка)"


class RateLimitError(HttpError):
    user_message = "⏳ Слишком много запросов. Подождите минуту и попробуйте снова"


class BadRequestError(HttpError):
    user_message = "⚠️ Некорректный запрос к Яндекс.Музыке"


class ServerError(HttpError):
    user_message = "⚠️ Ошибка на сервере Яндекс.Музыки. Попробуйте позже"


class ServiceUnavailableError(HttpError):
    user_message = "⚠️ Яндекс.Музыка временно недоступна. Попробуйте через пару минут"


class GatewayTimeoutError(HttpError):
    user_message = "⚠️ Сервер Яндекс.Музыки не отвечает. Попробуйте позже"


class BadGatewayError(HttpError):
    user_message = "⚠️ Яндекс.Музыка временно недоступна. Попробуйте через пару минут"


# ═══════════════════════════════════════════════════════════
# Сетевые ошибки
# ═══════════════════════════════════════════════════════════

class NetworkError(YandexMusicBotError):
    """Сетевые ошибки"""


class ConnectTimeoutError(NetworkError):
    user_message = "⏱️ Не удалось подключиться к Яндекс.Музыке. Проверьте, что сервис доступен"


class ReadTimeoutError(NetworkError):
    user_message = "⏱️ Яндекс.Музыка отвечает слишком долго. Попробуйте ещё раз"


class ConnectionError(NetworkError):
    user_message = "⚠️ Не удалось найти сервер Яндекс.Музыки"


class SSLError(NetworkError):
    user_message = "🔐 Ошибка безопасного соединения. Попробуйте позже"


class RemoteProtocolError(NetworkError):
    user_message = "⚠️ Соединение прервано. Попробуйте ещё раз"


# ═══════════════════════════════════════════════════════════
# Ошибки парсинга (Этап 4)
# ═══════════════════════════════════════════════════════════

class ParsingError(YandexMusicBotError):
    """Ошибки парсинга данных"""


class JsonLdNotFoundError(ParsingError):
    user_message = (
        "⚠️ Не удалось найти данные о треке на странице. "
        "Возможно, Яндекс изменил структуру сайта"
    )


class JsonParseError(ParsingError):
    user_message = "⚠️ Ошибка чтения данных. Попробуйте другой трек"


class WrongSchemaTypeError(ParsingError):
    user_message = "⚠️ Страница не содержит информации о треке"


class MissingFieldError(ParsingError):
    user_message = "⚠️ Не удалось получить полные данные о треке"

    def __init__(self, field_name: str):
        self.field_name = field_name
        super().__init__(f"Missing field: {field_name}")


class InvalidFieldTypeError(ParsingError):
    user_message = "⚠️ Получены некорректные данные"

    def __init__(self, field_name: str, expected_type: str):
        self.field_name = field_name
        self.expected_type = expected_type
        super().__init__(f"Invalid type for {field_name}: expected {expected_type}")


class EmptyFieldError(ParsingError):
    user_message = "⚠️ Получены пустые данные о треке"

    def __init__(self, field_name: str):
        self.field_name = field_name
        super().__init__(f"Empty field: {field_name}")


class InvalidDurationFormatError(ParsingError):
    user_message = "⚠️ Не удалось определить длительность трека"

    def __init__(self, duration: str):
        self.duration = duration
        super().__init__(f"Invalid duration format: {duration}")


# ═══════════════════════════════════════════════════════════
# Утилиты для маппинга исключений
# ═══════════════════════════════════════════════════════════

HTTP_ERROR_MAP = {
    400: BadRequestError,
    403: ForbiddenError,
    404: TrackNotFoundError,
    410: TrackDeletedError,
    429: RateLimitError,
    500: ServerError,
    502: BadGatewayError,
    503: ServiceUnavailableError,
    504: GatewayTimeoutError,
}


def get_http_error(status_code: int) -> type[HttpError]:
    """Получить класс исключения по HTTP-коду"""
    return HTTP_ERROR_MAP.get(status_code, ServerError)
