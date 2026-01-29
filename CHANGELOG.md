# Changelog

## [2.1.0] - 2026-01-29

### Добавлено

#### Fallback-парсинг (P0 Critical)
- **Каскадная система парсеров** с приоритетами:
  1. **JSON-LD парсер** (приоритет 1) - Schema.org MusicRecording
  2. **Open Graph парсер** (приоритет 2) - OG meta tags (og:title, og:audio:artist, music:duration)
  3. **HTML/CSS парсер** (приоритет 3) - CSS селекторы с множественными fallback'ами
- Автоматическое переключение при неудаче одного парсера
- Поддержка различных форматов данных на странице
- Устойчивость к изменениям структуры сайта

#### Защита от блокировок (P0 Critical)
- **User-Agent rotation**:
  - 6 различных User-Agent строк
  - Chrome, Firefox, Safari, Edge
  - Windows и macOS варианты
- **Браузерные заголовки**:
  - Accept, Accept-Language, Accept-Encoding
  - Connection: keep-alive
  - Sec-Fetch-* headers для Chrome-подобных браузеров
  - Upgrade-Insecure-Requests, Cache-Control
- **Exponential backoff с jitter**:
  - Начальная задержка: 1 секунда
  - Множитель: 2.0
  - Максимальная задержка: 60 секунд
  - Случайный разброс ±10% (jitter)
- **HTTP/2 поддержка** для более быстрых запросов
- **Retry-After header** для 429 ответов

#### Улучшенная обработка артистов (P0 Critical)
- **Форматирование нескольких артистов**:
  - 1 артист: `"Artist"`
  - 2 артиста: `"Artist1 feat. Artist2"`
  - 3+ артистов: `"Artist1 feat. Artist2, Artist3"`
- Поддержка JSON-LD форматов (dict и list)
- Graceful fallback для отсутствующих артистов

#### Кэширование (P0 Critical)
- **In-memory TTL кэш**:
  - Библиотека: cachetools.TTLCache
  - Дефолт: 1000 записей, TTL 1 час
  - Автоматическое удаление устаревших записей
- **Статистика кэша**:
  - Размер кэша (size/maxsize)
  - Количество попаданий (hits)
  - Количество промахов (misses)
  - Процент попаданий (hit_rate)
- **Методы управления**:
  - `get_cache_stats()` - получение статистики
  - `clear_cache()` - очистка кэша
- Логирование статистики при shutdown

#### Архитектурные улучшения
- **RequestManager** - централизованное управление HTTP-запросами
- **CascadeParser** - orchestration нескольких парсеров
- **TrackCache** - централизованное кэширование
- Модульная структура парсеров (src/parsers/)
- Утилиты для работы с артистами (src/utils/artists.py)

### Изменено

#### YandexMusicParser
- Использует RequestManager вместо прямого httpx.AsyncClient
- Использует CascadeParser вместо прямого JSON-LD парсинга
- Добавлен TrackCache для кэширования
- Упрощена логика get_track_info (удалены специфичные JSON-LD методы)
- Параметры конфигурации: cache_maxsize, cache_ttl, max_retries

#### Handlers
- Передача track_id в parser.get_track_info() для кэширования
- Формат cache_key: "album_id:track_id"

#### Зависимости
- Добавлена `cachetools==5.3.2` для TTL кэша
- Добавлена `lxml==5.1.0` для более быстрого парсинга HTML

### Производительность

- **Кэширование**: Мгновенный ответ для повторных запросов
- **HTTP/2**: Быстрее чем HTTP/1.1 для множественных запросов
- **lxml парсер**: В 5-10 раз быстрее html.parser для BeautifulSoup
- **User-Agent rotation**: Снижает риск rate-limiting

### Документация

- Обновлён CHANGELOG.md с описанием v2.1.0
- Inline docstrings для всех новых компонентов
- Описание cascade стратегии в parsers/cascade.py

---

## [2.0.0] - 2026-01-29

### Добавлено

#### Система обработки ошибок
- **4-этапная валидация** входящих данных
- **30+ типов исключений** с детальными сообщениями пользователю
- Иерархия исключений: `ValidationError`, `HttpError`, `NetworkError`, `ParsingError`

#### Улучшенная валидация URL
- Поддержка **5 доменов**: .ru, .com, .by, .kz, .ua
- Детектирование **разных типов страниц**:
  - Альбомы (`/album/123`)
  - Артисты (`/artist/123`)
  - Плейлисты (`/users/.../playlists/...`)
- Специфичные сообщения об ошибках для каждого типа

#### Retry-политика
- Автоматические повторные попытки при:
  - HTTP 502, 503, 504 (до 2 раз)
  - Connect timeout (до 2 раз)
  - Read timeout (до 2 раз)
  - Remote protocol error (до 2 раз)
- Задержка между попытками: 1 секунда

#### HTTP-ошибки
Специализированные обработчики для:
- 400 Bad Request
- 403 Forbidden (геоблокировка)
- 404 Not Found
- 410 Gone (трек удалён)
- 429 Too Many Requests
- 500 Internal Server Error
- 502 Bad Gateway
- 503 Service Unavailable
- 504 Gateway Timeout

#### Сетевые ошибки
- Connect timeout
- Read timeout
- Connection error
- SSL error
- Remote protocol error

#### Парсинг с валидацией
- Проверка типа JSON-LD схемы
- Валидация обязательных полей
- Проверка пустых значений
- Graceful degradation для необязательных полей

#### Логирование
- Разные уровни логирования по типу ошибки
- DEBUG для ошибок пользователя
- INFO для информационных событий
- WARNING для временных проблем
- ERROR для проблем сервиса
- CRITICAL для критических ошибок

### Изменено

#### Структура проекта
- Добавлен модуль `exceptions.py` с иерархией исключений
- Улучшен `validators.py` с детальной валидацией
- Переработан `yandex_parser.py` с retry-логикой
- Обновлён `handlers/common.py` с обработкой исключений

#### Конфигурация
- Добавлены параметры retry: `MAX_RETRIES`, `RETRY_DELAY`, `RETRY_STATUS_CODES`
- Удалён устаревший `YANDEX_MUSIC_URL_PATTERN` (перенесён в validators)

#### Обработчики сообщений
- Объединены `handle_url` и `handle_unknown_message` в один `handle_message`
- Добавлена функция `send_error_message` для безопасной отправки ошибок
- Улучшено логирование с ID пользователей

### Документация

Добавлены файлы:
- `ERROR_HANDLING.md` - подробная документация по обработке ошибок
- `CHANGELOG.md` - история изменений
- Обновлён `README.md` с новыми возможностями
- Обновлён `QUICKSTART.md`

### Безопасность

- HTML-экранирование всех выводимых данных
- Валидация доменов для защиты от SSRF
- Таймауты для всех HTTP-запросов
- Graceful degradation при отсутствии данных

---

## [1.0.0] - 2026-01-29

### Начальная версия

- Базовая функциональность парсинга треков
- Команды /start и /help
- Извлечение JSON-LD метаданных
- Форматирование вывода
- Асинхронная архитектура
