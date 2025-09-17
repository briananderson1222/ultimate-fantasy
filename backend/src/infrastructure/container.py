"""
Dependency Injection Container for the Ultimate Fantasy backend.

This container manages the lifecycle and injection of dependencies
throughout the application, following the Dependency Inversion Principle.
"""
from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager
from typing import AsyncGenerator, Dict, Any, Optional, Callable, TypeVar, Type
from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession

from src.infrastructure.service_registry import ServiceRegistry, initialize_registry, cleanup_registry
from src.infrastructure.database.session_factory import SessionFactory, get_session_factory

T = TypeVar('T')


class Container:
    """Dependency injection container for managing application services."""

    def __init__(self):
        self._session_factory: Optional[SessionFactory] = None
        self._service_registry: Optional[ServiceRegistry] = None
        self._singletons: Dict[Type, Any] = {}
        self._factories: Dict[Type, Callable] = {}

    async def initialize(self, database_url: Optional[str] = None) -> None:
        """
        Initialize the container with necessary dependencies.

        Args:
            database_url: Database connection URL. If None, uses default from config.
        """
        # Initialize session factory
        self._session_factory = get_session_factory(database_url)

        # Initialize service registry with a session
        async with self.get_db_session() as session:
            self._service_registry = initialize_registry(session)

    async def cleanup(self) -> None:
        """Clean up container resources."""
        cleanup_registry()
        if self._session_factory:
            await self._session_factory.close()
        self._singletons.clear()
        self._factories.clear()

    @asynccontextmanager
    async def get_db_session(self) -> AsyncGenerator[Session, None]:
        """
        Get a database session.

        Returns:
            Database session context manager

        Raises:
            RuntimeError: If container not initialized
        """
        if not self._session_factory:
            raise RuntimeError("Container not initialized. Call initialize() first.")

        async with self._session_factory.get_session() as session:
            yield session

    def get_service_registry(self) -> ServiceRegistry:
        """
        Get the service registry.

        Returns:
            ServiceRegistry instance

        Raises:
            RuntimeError: If container not initialized
        """
        if not self._service_registry:
            raise RuntimeError("Container not initialized. Call initialize() first.")
        return self._service_registry

    def register_singleton(self, service_type: Type[T], instance: T) -> None:
        """
        Register a singleton instance.

        Args:
            service_type: The service type
            instance: The singleton instance
        """
        self._singletons[service_type] = instance

    def register_factory(self, service_type: Type[T], factory: Callable[[], T]) -> None:
        """
        Register a factory function for creating instances.

        Args:
            service_type: The service type
            factory: Factory function to create instances
        """
        self._factories[service_type] = factory

    def get_instance(self, service_type: Type[T]) -> T:
        """
        Get an instance of the specified service type.

        Args:
            service_type: The service type to get

        Returns:
            Service instance

        Raises:
            KeyError: If service type not found
        """
        # Check singletons first
        if service_type in self._singletons:
            return self._singletons[service_type]

        # Check factories
        if service_type in self._factories:
            return self._factories[service_type]()

        # Try to get from service registry
        if self._service_registry:
            try:
                return self._service_registry.get_service(service_type)
            except KeyError:
                pass

        raise KeyError(f"Service {service_type.__name__} not registered in container")

    async def health_check(self) -> Dict[str, Any]:
        """
        Perform health check on container and its services.

        Returns:
            Health status information
        """
        health = {
            "container": "healthy",
            "session_factory": "healthy" if self._session_factory else "not_initialized",
            "service_registry": "healthy" if self._service_registry else "not_initialized",
            "services": {}
        }

        # Check service registry health
        if self._service_registry:
            try:
                health["services"] = self._service_registry.health_check()
            except Exception as e:
                health["services"] = {"error": str(e)}

        # Check database connectivity
        try:
            if self._session_factory:
                async with self.get_db_session() as session:
                    # Simple query to test connection
                    await session.execute("SELECT 1")
                health["database"] = "healthy"
            else:
                health["database"] = "not_initialized"
        except Exception as e:
            health["database"] = f"error: {str(e)}"

        return health

    def get_configuration(self) -> Dict[str, Any]:
        """
        Get container configuration information.

        Returns:
            Configuration details
        """
        return {
            "singletons": list(self._singletons.keys()),
            "factories": list(self._factories.keys()),
            "session_factory_initialized": self._session_factory is not None,
            "service_registry_initialized": self._service_registry is not None,
        }


# Global container instance
_container: Optional[Container] = None


async def get_container() -> Container:
    """
    Get the global container instance.

    Returns:
        Container instance

    Raises:
        RuntimeError: If container not initialized
    """
    global _container
    if _container is None:
        raise RuntimeError("Container not initialized. Call initialize_container() first.")
    return _container


async def initialize_container(database_url: Optional[str] = None) -> Container:
    """
    Initialize the global container.

    Args:
        database_url: Database connection URL

    Returns:
        Container instance
    """
    global _container
    _container = Container()
    await _container.initialize(database_url)
    return _container


async def cleanup_container() -> None:
    """Clean up the global container."""
    global _container
    if _container:
        await _container.cleanup()
    _container = None


@asynccontextmanager
async def container_lifespan() -> AsyncGenerator[Container, None]:
    """
    Context manager for container lifecycle.

    Usage:
        async with container_lifespan() as container:
            # Use container
            pass
    """
    container = await initialize_container()
    try:
        yield container
    finally:
        await cleanup_container()


# Dependency injection helpers for FastAPI
async def get_db_session() -> AsyncGenerator[Session, None]:
    """
    FastAPI dependency for database sessions.

    Usage:
        @app.get("/endpoint")
        async def endpoint(session: Session = Depends(get_db_session)):
            pass
    """
    container = await get_container()
    async with container.get_db_session() as session:
        yield session


async def get_service_registry() -> ServiceRegistry:
    """
    FastAPI dependency for service registry.

    Usage:
        @app.get("/endpoint")
        async def endpoint(registry: ServiceRegistry = Depends(get_service_registry)):
            pass
    """
    container = await get_container()
    return container.get_service_registry()