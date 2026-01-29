"""
Менеджер HTTP-запросов с защитой от блокировок.
"""

import random
import logging
import asyncio
from typing import Optional
import httpx

from src.config import REQUEST_TIMEOUT


logger = logging.getLogger(__name__)


# Пул User-Agent разных браузеров
USER_AGENTS = [
    # Chrome Windows
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    # Chrome macOS
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    # Firefox Windows
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
    # Firefox macOS
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:121.0) Gecko/20100101 Firefox/121.0",
    # Safari macOS
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15",
    # Edge Windows
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0",
]


class RequestManager:
    """
    Менеджер HTTP-запросов с защитой от блокировок.

    Возможности:
    - Ротация User-Agent
    - Браузерные заголовки
    - Сохранение cookies между запросами
    - Exponential backoff при ошибках
    - Retry с настраиваемой логикой
    """

    def __init__(
        self,
        timeout: float = REQUEST_TIMEOUT,
        max_retries: int = 3,
        initial_delay: float = 1.0,
        max_delay: float = 60.0,
        multiplier: float = 2.0,
        jitter: float = 0.1,
    ):
        """
        Args:
            timeout: Таймаут запроса (секунды)
            max_retries: Максимум попыток
            initial_delay: Начальная задержка при retry (секунды)
            max_delay: Максимальная задержка (секунды)
            multiplier: Множитель для exponential backoff
            jitter: Случайный разброс (±jitter * 100%)
        """
        self.timeout = timeout
        self.max_retries = max_retries
        self.initial_delay = initial_delay
        self.max_delay = max_delay
        self.multiplier = multiplier
        self.jitter = jitter

        # HTTP-клиент с сохранением cookies
        self.client = httpx.AsyncClient(
            timeout=timeout,
            follow_redirects=True,
            http2=True,  # HTTP/2 для более быстрых запросов
        )

    async def fetch(
        self,
        url: str,
        retry_on_status: tuple[int, ...] = (429, 500, 502, 503, 504),
    ) -> httpx.Response:
        """
        Выполняет HTTP-запрос с retry и защитой от блокировок.

        Args:
            url: URL для запроса
            retry_on_status: HTTP-коды для retry

        Returns:
            HTTP Response

        Raises:
            httpx.HTTPError: При ошибках после всех retry
        """
        last_exception = None

        for attempt in range(self.max_retries + 1):
            try:
                if attempt > 0:
                    # Exponential backoff с jitter
                    delay = self._calculate_backoff(attempt)
                    logger.info(f"Повторная попытка {attempt}/{self.max_retries} через {delay:.1f}с для {url}")
                    await asyncio.sleep(delay)

                # Генерация браузерных заголовков
                headers = self._get_browser_headers()

                # Выполнение запроса
                response = await self.client.get(url, headers=headers)

                # Проверка статус-кода
                if response.status_code in retry_on_status and attempt < self.max_retries:
                    # Для 429 пытаемся использовать Retry-After header
                    if response.status_code == 429:
                        retry_after = self._get_retry_after(response)
                        if retry_after:
                            logger.warning(f"HTTP 429, Retry-After: {retry_after}с")
                            await asyncio.sleep(min(retry_after, self.max_delay))
                            continue

                    logger.warning(f"HTTP {response.status_code}, retry...")
                    last_exception = httpx.HTTPStatusError(
                        f"Status {response.status_code}",
                        request=response.request,
                        response=response
                    )
                    continue

                # Проверяем успешность
                response.raise_for_status()

                # Успех!
                logger.debug(f"✅ Успешный запрос к {url} (попытка {attempt + 1})")
                return response

            except httpx.TimeoutException as e:
                logger.warning(f"Timeout для {url} (попытка {attempt + 1})")
                last_exception = e
                if attempt < self.max_retries:
                    continue
                raise

            except httpx.HTTPError as e:
                logger.warning(f"HTTP ошибка для {url}: {e}")
                last_exception = e
                if attempt < self.max_retries:
                    continue
                raise

        # Если дошли сюда - все retry исчерпаны
        if last_exception:
            raise last_exception

        # Не должно произойти
        raise httpx.HTTPError(f"Failed after {self.max_retries} retries")

    def _get_browser_headers(self) -> dict:
        """
        Генерирует заголовки, имитирующие браузер.

        Включает:
        - Случайный User-Agent
        - Accept headers
        - Accept-Language (ru)
        - Connection: keep-alive
        - Sec-Fetch-* headers (для Chrome)

        Returns:
            Dict с заголовками
        """
        user_agent = random.choice(USER_AGENTS)

        headers = {
            'User-Agent': user_agent,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
            'Accept-Language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Cache-Control': 'max-age=0',
        }

        # Sec-Fetch-* headers для Chrome-подобных браузеров
        if 'Chrome' in user_agent or 'Edg' in user_agent:
            headers.update({
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'none',
                'Sec-Fetch-User': '?1',
            })

        return headers

    def _calculate_backoff(self, attempt: int) -> float:
        """
        Вычисляет задержку для exponential backoff с jitter.

        Формула: initial_delay * (multiplier ^ (attempt - 1)) + random_jitter

        Args:
            attempt: Номер попытки (1, 2, 3, ...)

        Returns:
            Задержка в секундах
        """
        # Exponential backoff
        delay = self.initial_delay * (self.multiplier ** (attempt - 1))

        # Ограничиваем максимумом
        delay = min(delay, self.max_delay)

        # Добавляем jitter (±jitter * delay)
        jitter_amount = delay * self.jitter
        delay += random.uniform(-jitter_amount, jitter_amount)

        return max(0.0, delay)

    def _get_retry_after(self, response: httpx.Response) -> Optional[float]:
        """
        Извлекает значение Retry-After header.

        Args:
            response: HTTP Response

        Returns:
            Секунды до следующей попытки или None
        """
        retry_after = response.headers.get('Retry-After')
        if not retry_after:
            return None

        try:
            # Retry-After может быть в секундах или датой
            return float(retry_after)
        except ValueError:
            # Если это дата - игнорируем, используем свой backoff
            return None

    async def close(self):
        """Закрывает HTTP-клиент."""
        await self.client.aclose()
        logger.info("RequestManager закрыт")
