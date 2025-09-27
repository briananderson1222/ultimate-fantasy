"""
Database connection and session management for Ultimate Fantasy Platform
Provides SQLAlchemy engine, connection pooling, transaction management, and health checks
"""

import asyncio
import logging
import time
from collections.abc import Generator
from contextlib import contextmanager, suppress
from datetime import datetime
from typing import Any

import redis.asyncio as redis
from sqlalchemy import Engine, MetaData, create_engine, event, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session, scoped_session, sessionmaker
from sqlalchemy.pool import QueuePool

from ..config import settings

logger = logging.getLogger(__name__)


# SQLAlchemy Base for model definitions
Base = declarative_base()


class DatabaseConfig:
    """Database configuration settings"""

    def __init__(self):
        # Connection settings
        self.database_url = settings.DATABASE_URL
        self.echo_sql = settings.DEBUG
        self.pool_size = getattr(settings, "DB_POOL_SIZE", 20)
        self.max_overflow = getattr(settings, "DB_MAX_OVERFLOW", 30)
        self.pool_timeout = getattr(settings, "DB_POOL_TIMEOUT", 30)
        self.pool_recycle = getattr(settings, "DB_POOL_RECYCLE", 3600)  # 1 hour
        self.pool_pre_ping = getattr(settings, "DB_POOL_PRE_PING", True)

        # Transaction settings
        self.isolation_level = getattr(settings, "DB_ISOLATION_LEVEL", "READ_COMMITTED")
        self.autocommit = False
        self.autoflush = True

        # Health check settings
        self.health_check_interval = getattr(settings, "DB_HEALTH_CHECK_INTERVAL", 30)
        self.max_retries = getattr(settings, "DB_MAX_RETRIES", 3)
        self.retry_delay = getattr(settings, "DB_RETRY_DELAY", 1.0)


class DatabaseManager:
    """Manages database connections, sessions, and health monitoring"""

    def __init__(self, config: DatabaseConfig | None = None):
        """Initialize database manager with configuration"""
        self.config = config or DatabaseConfig()
        self.engine: Engine | None = None
        self.session_factory: sessionmaker | None = None
        self.scoped_session_factory: scoped_session | None = None

        # Health monitoring
        self.is_healthy = False
        self.last_health_check = None
        self.health_check_task: asyncio.Task | None = None
        self.connection_errors = 0
        self.total_connections = 0

        # Statistics
        self.stats = {
            "connections_created": 0,
            "connections_closed": 0,
            "transactions_committed": 0,
            "transactions_rolled_back": 0,
            "query_count": 0,
            "total_query_time": 0.0,
            "slow_queries": 0,
            "connection_errors": 0,
        }

        # Redis for distributed health status
        self.redis_client: redis.Redis | None = None

    async def initialize(self, redis_client: redis.Redis | None = None):
        """Initialize database engine and connection pool"""
        try:
            logger.info("Initializing database manager")

            self.redis_client = redis_client

            # Create SQLAlchemy engine with connection pooling
            self.engine = create_engine(
                self.config.database_url,
                poolclass=QueuePool,
                pool_size=self.config.pool_size,
                max_overflow=self.config.max_overflow,
                pool_timeout=self.config.pool_timeout,
                pool_recycle=self.config.pool_recycle,
                pool_pre_ping=self.config.pool_pre_ping,
                isolation_level=self.config.isolation_level,
                echo=self.config.echo_sql,
                future=True,
                # Performance optimizations
                connect_args=(
                    {
                        "connect_timeout": 10,
                        "application_name": "ultimate_fantasy_api",
                        "options": "-c timezone=UTC",
                    }
                    if "postgresql" in self.config.database_url
                    else {}
                ),
            )

            # Configure session factory
            self.session_factory = sessionmaker(
                bind=self.engine,
                autocommit=self.config.autocommit,
                autoflush=self.config.autoflush,
                expire_on_commit=False,
            )

            # Create scoped session for thread safety
            self.scoped_session_factory = scoped_session(self.session_factory)

            # Set up event listeners for monitoring
            self._setup_event_listeners()

            # Test initial connection
            await self._test_connection()

            # Start health monitoring
            if self.health_check_task is None:
                self.health_check_task = asyncio.create_task(self._health_monitor())

            self.is_healthy = True
            logger.info("Database manager initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize database manager: {e}")
            self.is_healthy = False
            raise

    async def shutdown(self):
        """Shutdown database manager and clean up resources"""
        logger.info("Shutting down database manager")

        try:
            # Cancel health monitoring
            if self.health_check_task:
                self.health_check_task.cancel()
                with suppress(asyncio.CancelledError):
                    await self.health_check_task

            # Close all sessions
            if self.scoped_session_factory:
                self.scoped_session_factory.remove()

            # Dispose of engine and connection pool
            if self.engine:
                self.engine.dispose()
                logger.info("Database engine disposed")

            self.is_healthy = False

        except Exception as e:
            logger.error(f"Error during database shutdown: {e}")

    def get_session(self) -> Session:
        """Get a new database session"""
        if not self.session_factory:
            raise RuntimeError("Database manager not initialized")

        return self.session_factory()

    def get_scoped_session(self) -> scoped_session:
        """Get a scoped session (thread-safe)"""
        if not self.scoped_session_factory:
            raise RuntimeError("Database manager not initialized")

        return self.scoped_session_factory()

    @contextmanager
    def session_scope(self) -> Generator[Session, None, None]:
        """
        Provide a transactional scope around a series of operations

        Usage:
            with db_manager.session_scope() as session:
                # Database operations
                session.add(obj)
                # Automatically commits on success, rolls back on exception
        """
        session = self.get_session()
        try:
            yield session
            session.commit()
            self.stats["transactions_committed"] += 1
        except Exception as e:
            session.rollback()
            self.stats["transactions_rolled_back"] += 1
            logger.error(f"Database transaction rolled back: {e}")
            raise
        finally:
            session.close()

    async def execute_query(
        self,
        query: str,
        params: dict[str, Any] | None = None,
        fetch_results: bool = True,
    ) -> Any | None:
        """
        Execute a raw SQL query with optional parameters

        Args:
            query: SQL query string
            params: Query parameters
            fetch_results: Whether to fetch and return results

        Returns:
            Query results if fetch_results=True, None otherwise
        """
        start_time = time.time()

        with self.session_scope() as session:
            try:
                result = session.execute(text(query), params or {})

                if fetch_results:
                    if result.returns_rows:
                        return result.fetchall()
                    else:
                        return result.rowcount

                return None

            finally:
                # Track query performance
                execution_time = time.time() - start_time
                self.stats["query_count"] += 1
                self.stats["total_query_time"] += execution_time

                # Log slow queries
                if execution_time > 1.0:  # Queries taking more than 1 second
                    self.stats["slow_queries"] += 1
                    logger.warning(
                        f"Slow query detected: {execution_time:.2f}s - {query[:100]}..."
                    )

    async def health_check(self) -> dict[str, Any]:
        """
        Comprehensive database health check

        Returns:
            Health status dictionary with metrics
        """
        health_status = {
            "healthy": False,
            "timestamp": datetime.utcnow().isoformat(),
            "checks": {},
        }

        try:
            # Basic connectivity test
            start_time = time.time()
            with self.session_scope() as session:
                result = session.execute(text("SELECT 1"))
                result.fetchone()

            connection_time = time.time() - start_time
            health_status["checks"]["connectivity"] = {
                "status": "healthy",
                "response_time_ms": round(connection_time * 1000, 2),
            }

            # Pool status
            if self.engine and hasattr(self.engine.pool, "size"):
                pool_status = {
                    "size": self.engine.pool.size(),
                    "checked_in": self.engine.pool.checkedin(),
                    "checked_out": self.engine.pool.checkedout(),
                    "invalid": self.engine.pool.invalid(),
                    "overflow": getattr(self.engine.pool, "_overflow", 0),
                }
                health_status["checks"]["connection_pool"] = {
                    "status": "healthy",
                    "metrics": pool_status,
                }

            # Database version and configuration
            with self.session_scope() as session:
                if "postgresql" in self.config.database_url:
                    version_result = session.execute(text("SELECT version()"))
                    version = version_result.fetchone()[0]

                    settings_result = session.execute(
                        text(
                            """
                        SELECT name, setting, unit
                        FROM pg_settings
                        WHERE name IN ('max_connections', 'shared_buffers', 'work_mem')
                    """
                        )
                    )
                    db_settings = {
                        row[0]: f"{row[1]} {row[2] or ''}".strip()
                        for row in settings_result.fetchall()
                    }

                    health_status["checks"]["database_info"] = {
                        "status": "healthy",
                        "version": version.split()[0:2],
                        "settings": db_settings,
                    }

            # Performance metrics
            health_status["checks"]["performance"] = {
                "status": "healthy",
                "metrics": {
                    "total_connections": self.total_connections,
                    "connection_errors": self.connection_errors,
                    "avg_query_time_ms": round(
                        (
                            self.stats["total_query_time"]
                            / max(self.stats["query_count"], 1)
                        )
                        * 1000,
                        2,
                    ),
                    "slow_queries": self.stats["slow_queries"],
                    "transactions_committed": self.stats["transactions_committed"],
                    "transactions_rolled_back": self.stats["transactions_rolled_back"],
                },
            }

            # Overall health assessment
            failed_checks = sum(
                1
                for check in health_status["checks"].values()
                if check["status"] != "healthy"
            )

            if failed_checks == 0:
                health_status["healthy"] = True
                health_status["status"] = "healthy"
            elif failed_checks <= 1:
                health_status["healthy"] = True
                health_status["status"] = "degraded"
            else:
                health_status["healthy"] = False
                health_status["status"] = "unhealthy"

            self.last_health_check = datetime.utcnow()

        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            health_status["healthy"] = False
            health_status["status"] = "unhealthy"
            health_status["error"] = str(e)
            self.connection_errors += 1

        return health_status

    async def create_tables(self, metadata: MetaData | None = None):
        """Create all database tables"""
        try:
            target_metadata = metadata or Base.metadata

            with self.session_scope() as session:
                target_metadata.create_all(bind=session.bind)
                logger.info("Database tables created successfully")

        except Exception as e:
            logger.error(f"Failed to create database tables: {e}")
            raise

    async def drop_tables(self, metadata: MetaData | None = None):
        """Drop all database tables (use with caution!)"""
        try:
            target_metadata = metadata or Base.metadata

            with self.session_scope() as session:
                target_metadata.drop_all(bind=session.bind)
                logger.warning("Database tables dropped")

        except Exception as e:
            logger.error(f"Failed to drop database tables: {e}")
            raise

    def get_stats(self) -> dict[str, Any]:
        """Get database manager statistics"""
        return {
            "healthy": self.is_healthy,
            "last_health_check": (
                self.last_health_check.isoformat() if self.last_health_check else None
            ),
            "total_connections": self.total_connections,
            "connection_errors": self.connection_errors,
            "stats": self.stats.copy(),
            "config": {
                "pool_size": self.config.pool_size,
                "max_overflow": self.config.max_overflow,
                "pool_timeout": self.config.pool_timeout,
                "pool_recycle": self.config.pool_recycle,
            },
        }

    # Private methods

    def _setup_event_listeners(self):
        """Set up SQLAlchemy event listeners for monitoring"""

        @event.listens_for(self.engine, "connect")
        def on_connect(dbapi_connection, connection_record):
            """Called when a new connection is created"""
            self.stats["connections_created"] += 1
            self.total_connections += 1
            logger.debug("Database connection created")

        @event.listens_for(self.engine, "checkout")
        def on_checkout(dbapi_connection, connection_record, connection_proxy):
            """Called when a connection is checked out from the pool"""
            connection_record.info["checkout_time"] = time.time()

        @event.listens_for(self.engine, "checkin")
        def on_checkin(dbapi_connection, connection_record):
            """Called when a connection is checked back into the pool"""
            if "checkout_time" in connection_record.info:
                checkout_time = connection_record.info.pop("checkout_time")
                usage_time = time.time() - checkout_time
                if usage_time > 10.0:  # Log long-running connections
                    logger.warning(
                        f"Long-running database connection: {usage_time:.2f}s"
                    )

        @event.listens_for(self.engine, "close")
        def on_close(dbapi_connection, connection_record):
            """Called when a connection is closed"""
            self.stats["connections_closed"] += 1
            logger.debug("Database connection closed")

        @event.listens_for(self.engine, "close_detached")
        def on_close_detached(dbapi_connection):
            """Called when a connection is closed outside the pool"""
            self.stats["connections_closed"] += 1

        # Listen for connection errors
        @event.listens_for(self.engine.pool, "connect")
        def on_pool_connect(dbapi_connection, connection_record):
            """Set up connection-level settings"""
            if "postgresql" in self.config.database_url:
                # Set PostgreSQL-specific settings
                with dbapi_connection.cursor() as cursor:
                    cursor.execute("SET timezone TO 'UTC'")
                    cursor.execute("SET statement_timeout TO '30s'")
                    cursor.execute("SET lock_timeout TO '10s'")

    async def _test_connection(self):
        """Test initial database connection"""
        try:
            with self.session_scope() as session:
                result = session.execute(text("SELECT 1"))
                result.fetchone()
            logger.info("Database connection test successful")
        except Exception as e:
            logger.error(f"Database connection test failed: {e}")
            raise

    async def _health_monitor(self):
        """Background task for continuous health monitoring"""
        while True:
            try:
                await asyncio.sleep(self.config.health_check_interval)

                health_status = await self.health_check()
                self.is_healthy = health_status["healthy"]

                # Publish health status to Redis if available
                if self.redis_client:
                    try:
                        await self.redis_client.set(
                            "db_health_status",
                            str(health_status),
                            ex=self.config.health_check_interval * 2,
                        )
                    except Exception as e:
                        logger.warning(f"Failed to publish health status to Redis: {e}")

                # Log health status changes
                if not self.is_healthy:
                    logger.warning(f"Database health check failed: {health_status}")

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in database health monitor: {e}")
                self.is_healthy = False


# Global database manager instance
db_manager = DatabaseManager()


# Convenience functions for backward compatibility
def get_db_session() -> Session:
    """Get a new database session"""
    return db_manager.get_session()


@contextmanager
def get_db_session_scope() -> Generator[Session, None, None]:
    """Get a transactional database session scope"""
    with db_manager.session_scope() as session:
        yield session


def get_scoped_session() -> scoped_session:
    """Get a scoped session"""
    return db_manager.get_scoped_session()


# Migration utilities
class MigrationManager:
    """Handles database migrations and schema changes"""

    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager

    async def check_migration_status(self) -> dict[str, Any]:
        """Check current migration status"""
        try:
            with self.db_manager.session_scope() as session:
                # Check if migration table exists
                result = session.execute(
                    text(
                        """
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables
                        WHERE table_name = 'alembic_version'
                    )
                """
                    )
                )

                has_migration_table = result.fetchone()[0]

                if has_migration_table:
                    # Get current migration version
                    version_result = session.execute(
                        text("SELECT version_num FROM alembic_version")
                    )
                    current_version = version_result.fetchone()
                    current_version = current_version[0] if current_version else None
                else:
                    current_version = None

                return {
                    "has_migration_table": has_migration_table,
                    "current_version": current_version,
                    "status": "ready" if current_version else "needs_init",
                }

        except Exception as e:
            logger.error(f"Failed to check migration status: {e}")
            return {
                "has_migration_table": False,
                "current_version": None,
                "status": "error",
                "error": str(e),
            }

    async def run_health_diagnostics(self) -> dict[str, Any]:
        """Run comprehensive database diagnostics"""
        diagnostics = {"timestamp": datetime.utcnow().isoformat(), "tests": {}}

        try:
            # Test basic connectivity
            start_time = time.time()
            with self.db_manager.session_scope() as session:
                session.execute(text("SELECT 1"))
            diagnostics["tests"]["connectivity"] = {
                "status": "pass",
                "response_time_ms": round((time.time() - start_time) * 1000, 2),
            }

            # Test transaction handling
            try:
                with self.db_manager.session_scope() as session:
                    session.execute(text("BEGIN"))
                    session.execute(text("SELECT 1"))
                    session.execute(text("ROLLBACK"))
                diagnostics["tests"]["transactions"] = {"status": "pass"}
            except Exception as e:
                diagnostics["tests"]["transactions"] = {
                    "status": "fail",
                    "error": str(e),
                }

            # Test connection pooling
            pool_info = {}
            if self.db_manager.engine and hasattr(self.db_manager.engine.pool, "size"):
                pool = self.db_manager.engine.pool
                pool_info = {
                    "size": pool.size(),
                    "checked_in": pool.checkedin(),
                    "checked_out": pool.checkedout(),
                    "overflow": getattr(pool, "_overflow", 0),
                }
            diagnostics["tests"]["connection_pool"] = {
                "status": "pass",
                "info": pool_info,
            }

            # Overall status
            failed_tests = sum(
                1
                for test in diagnostics["tests"].values()
                if test.get("status") != "pass"
            )
            diagnostics["overall_status"] = "pass" if failed_tests == 0 else "fail"
            diagnostics["failed_tests"] = failed_tests

        except Exception as e:
            logger.error(f"Database diagnostics failed: {e}")
            diagnostics["overall_status"] = "error"
            diagnostics["error"] = str(e)

        return diagnostics


# Create migration manager instance
migration_manager = MigrationManager(db_manager)
