"""
Redis connection pool management for Ultimate Fantasy Platform.

Provides connection pooling, configuration management, and fantasy sports
specific caching patterns with high availability and performance optimization.
"""

import json
import logging
import os
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Any

import redis.asyncio as redis
from redis.asyncio.connection import ConnectionPool
from redis.exceptions import RedisError

logger = logging.getLogger(__name__)


class FantasyRedisConfig:
    """Configuration for Redis connection pool in fantasy sports context."""

    def __init__(
        self,
        host: str = "localhost",
        port: int = 6379,
        password: str | None = None,
        db: int = 0,
        max_connections: int = 20,
        retry_on_timeout: bool = True,
        health_check_interval: int = 30,
        socket_timeout: float = 5.0,
        socket_connect_timeout: float = 5.0,
        decode_responses: bool = True,
    ):
        """
        Initialize Redis configuration.

        Args:
            host: Redis server host
            port: Redis server port
            password: Redis password
            db: Redis database number
            max_connections: Maximum connections in pool
            retry_on_timeout: Whether to retry on timeout
            health_check_interval: Health check interval in seconds
            socket_timeout: Socket timeout in seconds
            socket_connect_timeout: Socket connection timeout in seconds
            decode_responses: Whether to decode responses automatically
        """
        self.host = host
        self.port = port
        self.password = password
        self.db = db
        self.max_connections = max_connections
        self.retry_on_timeout = retry_on_timeout
        self.health_check_interval = health_check_interval
        self.socket_timeout = socket_timeout
        self.socket_connect_timeout = socket_connect_timeout
        self.decode_responses = decode_responses

        # Load from environment variables
        self._load_from_env()

    def _load_from_env(self):
        """Load configuration from environment variables."""
        self.host = os.getenv("REDIS_HOST", self.host)
        self.port = int(os.getenv("REDIS_PORT", str(self.port)))
        self.password = os.getenv("REDIS_PASSWORD", self.password)
        self.db = int(os.getenv("REDIS_DB", str(self.db)))
        self.max_connections = int(
            os.getenv("REDIS_MAX_CONNECTIONS", str(self.max_connections))
        )

    def get_connection_kwargs(self) -> dict[str, Any]:
        """
        Get connection parameters for Redis.

        Returns:
            Dictionary of connection parameters
        """
        kwargs = {
            "host": self.host,
            "port": self.port,
            "db": self.db,
            "max_connections": self.max_connections,
            "retry_on_timeout": self.retry_on_timeout,
            "health_check_interval": self.health_check_interval,
            "socket_timeout": self.socket_timeout,
            "socket_connect_timeout": self.socket_connect_timeout,
            "decode_responses": self.decode_responses,
        }

        if self.password:
            kwargs["password"] = self.password

        return kwargs


class FantasyRedisPool:
    """Redis connection pool manager for fantasy sports operations."""

    def __init__(self, config: FantasyRedisConfig | None = None):
        """
        Initialize Redis pool manager.

        Args:
            config: Redis configuration (uses default if None)
        """
        self.config = config or FantasyRedisConfig()
        self.pool: ConnectionPool | None = None
        self.redis_client: redis.Redis | None = None

        # Fantasy sports specific cache key prefixes
        self.key_prefixes = {
            "player": "fantasy:player:",
            "league": "fantasy:league:",
            "team": "fantasy:team:",
            "draft": "fantasy:draft:",
            "trade": "fantasy:trade:",
            "lineup": "fantasy:lineup:",
            "score": "fantasy:score:",
            "waiver": "fantasy:waiver:",
            "stats": "fantasy:stats:",
            "projection": "fantasy:projection:",
            "session": "fantasy:session:",
            "notification": "fantasy:notification:",
        }

        # Default TTL values for different data types (in seconds)
        self.default_ttl = {
            "player_stats": 300,  # 5 minutes
            "player_projection": 3600,  # 1 hour
            "league_settings": 1800,  # 30 minutes
            "team_roster": 600,  # 10 minutes
            "draft_state": 5,  # 5 seconds (real-time)
            "trade_status": 60,  # 1 minute
            "lineup": 300,  # 5 minutes
            "scores": 30,  # 30 seconds
            "waiver_priority": 1800,  # 30 minutes
            "user_session": 86400,  # 24 hours
            "notifications": 3600,  # 1 hour
        }

    async def initialize(self) -> None:
        """Initialize the Redis connection pool."""
        try:
            # Create connection pool
            connection_kwargs = self.config.get_connection_kwargs()
            self.pool = ConnectionPool(**connection_kwargs)

            # Create Redis client
            self.redis_client = redis.Redis(connection_pool=self.pool)

            # Test connection
            await self.redis_client.ping()
            logger.info(
                f"Redis connection pool initialized: {self.config.host}:{self.config.port}"
            )

        except RedisError as e:
            logger.error(f"Failed to initialize Redis pool: {e}")
            raise

    async def close(self) -> None:
        """Close the Redis connection pool."""
        if self.redis_client:
            await self.redis_client.close()
            logger.info("Redis connection pool closed")

    async def health_check(self) -> dict[str, Any]:
        """
        Perform health check on Redis connection.

        Returns:
            Health status information
        """
        try:
            if not self.redis_client:
                return {"status": "unhealthy", "error": "Redis client not initialized"}

            # Ping Redis
            start_time = datetime.utcnow()
            await self.redis_client.ping()
            response_time = (datetime.utcnow() - start_time).total_seconds() * 1000

            # Get Redis info
            info = await self.redis_client.info()

            return {
                "status": "healthy",
                "response_time_ms": response_time,
                "redis_version": info.get("redis_version"),
                "connected_clients": info.get("connected_clients"),
                "used_memory": info.get("used_memory_human"),
                "keyspace_hits": info.get("keyspace_hits"),
                "keyspace_misses": info.get("keyspace_misses"),
            }

        except Exception as e:
            return {"status": "unhealthy", "error": str(e)}

    def _build_key(self, prefix: str, identifier: str, suffix: str = "") -> str:
        """
        Build cache key with fantasy sports naming convention.

        Args:
            prefix: Key prefix type
            identifier: Unique identifier
            suffix: Optional suffix

        Returns:
            Formatted cache key
        """
        base_prefix = self.key_prefixes.get(prefix, f"fantasy:{prefix}:")
        key = f"{base_prefix}{identifier}"
        if suffix:
            key = f"{key}:{suffix}"
        return key

    async def get(self, prefix: str, identifier: str, suffix: str = "") -> Any | None:
        """
        Get value from cache.

        Args:
            prefix: Key prefix type
            identifier: Unique identifier
            suffix: Optional suffix

        Returns:
            Cached value or None
        """
        if not self.redis_client:
            return None

        try:
            key = self._build_key(prefix, identifier, suffix)
            value = await self.redis_client.get(key)

            if value:
                try:
                    return json.loads(value)
                except json.JSONDecodeError:
                    return value

            return None

        except RedisError as e:
            logger.error(f"Redis GET error for key {prefix}:{identifier}: {e}")
            return None

    async def set(
        self,
        prefix: str,
        identifier: str,
        value: Any,
        ttl: int | None = None,
        suffix: str = "",
    ) -> bool:
        """
        Set value in cache.

        Args:
            prefix: Key prefix type
            identifier: Unique identifier
            value: Value to cache
            ttl: Time to live in seconds
            suffix: Optional suffix

        Returns:
            True if successful, False otherwise
        """
        if not self.redis_client:
            return False

        try:
            key = self._build_key(prefix, identifier, suffix)

            # Serialize value if needed
            if isinstance(value, (dict, list)):
                value = json.dumps(value)

            # Use default TTL if not specified
            if ttl is None:
                ttl = self.default_ttl.get(prefix, 3600)

            await self.redis_client.setex(key, ttl, value)
            return True

        except RedisError as e:
            logger.error(f"Redis SET error for key {prefix}:{identifier}: {e}")
            return False

    async def delete(self, prefix: str, identifier: str, suffix: str = "") -> bool:
        """
        Delete value from cache.

        Args:
            prefix: Key prefix type
            identifier: Unique identifier
            suffix: Optional suffix

        Returns:
            True if successful, False otherwise
        """
        if not self.redis_client:
            return False

        try:
            key = self._build_key(prefix, identifier, suffix)
            result = await self.redis_client.delete(key)
            return result > 0

        except RedisError as e:
            logger.error(f"Redis DELETE error for key {prefix}:{identifier}: {e}")
            return False

    async def exists(self, prefix: str, identifier: str, suffix: str = "") -> bool:
        """
        Check if key exists in cache.

        Args:
            prefix: Key prefix type
            identifier: Unique identifier
            suffix: Optional suffix

        Returns:
            True if exists, False otherwise
        """
        if not self.redis_client:
            return False

        try:
            key = self._build_key(prefix, identifier, suffix)
            result = await self.redis_client.exists(key)
            return result > 0

        except RedisError as e:
            logger.error(f"Redis EXISTS error for key {prefix}:{identifier}: {e}")
            return False

    async def increment(
        self, prefix: str, identifier: str, amount: int = 1, suffix: str = ""
    ) -> int | None:
        """
        Increment counter in cache.

        Args:
            prefix: Key prefix type
            identifier: Unique identifier
            amount: Amount to increment
            suffix: Optional suffix

        Returns:
            New value or None on error
        """
        if not self.redis_client:
            return None

        try:
            key = self._build_key(prefix, identifier, suffix)
            result = await self.redis_client.incrby(key, amount)
            return result

        except RedisError as e:
            logger.error(f"Redis INCR error for key {prefix}:{identifier}: {e}")
            return None

    async def expire(
        self, prefix: str, identifier: str, ttl: int, suffix: str = ""
    ) -> bool:
        """
        Set expiration for existing key.

        Args:
            prefix: Key prefix type
            identifier: Unique identifier
            ttl: Time to live in seconds
            suffix: Optional suffix

        Returns:
            True if successful, False otherwise
        """
        if not self.redis_client:
            return False

        try:
            key = self._build_key(prefix, identifier, suffix)
            result = await self.redis_client.expire(key, ttl)
            return result

        except RedisError as e:
            logger.error(f"Redis EXPIRE error for key {prefix}:{identifier}: {e}")
            return False

    async def get_keys_by_pattern(self, pattern: str) -> list[str]:
        """
        Get keys matching pattern.

        Args:
            pattern: Key pattern

        Returns:
            List of matching keys
        """
        if not self.redis_client:
            return []

        try:
            keys = await self.redis_client.keys(pattern)
            return keys

        except RedisError as e:
            logger.error(f"Redis KEYS error for pattern {pattern}: {e}")
            return []

    async def clear_fantasy_cache(self, cache_type: str | None = None) -> int:
        """
        Clear fantasy sports cache data.

        Args:
            cache_type: Specific cache type to clear (optional)

        Returns:
            Number of keys deleted
        """
        if not self.redis_client:
            return 0

        try:
            if cache_type and cache_type in self.key_prefixes:
                pattern = f"{self.key_prefixes[cache_type]}*"
            else:
                pattern = "fantasy:*"

            keys = await self.get_keys_by_pattern(pattern)
            if keys:
                deleted = await self.redis_client.delete(*keys)
                logger.info(f"Cleared {deleted} cache keys with pattern: {pattern}")
                return deleted

            return 0

        except RedisError as e:
            logger.error(f"Error clearing fantasy cache: {e}")
            return 0


# Global Redis pool instance
_redis_pool: FantasyRedisPool | None = None


async def get_redis_pool() -> FantasyRedisPool:
    """
    Get the global Redis pool instance.

    Returns:
        Redis pool instance
    """
    global _redis_pool
    if _redis_pool is None:
        _redis_pool = FantasyRedisPool()
        await _redis_pool.initialize()
    return _redis_pool


async def close_redis_pool() -> None:
    """Close the global Redis pool."""
    global _redis_pool
    if _redis_pool:
        await _redis_pool.close()
        _redis_pool = None


@asynccontextmanager
async def redis_connection():
    """
    Context manager for Redis operations.

    Usage:
        async with redis_connection() as redis_pool:
            await redis_pool.set("player", "123", {"name": "John Doe"})
    """
    pool = await get_redis_pool()
    try:
        yield pool
    except Exception as e:
        logger.error(f"Redis operation error: {e}")
        raise


# Convenience functions for common fantasy sports caching patterns


async def cache_player_stats(
    player_id: str, stats: dict[str, Any], ttl: int = 300
) -> bool:
    """Cache player statistics with default TTL."""
    pool = await get_redis_pool()
    return await pool.set("player", player_id, stats, ttl, "stats")


async def get_player_stats(player_id: str) -> dict[str, Any] | None:
    """Get cached player statistics."""
    pool = await get_redis_pool()
    return await pool.get("player", player_id, "stats")


async def cache_league_settings(league_id: str, settings: dict[str, Any]) -> bool:
    """Cache league settings."""
    pool = await get_redis_pool()
    return await pool.set("league", league_id, settings, suffix="settings")


async def get_league_settings(league_id: str) -> dict[str, Any] | None:
    """Get cached league settings."""
    pool = await get_redis_pool()
    return await pool.get("league", league_id, "settings")


async def cache_draft_state(draft_id: str, state: dict[str, Any]) -> bool:
    """Cache draft state with short TTL for real-time updates."""
    pool = await get_redis_pool()
    return await pool.set("draft", draft_id, state, ttl=5, suffix="state")


async def get_draft_state(draft_id: str) -> dict[str, Any] | None:
    """Get cached draft state."""
    pool = await get_redis_pool()
    return await pool.get("draft", draft_id, "state")
