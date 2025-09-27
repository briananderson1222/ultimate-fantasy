"""
API response caching layer.

Provides intelligent HTTP response caching with:
- Multi-tier caching strategy
- Cache invalidation and warming
- Conditional caching based on request patterns
- Performance monitoring
- Memory and Redis-based storage
"""

import asyncio
import gzip
import hashlib
import json
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

try:
    from infrastructure.cache.redis_pool import get_redis_pool
except ImportError:
    get_redis_pool = None

try:
    from infrastructure.logging.domain_logger import get_logger
except ImportError:
    import logging

    get_logger = logging.getLogger

logger = get_logger(__name__)


class CacheStrategy(Enum):
    """Cache strategy types."""

    NO_CACHE = "no_cache"
    MEMORY_ONLY = "memory_only"
    REDIS_ONLY = "redis_only"
    MULTI_TIER = "multi_tier"


class CacheControl(Enum):
    """Cache control directives."""

    NO_CACHE = "no-cache"
    NO_STORE = "no-store"
    PRIVATE = "private"
    PUBLIC = "public"
    MUST_REVALIDATE = "must-revalidate"


@dataclass
class CacheRule:
    """Cache rule configuration."""

    path_pattern: str
    methods: set[str] = field(default_factory=lambda: {"GET"})
    ttl_seconds: int = 300
    strategy: CacheStrategy = CacheStrategy.MULTI_TIER
    cache_control: list[CacheControl] = field(default_factory=list)

    # Conditional caching
    cache_if: Callable[[Request], bool] | None = None
    skip_if: Callable[[Request], bool] | None = None

    # Response filtering
    cache_status_codes: set[int] = field(default_factory=lambda: {200})
    max_response_size: int = 1024 * 1024  # 1MB
    min_response_size: int = 0

    # Compression
    compress_response: bool = True
    compression_threshold: int = 1024

    # Cache warming
    warm_cache: bool = False
    warm_interval_seconds: int = 3600


@dataclass
class CacheEntry:
    """Cache entry with metadata."""

    key: str
    content: bytes
    content_type: str
    status_code: int
    headers: dict[str, str]
    created_at: datetime
    expires_at: datetime
    access_count: int = 0
    last_accessed: datetime = field(default_factory=datetime.utcnow)
    compressed: bool = False
    size: int = 0


@dataclass
class CacheMetrics:
    """Cache performance metrics."""

    hits: int = 0
    misses: int = 0
    stores: int = 0
    evictions: int = 0
    errors: int = 0

    # Performance metrics
    avg_hit_time_ms: float = 0.0
    avg_miss_time_ms: float = 0.0
    avg_store_time_ms: float = 0.0

    # Size metrics
    memory_entries: int = 0
    memory_size_bytes: int = 0
    redis_entries: int = 0
    redis_size_bytes: int = 0


class MemoryCache:
    """Memory-based cache implementation."""

    def __init__(self, max_size: int = 100, max_memory_mb: int = 100):
        self.max_size = max_size
        self.max_memory_bytes = max_memory_mb * 1024 * 1024
        self.cache: dict[str, CacheEntry] = {}
        self.access_order: list[str] = []
        self.current_size = 0

    async def get(self, key: str) -> CacheEntry | None:
        """Get entry from memory cache."""
        if key not in self.cache:
            return None

        entry = self.cache[key]

        # Check expiration
        if datetime.utcnow() > entry.expires_at:
            await self.delete(key)
            return None

        # Update access info
        entry.access_count += 1
        entry.last_accessed = datetime.utcnow()

        # Update LRU order
        if key in self.access_order:
            self.access_order.remove(key)
        self.access_order.append(key)

        return entry

    async def set(self, key: str, entry: CacheEntry):
        """Set entry in memory cache."""
        # Remove existing entry
        if key in self.cache:
            await self.delete(key)

        # Check if we need to evict entries
        await self._ensure_capacity(entry.size)

        # Add new entry
        self.cache[key] = entry
        self.access_order.append(key)
        self.current_size += entry.size

    async def delete(self, key: str) -> bool:
        """Delete entry from memory cache."""
        if key not in self.cache:
            return False

        entry = self.cache[key]
        del self.cache[key]

        if key in self.access_order:
            self.access_order.remove(key)

        self.current_size -= entry.size
        return True

    async def clear(self):
        """Clear all entries from memory cache."""
        self.cache.clear()
        self.access_order.clear()
        self.current_size = 0

    async def _ensure_capacity(self, new_entry_size: int):
        """Ensure cache has capacity for new entry."""
        # Check size limit
        while (
            len(self.cache) >= self.max_size
            or self.current_size + new_entry_size > self.max_memory_bytes
        ):

            if not self.access_order:
                break

            # Evict least recently used
            lru_key = self.access_order[0]
            await self.delete(lru_key)

    def get_stats(self) -> dict[str, Any]:
        """Get memory cache statistics."""
        return {
            "entries": len(self.cache),
            "size_bytes": self.current_size,
            "max_size": self.max_size,
            "max_memory_bytes": self.max_memory_bytes,
            "memory_usage_percent": (self.current_size / self.max_memory_bytes) * 100,
        }


class RedisCache:
    """Redis-based cache implementation."""

    def __init__(self, redis_pool=None, key_prefix: str = "response_cache"):
        self.redis_pool = redis_pool
        self.key_prefix = key_prefix

    def _make_key(self, key: str) -> str:
        """Make Redis key with prefix."""
        return f"{self.key_prefix}:{key}"

    async def get(self, key: str) -> CacheEntry | None:
        """Get entry from Redis cache."""
        if not self.redis_pool:
            return None

        try:
            redis_key = self._make_key(key)
            data = await self.redis_pool.redis_client.get(redis_key)

            if not data:
                return None

            # Deserialize entry
            entry_data = json.loads(data)

            entry = CacheEntry(
                key=entry_data["key"],
                content=(
                    entry_data["content"].encode()
                    if isinstance(entry_data["content"], str)
                    else entry_data["content"]
                ),
                content_type=entry_data["content_type"],
                status_code=entry_data["status_code"],
                headers=entry_data["headers"],
                created_at=datetime.fromisoformat(entry_data["created_at"]),
                expires_at=datetime.fromisoformat(entry_data["expires_at"]),
                access_count=entry_data.get("access_count", 0),
                last_accessed=datetime.fromisoformat(
                    entry_data.get("last_accessed", datetime.utcnow().isoformat())
                ),
                compressed=entry_data.get("compressed", False),
                size=entry_data.get("size", 0),
            )

            # Check expiration
            if datetime.utcnow() > entry.expires_at:
                await self.delete(key)
                return None

            # Update access info
            entry.access_count += 1
            entry.last_accessed = datetime.utcnow()

            return entry

        except Exception as e:
            logger.error(f"Redis cache get error: {e}")
            return None

    async def set(self, key: str, entry: CacheEntry, ttl: int):
        """Set entry in Redis cache."""
        if not self.redis_pool:
            return

        try:
            redis_key = self._make_key(key)

            # Serialize entry
            entry_data = {
                "key": entry.key,
                "content": (
                    entry.content.decode()
                    if isinstance(entry.content, bytes)
                    else entry.content
                ),
                "content_type": entry.content_type,
                "status_code": entry.status_code,
                "headers": entry.headers,
                "created_at": entry.created_at.isoformat(),
                "expires_at": entry.expires_at.isoformat(),
                "access_count": entry.access_count,
                "last_accessed": entry.last_accessed.isoformat(),
                "compressed": entry.compressed,
                "size": entry.size,
            }

            await self.redis_pool.redis_client.setex(
                redis_key, ttl, json.dumps(entry_data)
            )

        except Exception as e:
            logger.error(f"Redis cache set error: {e}")

    async def delete(self, key: str) -> bool:
        """Delete entry from Redis cache."""
        if not self.redis_pool:
            return False

        try:
            redis_key = self._make_key(key)
            result = await self.redis_pool.redis_client.delete(redis_key)
            return result > 0

        except Exception as e:
            logger.error(f"Redis cache delete error: {e}")
            return False

    async def clear(self):
        """Clear all entries from Redis cache."""
        if not self.redis_pool:
            return

        try:
            pattern = f"{self.key_prefix}:*"
            keys = await self.redis_pool.redis_client.keys(pattern)
            if keys:
                await self.redis_pool.redis_client.delete(*keys)

        except Exception as e:
            logger.error(f"Redis cache clear error: {e}")


class ResponseCacheMiddleware(BaseHTTPMiddleware):
    """
    HTTP response caching middleware with intelligent caching strategies.
    """

    def __init__(
        self,
        app,
        cache_rules: list[CacheRule],
        memory_cache_size: int = 100,
        memory_cache_mb: int = 100,
        default_ttl: int = 300,
        enable_redis: bool = True,
    ):
        super().__init__(app)
        self.cache_rules = {rule.path_pattern: rule for rule in cache_rules}
        self.default_ttl = default_ttl
        self.enable_redis = enable_redis

        # Initialize caches
        self.memory_cache = MemoryCache(memory_cache_size, memory_cache_mb)
        self.redis_cache: RedisCache | None = None

        # Metrics
        self.metrics = CacheMetrics()

        # Background tasks
        self._cleanup_task: asyncio.Task | None = None
        self._warming_task: asyncio.Task | None = None

        # Initialized flag
        self._initialized = False

    async def _initialize(self):
        """Initialize async components."""
        if self._initialized:
            return

        # Initialize Redis cache if enabled
        if self.enable_redis and get_redis_pool:
            try:
                redis_pool = await get_redis_pool()
                self.redis_cache = RedisCache(redis_pool)
            except Exception as e:
                logger.warning(f"Redis cache not available: {e}")

        # Start background tasks
        self._cleanup_task = asyncio.create_task(self._cleanup_loop())
        if any(rule.warm_cache for rule in self.cache_rules.values()):
            self._warming_task = asyncio.create_task(self._warming_loop())

        self._initialized = True

    async def dispatch(self, request: Request, call_next):
        """Process request with caching."""
        await self._initialize()

        # Find matching cache rule
        cache_rule = self._find_cache_rule(request)
        if not cache_rule or not self._should_cache_request(request, cache_rule):
            return await call_next(request)

        # Generate cache key
        cache_key = self._generate_cache_key(request)

        # Try to get from cache
        start_time = time.time()
        cached_entry = await self._get_from_cache(cache_key, cache_rule.strategy)

        if cached_entry:
            # Cache hit
            hit_time = (time.time() - start_time) * 1000
            self.metrics.hits += 1
            self._update_avg_hit_time(hit_time)

            # Create response from cache
            response = self._create_response_from_cache(cached_entry)
            response.headers["X-Cache"] = "HIT"
            response.headers["X-Cache-Key"] = cache_key

            return response

        # Cache miss - process request
        miss_time = (time.time() - start_time) * 1000
        self.metrics.misses += 1
        self._update_avg_miss_time(miss_time)

        response = await call_next(request)

        # Check if response should be cached
        if self._should_cache_response(response, cache_rule):
            await self._store_in_cache(cache_key, request, response, cache_rule)

        response.headers["X-Cache"] = "MISS"
        response.headers["X-Cache-Key"] = cache_key

        return response

    def _find_cache_rule(self, request: Request) -> CacheRule | None:
        """Find matching cache rule for request."""
        import re

        for pattern, rule in self.cache_rules.items():
            if re.match(pattern, request.url.path):
                return rule

        return None

    def _should_cache_request(self, request: Request, rule: CacheRule) -> bool:
        """Check if request should be cached."""
        # Check method
        if request.method not in rule.methods:
            return False

        # Check conditional rules
        if rule.skip_if and rule.skip_if(request):
            return False

        if rule.cache_if and not rule.cache_if(request):
            return False

        # Check cache-control headers
        cache_control = request.headers.get("cache-control", "")
        return not ("no-cache" in cache_control or "no-store" in cache_control)

    def _should_cache_response(self, response: Response, rule: CacheRule) -> bool:
        """Check if response should be cached."""
        # Check status code
        if response.status_code not in rule.cache_status_codes:
            return False

        # Check response size
        content_length = response.headers.get("content-length")
        if content_length:
            size = int(content_length)
            if size > rule.max_response_size or size < rule.min_response_size:
                return False

        # Check cache-control headers
        cache_control = response.headers.get("cache-control", "")
        return not ("no-cache" in cache_control or "no-store" in cache_control or "private" in cache_control)

    def _generate_cache_key(self, request: Request) -> str:
        """Generate cache key for request."""
        # Include method, path, query params, and relevant headers
        key_parts = [
            request.method,
            request.url.path,
            str(sorted(request.query_params.items())),
        ]

        # Include user-specific info if authenticated
        if hasattr(request.state, "user_id") and request.state.user_id:
            key_parts.append(f"user:{request.state.user_id}")

        # Include relevant headers for cache variation
        vary_headers = ["accept", "accept-encoding", "accept-language"]
        for header in vary_headers:
            value = request.headers.get(header)
            if value:
                key_parts.append(f"{header}:{value}")

        key_string = "|".join(key_parts)
        return hashlib.sha256(key_string.encode()).hexdigest()

    async def _get_from_cache(
        self, key: str, strategy: CacheStrategy
    ) -> CacheEntry | None:
        """Get entry from cache based on strategy."""
        if strategy == CacheStrategy.NO_CACHE:
            return None

        # Try memory cache first
        if strategy in [CacheStrategy.MEMORY_ONLY, CacheStrategy.MULTI_TIER]:
            entry = await self.memory_cache.get(key)
            if entry:
                return entry

        # Try Redis cache
        if (
            strategy in [CacheStrategy.REDIS_ONLY, CacheStrategy.MULTI_TIER]
            and self.redis_cache
        ):
            entry = await self.redis_cache.get(key)
            if entry and strategy == CacheStrategy.MULTI_TIER:
                # Store in memory cache for faster access
                await self.memory_cache.set(key, entry)
            return entry

        return None

    async def _store_in_cache(
        self, key: str, request: Request, response: Response, rule: CacheRule
    ):
        """Store response in cache."""
        try:
            store_start = time.time()

            # Read response body
            response_body = b""
            async for chunk in response.body_iterator:
                response_body += chunk

            # Create new response with body
            response.body_iterator = iter([response_body])

            # Compress if needed
            compressed = False
            if (
                rule.compress_response
                and len(response_body) >= rule.compression_threshold
            ):
                response_body = gzip.compress(response_body)
                compressed = True

            # Create cache entry
            entry = CacheEntry(
                key=key,
                content=response_body,
                content_type=response.headers.get("content-type", ""),
                status_code=response.status_code,
                headers=dict(response.headers),
                created_at=datetime.utcnow(),
                expires_at=datetime.utcnow() + timedelta(seconds=rule.ttl_seconds),
                compressed=compressed,
                size=len(response_body),
            )

            # Store based on strategy
            if rule.strategy in [CacheStrategy.MEMORY_ONLY, CacheStrategy.MULTI_TIER]:
                await self.memory_cache.set(key, entry)

            if (
                rule.strategy in [CacheStrategy.REDIS_ONLY, CacheStrategy.MULTI_TIER]
                and self.redis_cache
            ):
                await self.redis_cache.set(key, entry, rule.ttl_seconds)

            # Update metrics
            store_time = (time.time() - store_start) * 1000
            self.metrics.stores += 1
            self._update_avg_store_time(store_time)

            # Add cache headers to response
            response.headers["Cache-Control"] = f"max-age={rule.ttl_seconds}"
            if CacheControl.PUBLIC in rule.cache_control:
                response.headers["Cache-Control"] += ", public"
            elif CacheControl.PRIVATE in rule.cache_control:
                response.headers["Cache-Control"] += ", private"

        except Exception as e:
            self.metrics.errors += 1
            logger.error(f"Cache store error: {e}")

    def _create_response_from_cache(self, entry: CacheEntry) -> Response:
        """Create HTTP response from cache entry."""
        content = entry.content

        # Decompress if needed
        if entry.compressed:
            content = gzip.decompress(content)

        response = Response(
            content=content,
            status_code=entry.status_code,
            headers=entry.headers,
            media_type=entry.content_type,
        )

        # Add cache-specific headers
        response.headers["Age"] = str(
            int((datetime.utcnow() - entry.created_at).total_seconds())
        )
        response.headers["X-Cache-Created"] = entry.created_at.isoformat()
        response.headers["X-Cache-Expires"] = entry.expires_at.isoformat()

        return response

    def _update_avg_hit_time(self, hit_time: float):
        """Update average hit time."""
        if self.metrics.hits == 1:
            self.metrics.avg_hit_time_ms = hit_time
        else:
            self.metrics.avg_hit_time_ms = (
                self.metrics.avg_hit_time_ms * (self.metrics.hits - 1) + hit_time
            ) / self.metrics.hits

    def _update_avg_miss_time(self, miss_time: float):
        """Update average miss time."""
        if self.metrics.misses == 1:
            self.metrics.avg_miss_time_ms = miss_time
        else:
            self.metrics.avg_miss_time_ms = (
                self.metrics.avg_miss_time_ms * (self.metrics.misses - 1) + miss_time
            ) / self.metrics.misses

    def _update_avg_store_time(self, store_time: float):
        """Update average store time."""
        if self.metrics.stores == 1:
            self.metrics.avg_store_time_ms = store_time
        else:
            self.metrics.avg_store_time_ms = (
                self.metrics.avg_store_time_ms * (self.metrics.stores - 1) + store_time
            ) / self.metrics.stores

    async def _cleanup_loop(self):
        """Background cleanup loop."""
        while True:
            try:
                await asyncio.sleep(300)  # Run every 5 minutes
                # Memory cache cleanup is handled automatically via LRU
                # Redis cleanup is handled via TTL

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Cache cleanup error: {e}")

    async def _warming_loop(self):
        """Background cache warming loop."""
        while True:
            try:
                await asyncio.sleep(60)  # Check every minute

                for rule in self.cache_rules.values():
                    if rule.warm_cache:
                        # Implement cache warming logic here
                        pass

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Cache warming error: {e}")

    async def invalidate_cache(self, pattern: str | None = None):
        """Invalidate cache entries matching pattern."""
        if pattern:
            # Invalidate specific pattern
            # This would require more sophisticated key tracking
            pass
        else:
            # Clear all cache
            await self.memory_cache.clear()
            if self.redis_cache:
                await self.redis_cache.clear()

    def get_cache_stats(self) -> dict[str, Any]:
        """Get cache statistics."""
        hit_rate = 0.0
        if self.metrics.hits + self.metrics.misses > 0:
            hit_rate = self.metrics.hits / (self.metrics.hits + self.metrics.misses)

        memory_stats = self.memory_cache.get_stats()

        return {
            "hit_rate": hit_rate,
            "hits": self.metrics.hits,
            "misses": self.metrics.misses,
            "stores": self.metrics.stores,
            "evictions": self.metrics.evictions,
            "errors": self.metrics.errors,
            "avg_hit_time_ms": self.metrics.avg_hit_time_ms,
            "avg_miss_time_ms": self.metrics.avg_miss_time_ms,
            "avg_store_time_ms": self.metrics.avg_store_time_ms,
            "memory_cache": memory_stats,
            "redis_enabled": self.redis_cache is not None,
        }
