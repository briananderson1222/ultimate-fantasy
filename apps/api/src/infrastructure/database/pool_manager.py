"""
Database connection pooling optimization.

Provides advanced database connection management with:
- Connection pooling with dynamic scaling
- Health monitoring and recovery
- Performance metrics and optimization
- Read/write splitting
- Connection lifecycle management
"""

import asyncio
import time
import logging
from typing import Optional, Dict, Any, List, Callable, AsyncContextManager
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from contextlib import asynccontextmanager
from enum import Enum

import sqlalchemy as sa
from sqlalchemy.ext.asyncio import (
    create_async_engine,
    AsyncEngine,
    AsyncSession,
    async_sessionmaker
)
from sqlalchemy.pool import StaticPool, QueuePool
from sqlalchemy.exc import SQLAlchemyError, DisconnectionError

try:
    from infrastructure.logging.domain_logger import get_logger
except ImportError:
    import logging
    get_logger = logging.getLogger

try:
    from infrastructure.observability.tracing import get_tracer, trace_fantasy_operation
except ImportError:
    class MockSpan:
        def set_attribute(self, key, value):
            pass

    class MockTracer:
        def span(self, name, **kwargs):
            return MockSpan()

    def get_tracer():
        return MockTracer()

    def trace_fantasy_operation(tracer, name, **kwargs):
        from contextlib import contextmanager

        @contextmanager
        def mock_trace():
            yield MockSpan()

        return mock_trace()

logger = get_logger(__name__)
tracer = get_tracer()


class PoolType(Enum):
    """Database pool types."""
    PRIMARY = "primary"
    REPLICA = "replica"
    ANALYTICS = "analytics"


class ConnectionState(Enum):
    """Connection states."""
    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"
    RECOVERING = "recovering"
    MAINTENANCE = "maintenance"


@dataclass
class PoolConfig:
    """Database pool configuration."""
    # Basic connection settings
    database_url: str
    pool_size: int = 10
    max_overflow: int = 20
    pool_timeout: int = 30
    pool_recycle: int = 3600
    pool_pre_ping: bool = True

    # Advanced settings
    echo: bool = False
    echo_pool: bool = False
    pool_reset_on_return: str = "commit"

    # Health check settings
    health_check_interval: int = 60
    max_connection_age: int = 7200
    connection_test_query: str = "SELECT 1"

    # Performance settings
    statement_timeout: int = 30
    idle_in_transaction_session_timeout: int = 300
    lock_timeout: int = 30000

    # Retry settings
    max_retries: int = 3
    retry_delay: float = 1.0
    exponential_backoff: bool = True


@dataclass
class PoolMetrics:
    """Pool performance metrics."""
    total_connections: int = 0
    active_connections: int = 0
    idle_connections: int = 0
    checked_out_connections: int = 0

    # Performance metrics
    avg_checkout_time: float = 0.0
    max_checkout_time: float = 0.0
    total_checkouts: int = 0
    failed_checkouts: int = 0

    # Health metrics
    healthy_connections: int = 0
    unhealthy_connections: int = 0
    last_health_check: Optional[datetime] = None

    # Query metrics
    total_queries: int = 0
    failed_queries: int = 0
    avg_query_time: float = 0.0
    slow_queries: int = 0


@dataclass
class ConnectionInfo:
    """Connection information."""
    connection_id: str
    created_at: datetime
    last_used: datetime
    state: ConnectionState = ConnectionState.HEALTHY
    query_count: int = 0
    error_count: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)


class DatabasePool:
    """Enhanced database connection pool with monitoring and optimization."""

    def __init__(self, config: PoolConfig, pool_type: PoolType = PoolType.PRIMARY):
        self.config = config
        self.pool_type = pool_type
        self.engine: Optional[AsyncEngine] = None
        self.session_factory: Optional[async_sessionmaker] = None

        self.metrics = PoolMetrics()
        self.connections: Dict[str, ConnectionInfo] = {}
        self._initialized = False
        self._health_check_task: Optional[asyncio.Task] = None
        self._cleanup_task: Optional[asyncio.Task] = None

        # Performance tracking
        self._checkout_times: List[float] = []
        self._query_times: List[float] = []

    async def initialize(self):
        """Initialize the database pool."""
        if self._initialized:
            return

        try:
            # Create engine with optimized settings
            engine_kwargs = {
                "url": self.config.database_url,
                "echo": self.config.echo,
                "echo_pool": self.config.echo_pool,
                "pool_size": self.config.pool_size,
                "max_overflow": self.config.max_overflow,
                "pool_timeout": self.config.pool_timeout,
                "pool_recycle": self.config.pool_recycle,
                "pool_pre_ping": self.config.pool_pre_ping,
                "pool_reset_on_return": self.config.pool_reset_on_return,
            }

            # Add PostgreSQL-specific optimizations
            if "postgresql" in self.config.database_url:
                engine_kwargs["connect_args"] = {
                    "statement_timeout": self.config.statement_timeout * 1000,  # Convert to ms
                    "idle_in_transaction_session_timeout": self.config.idle_in_transaction_session_timeout * 1000,
                    "lock_timeout": self.config.lock_timeout,
                    "application_name": f"ultimate-fantasy-{self.pool_type.value}",
                }

            # Use QueuePool for better performance
            if self.config.pool_size > 0:
                engine_kwargs["poolclass"] = QueuePool
            else:
                engine_kwargs["poolclass"] = StaticPool

            self.engine = create_async_engine(**engine_kwargs)

            # Create session factory
            self.session_factory = async_sessionmaker(
                bind=self.engine,
                class_=AsyncSession,
                expire_on_commit=False
            )

            # Start background tasks
            self._health_check_task = asyncio.create_task(self._health_check_loop())
            self._cleanup_task = asyncio.create_task(self._cleanup_loop())

            self._initialized = True
            logger.info(f"Database pool {self.pool_type.value} initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize database pool {self.pool_type.value}: {e}")
            raise

    async def close(self):
        """Close the database pool."""
        if not self._initialized:
            return

        # Cancel background tasks
        if self._health_check_task:
            self._health_check_task.cancel()
        if self._cleanup_task:
            self._cleanup_task.cancel()

        # Close engine
        if self.engine:
            await self.engine.dispose()
            self.engine = None

        self.session_factory = None
        self._initialized = False
        logger.info(f"Database pool {self.pool_type.value} closed")

    @asynccontextmanager
    async def get_session(self) -> AsyncContextManager[AsyncSession]:
        """
        Get database session with automatic cleanup and error handling.

        Yields:
            AsyncSession: Database session

        Raises:
            RuntimeError: If pool is not initialized
            SQLAlchemyError: If connection fails
        """
        if not self._initialized or not self.session_factory:
            raise RuntimeError(f"Database pool {self.pool_type.value} not initialized")

        checkout_start = time.time()
        session = None

        try:
            # Create session with retry logic
            session = await self._create_session_with_retry()

            # Track checkout time
            checkout_time = time.time() - checkout_start
            self._record_checkout_time(checkout_time)

            # Update metrics
            self.metrics.total_checkouts += 1
            self.metrics.checked_out_connections += 1

            with trace_fantasy_operation(
                tracer,
                f"db_session_{self.pool_type.value}",
                pool_type=self.pool_type.value
            ) as span:
                span.set_attribute("checkout_time", checkout_time)
                yield session

        except Exception as e:
            self.metrics.failed_checkouts += 1
            logger.error(f"Database session error in pool {self.pool_type.value}: {e}")

            if session:
                try:
                    await session.rollback()
                except Exception:
                    pass  # Ignore rollback errors

            raise

        finally:
            self.metrics.checked_out_connections -= 1

            if session:
                try:
                    await session.close()
                except Exception as e:
                    logger.warning(f"Error closing session: {e}")

    async def _create_session_with_retry(self) -> AsyncSession:
        """Create session with retry logic."""
        last_error = None

        for attempt in range(self.config.max_retries + 1):
            try:
                return self.session_factory()

            except (SQLAlchemyError, DisconnectionError) as e:
                last_error = e

                if attempt < self.config.max_retries:
                    delay = self.config.retry_delay
                    if self.config.exponential_backoff:
                        delay *= (2 ** attempt)

                    logger.warning(
                        f"Database connection attempt {attempt + 1} failed, "
                        f"retrying in {delay}s: {e}"
                    )
                    await asyncio.sleep(delay)
                else:
                    logger.error(f"All connection attempts failed: {e}")

        raise last_error

    async def execute_query(
        self,
        query: str,
        params: Optional[Dict[str, Any]] = None,
        session: Optional[AsyncSession] = None
    ) -> Any:
        """
        Execute query with performance tracking.

        Args:
            query: SQL query to execute
            params: Query parameters
            session: Optional existing session

        Returns:
            Query result
        """
        query_start = time.time()

        try:
            if session:
                # Use provided session
                result = await session.execute(sa.text(query), params or {})
            else:
                # Use managed session
                async with self.get_session() as session:
                    result = await session.execute(sa.text(query), params or {})

            # Track query performance
            query_time = time.time() - query_start
            self._record_query_time(query_time)

            self.metrics.total_queries += 1

            # Track slow queries (> 1 second)
            if query_time > 1.0:
                self.metrics.slow_queries += 1
                logger.warning(
                    f"Slow query detected ({query_time:.2f}s) in pool {self.pool_type.value}: "
                    f"{query[:100]}..."
                )

            return result

        except Exception as e:
            self.metrics.failed_queries += 1
            logger.error(f"Query failed in pool {self.pool_type.value}: {e}")
            raise

    async def health_check(self) -> bool:
        """
        Perform health check on the database pool.

        Returns:
            True if healthy, False otherwise
        """
        if not self._initialized:
            return False

        try:
            async with self.get_session() as session:
                await session.execute(sa.text(self.config.connection_test_query))

            self.metrics.last_health_check = datetime.utcnow()
            return True

        except Exception as e:
            logger.error(f"Health check failed for pool {self.pool_type.value}: {e}")
            return False

    async def _health_check_loop(self):
        """Background health check loop."""
        while True:
            try:
                await asyncio.sleep(self.config.health_check_interval)
                await self.health_check()
                await self._update_pool_metrics()

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Health check loop error: {e}")

    async def _cleanup_loop(self):
        """Background cleanup loop."""
        while True:
            try:
                await asyncio.sleep(300)  # Run every 5 minutes
                await self._cleanup_old_connections()
                self._cleanup_metrics()

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Cleanup loop error: {e}")

    async def _update_pool_metrics(self):
        """Update pool metrics."""
        if self.engine and hasattr(self.engine.pool, 'size'):
            pool = self.engine.pool
            self.metrics.total_connections = getattr(pool, 'size', 0)
            self.metrics.active_connections = getattr(pool, 'checked_out', 0)
            self.metrics.idle_connections = self.metrics.total_connections - self.metrics.active_connections

    async def _cleanup_old_connections(self):
        """Clean up old connections."""
        if not self.engine:
            return

        try:
            # Force pool cleanup
            await self.engine.pool.recreate()
            logger.debug(f"Pool cleanup completed for {self.pool_type.value}")

        except Exception as e:
            logger.error(f"Pool cleanup failed: {e}")

    def _cleanup_metrics(self):
        """Clean up old metrics data."""
        # Keep only last 1000 measurements
        if len(self._checkout_times) > 1000:
            self._checkout_times = self._checkout_times[-500:]

        if len(self._query_times) > 1000:
            self._query_times = self._query_times[-500:]

    def _record_checkout_time(self, checkout_time: float):
        """Record connection checkout time."""
        self._checkout_times.append(checkout_time)

        if self._checkout_times:
            self.metrics.avg_checkout_time = sum(self._checkout_times) / len(self._checkout_times)
            self.metrics.max_checkout_time = max(self._checkout_times)

    def _record_query_time(self, query_time: float):
        """Record query execution time."""
        self._query_times.append(query_time)

        if self._query_times:
            self.metrics.avg_query_time = sum(self._query_times) / len(self._query_times)

    def get_metrics(self) -> Dict[str, Any]:
        """Get current pool metrics."""
        return {
            "pool_type": self.pool_type.value,
            "total_connections": self.metrics.total_connections,
            "active_connections": self.metrics.active_connections,
            "idle_connections": self.metrics.idle_connections,
            "checked_out_connections": self.metrics.checked_out_connections,
            "avg_checkout_time": self.metrics.avg_checkout_time,
            "max_checkout_time": self.metrics.max_checkout_time,
            "total_checkouts": self.metrics.total_checkouts,
            "failed_checkouts": self.metrics.failed_checkouts,
            "total_queries": self.metrics.total_queries,
            "failed_queries": self.metrics.failed_queries,
            "avg_query_time": self.metrics.avg_query_time,
            "slow_queries": self.metrics.slow_queries,
            "last_health_check": self.metrics.last_health_check.isoformat() if self.metrics.last_health_check else None,
            "config": {
                "pool_size": self.config.pool_size,
                "max_overflow": self.config.max_overflow,
                "pool_timeout": self.config.pool_timeout,
                "pool_recycle": self.config.pool_recycle
            }
        }


class DatabasePoolManager:
    """
    Manager for multiple database pools with read/write splitting.
    """

    def __init__(self):
        self.pools: Dict[PoolType, DatabasePool] = {}
        self._initialized = False

    async def initialize(self, configs: Dict[PoolType, PoolConfig]):
        """
        Initialize database pools.

        Args:
            configs: Configuration for each pool type
        """
        for pool_type, config in configs.items():
            pool = DatabasePool(config, pool_type)
            await pool.initialize()
            self.pools[pool_type] = pool

        self._initialized = True
        logger.info(f"Database pool manager initialized with {len(self.pools)} pools")

    async def close(self):
        """Close all database pools."""
        for pool in self.pools.values():
            await pool.close()

        self.pools.clear()
        self._initialized = False
        logger.info("Database pool manager closed")

    def get_pool(self, pool_type: PoolType = PoolType.PRIMARY) -> DatabasePool:
        """
        Get database pool by type.

        Args:
            pool_type: Type of pool to retrieve

        Returns:
            DatabasePool instance

        Raises:
            ValueError: If pool type not found
        """
        if pool_type not in self.pools:
            raise ValueError(f"Pool type {pool_type.value} not configured")

        return self.pools[pool_type]

    @asynccontextmanager
    async def get_session(
        self,
        pool_type: PoolType = PoolType.PRIMARY,
        read_only: bool = False
    ) -> AsyncContextManager[AsyncSession]:
        """
        Get database session with automatic read/write routing.

        Args:
            pool_type: Preferred pool type
            read_only: Whether this is a read-only operation

        Yields:
            AsyncSession: Database session
        """
        # Route read-only queries to replica if available
        if read_only and PoolType.REPLICA in self.pools:
            pool_type = PoolType.REPLICA

        pool = self.get_pool(pool_type)
        async with pool.get_session() as session:
            yield session

    async def execute_query(
        self,
        query: str,
        params: Optional[Dict[str, Any]] = None,
        pool_type: PoolType = PoolType.PRIMARY,
        read_only: bool = False
    ) -> Any:
        """
        Execute query with automatic pool routing.

        Args:
            query: SQL query to execute
            params: Query parameters
            pool_type: Preferred pool type
            read_only: Whether this is a read-only operation

        Returns:
            Query result
        """
        async with self.get_session(pool_type, read_only) as session:
            pool = self.get_pool(pool_type if not read_only or PoolType.REPLICA not in self.pools else PoolType.REPLICA)
            return await pool.execute_query(query, params, session)

    async def health_check_all(self) -> Dict[str, bool]:
        """
        Perform health check on all pools.

        Returns:
            Dictionary mapping pool types to health status
        """
        results = {}

        for pool_type, pool in self.pools.items():
            results[pool_type.value] = await pool.health_check()

        return results

    def get_all_metrics(self) -> Dict[str, Any]:
        """Get metrics for all pools."""
        return {
            pool_type.value: pool.get_metrics()
            for pool_type, pool in self.pools.items()
        }


# Global pool manager instance
_pool_manager: Optional[DatabasePoolManager] = None


async def get_pool_manager() -> DatabasePoolManager:
    """Get global database pool manager."""
    global _pool_manager

    if _pool_manager is None:
        raise RuntimeError("Database pool manager not initialized")

    return _pool_manager


async def initialize_database_pools(configs: Dict[PoolType, PoolConfig]):
    """Initialize global database pool manager."""
    global _pool_manager

    _pool_manager = DatabasePoolManager()
    await _pool_manager.initialize(configs)


async def close_database_pools():
    """Close global database pool manager."""
    global _pool_manager

    if _pool_manager:
        await _pool_manager.close()
        _pool_manager = None