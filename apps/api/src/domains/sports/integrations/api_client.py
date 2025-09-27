"""
Generic sports API client with rate limiting and error handling.
"""

import asyncio
import logging
import time
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any

try:
    import httpx
except ImportError:
    httpx = None

try:
    import aiohttp
except ImportError:
    aiohttp = None


logger = logging.getLogger(__name__)


class APIError(Exception):
    """Base API error."""


class RateLimitError(APIError):
    """Rate limit exceeded."""

    def __init__(self, retry_after: int | None = None):
        self.retry_after = retry_after
        super().__init__(f"Rate limit exceeded. Retry after {retry_after} seconds")


class TimeoutError(APIError):
    """Request timeout."""


class AuthenticationError(APIError):
    """Authentication failed."""


@dataclass
class RateLimitConfig:
    """Rate limiting configuration."""

    requests_per_minute: int = 60
    burst_limit: int = 10
    window_size: int = 60  # seconds


@dataclass
class APIConfig:
    """API configuration."""

    base_url: str
    api_key: str | None = None
    timeout: int = 30
    max_retries: int = 3
    retry_delay: float = 1.0
    rate_limit: RateLimitConfig | None = None
    headers: dict[str, str] | None = None


class RateLimiter:
    """Token bucket rate limiter."""

    def __init__(self, config: RateLimitConfig):
        self.config = config
        self.tokens = config.burst_limit
        self.last_update = time.time()
        self.lock = asyncio.Lock()

    async def acquire(self) -> bool:
        """Acquire a rate limit token."""
        async with self.lock:
            now = time.time()

            # Add tokens based on time elapsed
            time_passed = now - self.last_update
            tokens_to_add = (time_passed / 60) * self.config.requests_per_minute
            self.tokens = min(self.config.burst_limit, self.tokens + tokens_to_add)
            self.last_update = now

            # Check if we have tokens available
            if self.tokens >= 1:
                self.tokens -= 1
                return True

            return False

    def time_until_token(self) -> float:
        """Time in seconds until next token is available."""
        if self.tokens >= 1:
            return 0.0

        tokens_needed = 1 - self.tokens
        return (tokens_needed / self.config.requests_per_minute) * 60


class SportsAPIClient:
    """
    Generic HTTP client for sports APIs with rate limiting and error handling.
    """

    def __init__(self, config: APIConfig):
        self.config = config
        self.rate_limiter = (
            RateLimiter(config.rate_limit) if config.rate_limit else None
        )
        self.session: Any | None = None

    async def __aenter__(self):
        """Async context manager entry."""
        await self._create_session()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self._close_session()

    async def _create_session(self):
        """Create HTTP session."""
        headers = {
            "User-Agent": "Ultimate Fantasy Platform/1.0",
            "Accept": "application/json",
            "Content-Type": "application/json",
        }

        if self.config.headers:
            headers.update(self.config.headers)

        if self.config.api_key:
            headers["Authorization"] = f"Bearer {self.config.api_key}"

        timeout_config = httpx.Timeout(self.config.timeout) if httpx else None

        if httpx:
            self.session = httpx.AsyncClient(
                timeout=timeout_config, headers=headers, follow_redirects=True
            )
        elif aiohttp:
            timeout = aiohttp.ClientTimeout(total=self.config.timeout)
            self.session = aiohttp.ClientSession(timeout=timeout, headers=headers)
        else:
            raise RuntimeError("No HTTP client available (install httpx or aiohttp)")

    async def _close_session(self):
        """Close HTTP session."""
        if self.session:
            (
                await self.session.aclose()
                if hasattr(self.session, "aclose")
                else await self.session.close()
            )
            self.session = None

    async def _wait_for_rate_limit(self):
        """Wait for rate limit if necessary."""
        if not self.rate_limiter:
            return

        while not await self.rate_limiter.acquire():
            wait_time = self.rate_limiter.time_until_token()
            logger.info(f"Rate limit hit, waiting {wait_time:.2f} seconds")
            await asyncio.sleep(wait_time)

    async def _make_request(
        self,
        method: str,
        endpoint: str,
        params: dict[str, Any] | None = None,
        data: dict[str, Any] | None = None,
        **kwargs,
    ) -> dict[str, Any]:
        """Make HTTP request with retries and error handling."""
        if not self.session:
            await self._create_session()

        url = f"{self.config.base_url.rstrip('/')}/{endpoint.lstrip('/')}"

        for attempt in range(self.config.max_retries + 1):
            try:
                await self._wait_for_rate_limit()

                if httpx and isinstance(self.session, httpx.AsyncClient):
                    response = await self.session.request(
                        method=method, url=url, params=params, json=data, **kwargs
                    )

                    if response.status_code == 429:
                        retry_after = int(response.headers.get("Retry-After", 60))
                        if attempt < self.config.max_retries:
                            logger.warning(
                                f"Rate limited, retrying after {retry_after}s"
                            )
                            await asyncio.sleep(retry_after)
                            continue
                        raise RateLimitError(retry_after)

                    if response.status_code == 401:
                        raise AuthenticationError("API authentication failed")

                    response.raise_for_status()
                    return response.json()

                elif aiohttp and isinstance(self.session, aiohttp.ClientSession):
                    async with self.session.request(
                        method=method, url=url, params=params, json=data, **kwargs
                    ) as response:

                        if response.status == 429:
                            retry_after = int(response.headers.get("Retry-After", 60))
                            if attempt < self.config.max_retries:
                                logger.warning(
                                    f"Rate limited, retrying after {retry_after}s"
                                )
                                await asyncio.sleep(retry_after)
                                continue
                            raise RateLimitError(retry_after)

                        if response.status == 401:
                            raise AuthenticationError("API authentication failed")

                        response.raise_for_status()
                        return await response.json()

            except (
                httpx.TimeoutException if httpx else Exception,
                aiohttp.ServerTimeoutError if aiohttp else Exception,
            ) as e:
                if attempt < self.config.max_retries:
                    delay = self.config.retry_delay * (
                        2**attempt
                    )  # Exponential backoff
                    logger.warning(f"Request timeout, retrying in {delay}s: {e}")
                    await asyncio.sleep(delay)
                    continue
                raise TimeoutError(
                    f"Request timed out after {self.config.max_retries} retries"
                )

            except Exception as e:
                if attempt < self.config.max_retries:
                    delay = self.config.retry_delay * (2**attempt)
                    logger.warning(f"Request failed, retrying in {delay}s: {e}")
                    await asyncio.sleep(delay)
                    continue
                raise APIError(f"Request failed: {e}")

        raise APIError("Maximum retries exceeded")

    async def get(
        self, endpoint: str, params: dict[str, Any] | None = None, **kwargs
    ) -> dict[str, Any]:
        """Make GET request."""
        return await self._make_request("GET", endpoint, params=params, **kwargs)

    async def post(
        self,
        endpoint: str,
        data: dict[str, Any] | None = None,
        params: dict[str, Any] | None = None,
        **kwargs,
    ) -> dict[str, Any]:
        """Make POST request."""
        return await self._make_request(
            "POST", endpoint, params=params, data=data, **kwargs
        )

    async def put(
        self,
        endpoint: str,
        data: dict[str, Any] | None = None,
        params: dict[str, Any] | None = None,
        **kwargs,
    ) -> dict[str, Any]:
        """Make PUT request."""
        return await self._make_request(
            "PUT", endpoint, params=params, data=data, **kwargs
        )

    async def delete(
        self, endpoint: str, params: dict[str, Any] | None = None, **kwargs
    ) -> dict[str, Any]:
        """Make DELETE request."""
        return await self._make_request("DELETE", endpoint, params=params, **kwargs)

    async def health_check(self) -> bool:
        """Check API health/connectivity."""
        try:
            # Most APIs have a status or health endpoint
            await self.get("/status")
            return True
        except:
            try:
                # Fallback: try a simple endpoint
                await self.get("/")
                return True
            except:
                return False


class CachedAPIClient(SportsAPIClient):
    """API client with response caching."""

    def __init__(self, config: APIConfig, cache_ttl: int = 300):
        super().__init__(config)
        self.cache: dict[str, dict[str, Any]] = {}
        self.cache_ttl = cache_ttl

    def _get_cache_key(
        self, method: str, endpoint: str, params: dict[str, Any] | None = None
    ) -> str:
        """Generate cache key for request."""
        key_parts = [method, endpoint]
        if params:
            sorted_params = sorted(params.items())
            key_parts.append(str(sorted_params))
        return "|".join(key_parts)

    def _is_cache_valid(self, cached_at: datetime) -> bool:
        """Check if cache entry is still valid."""
        return datetime.utcnow() - cached_at < timedelta(seconds=self.cache_ttl)

    async def _make_request(
        self,
        method: str,
        endpoint: str,
        params: dict[str, Any] | None = None,
        data: dict[str, Any] | None = None,
        use_cache: bool = True,
        **kwargs,
    ) -> dict[str, Any]:
        """Make request with caching for GET requests."""

        # Only cache GET requests
        if method == "GET" and use_cache:
            cache_key = self._get_cache_key(method, endpoint, params)

            if cache_key in self.cache:
                cached_entry = self.cache[cache_key]
                if self._is_cache_valid(cached_entry["cached_at"]):
                    logger.debug(f"Cache hit for {cache_key}")
                    return cached_entry["data"]
                else:
                    # Remove expired cache entry
                    del self.cache[cache_key]

        # Make the actual request
        response = await super()._make_request(method, endpoint, params, data, **kwargs)

        # Cache GET responses
        if method == "GET" and use_cache:
            cache_key = self._get_cache_key(method, endpoint, params)
            self.cache[cache_key] = {"data": response, "cached_at": datetime.utcnow()}
            logger.debug(f"Cached response for {cache_key}")

        return response

    def clear_cache(self, pattern: str | None = None):
        """Clear cache entries matching pattern."""
        if pattern is None:
            self.cache.clear()
            logger.info("Cleared all cache entries")
        else:
            keys_to_remove = [key for key in self.cache if pattern in key]
            for key in keys_to_remove:
                del self.cache[key]
            logger.info(
                f"Cleared {len(keys_to_remove)} cache entries matching '{pattern}'"
            )

    def get_cache_stats(self) -> dict[str, Any]:
        """Get cache statistics."""
        datetime.utcnow()
        valid_entries = sum(
            1
            for entry in self.cache.values()
            if self._is_cache_valid(entry["cached_at"])
        )

        return {
            "total_entries": len(self.cache),
            "valid_entries": valid_entries,
            "expired_entries": len(self.cache) - valid_entries,
            "cache_ttl": self.cache_ttl,
        }
