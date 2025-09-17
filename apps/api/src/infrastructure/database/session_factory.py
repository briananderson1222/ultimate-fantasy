"""
Database Session Factory for domain-specific database access.

This factory provides centralized database session management with
support for different domains and connection pooling.
"""
from __future__ import annotations

import os
from contextlib import asynccontextmanager
from typing import AsyncGenerator, Optional, Dict, Any
from sqlalchemy import create_engine, Engine, pool
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.ext.asyncio import create_async_engine, AsyncEngine, AsyncSession, async_sessionmaker

from domains.shared.models.base import Base


class SessionFactory:
    """Factory for creating and managing database sessions."""

    def __init__(
        self,
        database_url: str,
        echo: bool = False,
        pool_size: int = 5,
        max_overflow: int = 10,
        pool_timeout: int = 30,
        async_mode: bool = False
    ):
        """
        Initialize the session factory.

        Args:
            database_url: Database connection URL
            echo: Whether to echo SQL statements
            pool_size: Connection pool size
            max_overflow: Maximum overflow connections
            pool_timeout: Pool timeout in seconds
            async_mode: Whether to use async engine
        """
        self.database_url = database_url
        self.echo = echo
        self.pool_size = pool_size
        self.max_overflow = max_overflow
        self.pool_timeout = pool_timeout
        self.async_mode = async_mode

        # Initialize engines and session makers
        if async_mode:
            self._async_engine = self._create_async_engine()
            self._async_session_maker = async_sessionmaker(
                bind=self._async_engine,
                class_=AsyncSession,
                expire_on_commit=False
            )
            self._engine = None
            self._session_maker = None
        else:
            self._engine = self._create_sync_engine()
            self._session_maker = sessionmaker(
                bind=self._engine,
                expire_on_commit=False
            )
            self._async_engine = None
            self._async_session_maker = None

    def _create_sync_engine(self) -> Engine:
        """Create synchronous database engine."""
        return create_engine(
            self.database_url,
            echo=self.echo,
            poolclass=pool.QueuePool,
            pool_size=self.pool_size,
            max_overflow=self.max_overflow,
            pool_timeout=self.pool_timeout,
            pool_pre_ping=True,  # Validate connections before use
        )

    def _create_async_engine(self) -> AsyncEngine:
        """Create asynchronous database engine."""
        # Convert sync URL to async if needed
        async_url = self.database_url
        if async_url.startswith("postgresql://"):
            async_url = async_url.replace("postgresql://", "postgresql+asyncpg://", 1)
        elif async_url.startswith("sqlite:///"):
            async_url = async_url.replace("sqlite:///", "sqlite+aiosqlite:///", 1)

        return create_async_engine(
            async_url,
            echo=self.echo,
            pool_size=self.pool_size,
            max_overflow=self.max_overflow,
            pool_timeout=self.pool_timeout,
            pool_pre_ping=True,
        )

    @asynccontextmanager
    async def get_session(self) -> AsyncGenerator[Session, None]:
        """
        Get a database session.

        Returns:
            Database session context manager

        Raises:
            RuntimeError: If factory not properly initialized
        """
        if self.async_mode:
            if not self._async_session_maker:
                raise RuntimeError("Async session maker not initialized")

            async with self._async_session_maker() as session:
                try:
                    yield session
                    await session.commit()
                except Exception:
                    await session.rollback()
                    raise
        else:
            if not self._session_maker:
                raise RuntimeError("Sync session maker not initialized")

            with self._session_maker() as session:
                try:
                    yield session
                    session.commit()
                except Exception:
                    session.rollback()
                    raise

    def get_sync_session(self) -> Session:
        """
        Get a synchronous database session.

        Returns:
            Synchronous database session

        Raises:
            RuntimeError: If sync engine not available
        """
        if not self._session_maker:
            raise RuntimeError("Sync session maker not available")

        return self._session_maker()

    async def create_tables(self) -> None:
        """Create all database tables."""
        if self.async_mode and self._async_engine:
            async with self._async_engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
        elif self._engine:
            Base.metadata.create_all(self._engine)
        else:
            raise RuntimeError("No engine available for table creation")

    async def drop_tables(self) -> None:
        """Drop all database tables."""
        if self.async_mode and self._async_engine:
            async with self._async_engine.begin() as conn:
                await conn.run_sync(Base.metadata.drop_all)
        elif self._engine:
            Base.metadata.drop_all(self._engine)
        else:
            raise RuntimeError("No engine available for table dropping")

    async def health_check(self) -> Dict[str, Any]:
        """
        Perform health check on database connection.

        Returns:
            Health status information
        """
        try:
            async with self.get_session() as session:
                # Simple query to test connection
                if self.async_mode:
                    await session.execute("SELECT 1")
                else:
                    session.execute("SELECT 1")

            return {
                "status": "healthy",
                "database_url": self.database_url.split("@")[-1] if "@" in self.database_url else "hidden",
                "async_mode": self.async_mode,
                "pool_size": self.pool_size,
                "max_overflow": self.max_overflow,
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "database_url": self.database_url.split("@")[-1] if "@" in self.database_url else "hidden",
                "async_mode": self.async_mode,
            }

    async def close(self) -> None:
        """Close database connections and clean up resources."""
        if self._async_engine:
            await self._async_engine.dispose()
        if self._engine:
            self._engine.dispose()

    def get_engine_info(self) -> Dict[str, Any]:
        """
        Get information about the database engine.

        Returns:
            Engine configuration information
        """
        return {
            "database_url": self.database_url.split("@")[-1] if "@" in self.database_url else "hidden",
            "echo": self.echo,
            "pool_size": self.pool_size,
            "max_overflow": self.max_overflow,
            "pool_timeout": self.pool_timeout,
            "async_mode": self.async_mode,
        }


# Default session factory instance
_session_factory: Optional[SessionFactory] = None


def get_session_factory(database_url: Optional[str] = None) -> SessionFactory:
    """
    Get or create the global session factory.

    Args:
        database_url: Database URL. If None, uses environment variable or default.

    Returns:
        SessionFactory instance
    """
    global _session_factory

    if _session_factory is None:
        # Get database URL from environment or use default
        url = database_url or os.getenv(
            "DATABASE_URL",
            "sqlite:///./ultimate_fantasy.db"
        )

        # Determine if we should use async mode
        async_mode = os.getenv("DATABASE_ASYNC", "false").lower() == "true"

        # Get configuration from environment
        echo = os.getenv("DATABASE_ECHO", "false").lower() == "true"
        pool_size = int(os.getenv("DATABASE_POOL_SIZE", "5"))
        max_overflow = int(os.getenv("DATABASE_MAX_OVERFLOW", "10"))
        pool_timeout = int(os.getenv("DATABASE_POOL_TIMEOUT", "30"))

        _session_factory = SessionFactory(
            database_url=url,
            echo=echo,
            pool_size=pool_size,
            max_overflow=max_overflow,
            pool_timeout=pool_timeout,
            async_mode=async_mode,
        )

    return _session_factory


def reset_session_factory() -> None:
    """Reset the global session factory (useful for testing)."""
    global _session_factory
    _session_factory = None


# FastAPI dependency for database sessions
async def get_db_session() -> AsyncGenerator[Session, None]:
    """
    FastAPI dependency for database sessions.

    Usage:
        @app.get("/endpoint")
        async def endpoint(session: Session = Depends(get_db_session)):
            pass
    """
    factory = get_session_factory()
    async with factory.get_session() as session:
        yield session


# Domain-specific session factories (for future microservices)
class DomainSessionFactory:
    """Session factory for specific domains."""

    def __init__(self, domain_name: str, base_factory: SessionFactory):
        self.domain_name = domain_name
        self.base_factory = base_factory

    @asynccontextmanager
    async def get_session(self) -> AsyncGenerator[Session, None]:
        """Get a session for this domain."""
        async with self.base_factory.get_session() as session:
            # Add domain-specific session configuration here
            # For example, set schema, connection parameters, etc.
            yield session

    async def health_check(self) -> Dict[str, Any]:
        """Health check for domain-specific session factory."""
        base_health = await self.base_factory.health_check()
        return {
            **base_health,
            "domain": self.domain_name,
        }


def create_domain_factory(domain_name: str, database_url: Optional[str] = None) -> DomainSessionFactory:
    """
    Create a domain-specific session factory.

    Args:
        domain_name: Name of the domain
        database_url: Domain-specific database URL (optional)

    Returns:
        DomainSessionFactory instance
    """
    base_factory = get_session_factory(database_url)
    return DomainSessionFactory(domain_name, base_factory)