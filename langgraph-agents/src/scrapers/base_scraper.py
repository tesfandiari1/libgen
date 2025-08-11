import asyncio
import random
import time

import httpx
from tenacity import retry, stop_after_attempt, wait_random_exponential, retry_if_exception_type


class BaseHttpClient:
    """Minimal HTTP client with retries, rate limit, and UA rotation.

    - Sequential only (no parallel usage here)
    - 1 request/second rate limiting
    - Retries with exponential backoff and jitter
    - Simple user-agent rotation
    """

    DEFAULT_UAS = [
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
        "Mozilla/5.0 (iPhone; CPU iPhone OS 17_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1",
    ]

    def __init__(
        self,
        base_headers: dict[str, str] | None = None,
        request_interval_seconds: float = 1.0,
        timeout_seconds: float = 20.0,
        user_agents: list[str] | None = None,
    ) -> None:
        self._last_request_ts: float = 0.0
        self._interval = max(1.0, float(request_interval_seconds))
        self._timeout = httpx.Timeout(timeout_seconds)
        self._base_headers = base_headers or {}
        self._user_agents = user_agents or self.DEFAULT_UAS
        self._client = httpx.AsyncClient(follow_redirects=True, timeout=self._timeout)

    def _pick_user_agent(self) -> str:
        return random.choice(self._user_agents)

    async def _respect_rate_limit(self) -> None:
        now = time.monotonic()
        elapsed = now - self._last_request_ts
        sleep_for = self._interval - elapsed
        if sleep_for > 0:
            await asyncio.sleep(sleep_for)

    def _merge_headers(self, headers: dict[str, str] | None) -> dict[str, str]:
        merged = dict(self._base_headers)
        if headers:
            merged.update(headers)
        merged.setdefault("User-Agent", self._pick_user_agent())
        return merged

    @retry(
        reraise=True,
        stop=stop_after_attempt(3),
        wait=wait_random_exponential(multiplier=1, max=6),
        retry=retry_if_exception_type((httpx.HTTPError,)),
    )
    async def get(self, url: str, headers: dict[str, str] | None = None) -> str:
        await self._respect_rate_limit()
        response = await self._client.get(url, headers=self._merge_headers(headers))
        self._last_request_ts = time.monotonic()
        response.raise_for_status()
        return response.text

    async def close(self) -> None:
        await self._client.aclose()


