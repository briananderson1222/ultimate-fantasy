"""
Domain Service Registry for managing service instances and dependencies.

This registry provides centralized access to domain services and manages
their lifecycle and dependencies.
"""
from __future__ import annotations

from typing import Any, TypeVar

from sqlalchemy.orm import Session

from domains.leagues.services.league_service import LeagueService
from domains.lineups.services.lineup_service import LineupService
from domains.scoring.services.scoring_service import ScoringService
from domains.shared.interfaces.league_service import LeagueServiceInterface
from domains.shared.interfaces.lineup_service import LineupServiceInterface
from domains.shared.interfaces.scoring_service import ScoringServiceInterface
from domains.shared.interfaces.trading_service import TradingServiceInterface
from domains.shared.interfaces.user_service import UserServiceInterface
from domains.shared.interfaces.waitlist_service import WaitlistServiceInterface
from domains.trading.services.trading_service import TradingService
from domains.users.services.user_service import UserService
from domains.waitlist.services.waitlist_service import WaitlistService

T = TypeVar('T')


class ServiceRegistry:
    """Registry for managing domain service instances."""

    def __init__(self, db_session: Session):
        self.db_session = db_session
        self._services: dict[type, Any] = {}
        self._initialize_services()

    def _initialize_services(self) -> None:
        """Initialize all domain services with their dependencies."""
        # Initialize concrete service implementations
        self._services[LeagueServiceInterface] = LeagueService(self.db_session)
        self._services[UserServiceInterface] = UserService(self.db_session)
        self._services[LineupServiceInterface] = LineupService(self.db_session)
        self._services[TradingServiceInterface] = TradingService(self.db_session)
        self._services[ScoringServiceInterface] = ScoringService(self.db_session)
        self._services[WaitlistServiceInterface] = WaitlistService(self.db_session)

        # Also register by concrete class for backward compatibility
        self._services[LeagueService] = self._services[LeagueServiceInterface]
        self._services[UserService] = self._services[UserServiceInterface]
        self._services[LineupService] = self._services[LineupServiceInterface]
        self._services[TradingService] = self._services[TradingServiceInterface]
        self._services[ScoringService] = self._services[ScoringServiceInterface]
        self._services[WaitlistService] = self._services[WaitlistServiceInterface]

    def get_service(self, service_type: type[T]) -> T:
        """
        Get a service instance by its type.

        Args:
            service_type: The service interface or concrete class type

        Returns:
            Service instance

        Raises:
            KeyError: If service type is not registered
        """
        if service_type not in self._services:
            raise KeyError(f"Service {service_type.__name__} not registered")

        return self._services[service_type]

    def get_league_service(self) -> LeagueServiceInterface:
        """Get the league service instance."""
        return self.get_service(LeagueServiceInterface)

    def get_user_service(self) -> UserServiceInterface:
        """Get the user service instance."""
        return self.get_service(UserServiceInterface)

    def get_lineup_service(self) -> LineupServiceInterface:
        """Get the lineup service instance."""
        return self.get_service(LineupServiceInterface)

    def get_trading_service(self) -> TradingServiceInterface:
        """Get the trading service instance."""
        return self.get_service(TradingServiceInterface)

    def get_scoring_service(self) -> ScoringServiceInterface:
        """Get the scoring service instance."""
        return self.get_service(ScoringServiceInterface)

    def get_waitlist_service(self) -> WaitlistServiceInterface:
        """Get the waitlist service instance."""
        return self.get_service(WaitlistServiceInterface)

    def register_service(self, service_type: type[T], instance: T) -> None:
        """
        Register a custom service instance.

        Args:
            service_type: The service type to register
            instance: The service instance
        """
        self._services[service_type] = instance

    def list_services(self) -> dict[str, str]:
        """
        List all registered services.

        Returns:
            Dictionary mapping service names to their types
        """
        return {
            service_type.__name__: type(instance).__name__
            for service_type, instance in self._services.items()
        }

    def health_check(self) -> dict[str, str]:
        """
        Perform health check on all services.

        Returns:
            Dictionary with health status of each service
        """
        health_status = {}

        for service_type, instance in self._services.items():
            try:
                # Basic health check - ensure service is instantiated
                if instance is not None:
                    health_status[service_type.__name__] = "healthy"
                else:
                    health_status[service_type.__name__] = "unhealthy"
            except Exception as e:
                health_status[service_type.__name__] = f"error: {e!s}"

        return health_status


# Global registry instance (will be initialized by container)
_registry: ServiceRegistry | None = None


def get_registry() -> ServiceRegistry:
    """
    Get the global service registry instance.

    Returns:
        ServiceRegistry instance

    Raises:
        RuntimeError: If registry not initialized
    """
    global _registry
    if _registry is None:
        raise RuntimeError("Service registry not initialized. Call initialize_registry() first.")
    return _registry


def initialize_registry(db_session: Session) -> ServiceRegistry:
    """
    Initialize the global service registry.

    Args:
        db_session: Database session to use for services

    Returns:
        ServiceRegistry instance
    """
    global _registry
    _registry = ServiceRegistry(db_session)
    return _registry


def cleanup_registry() -> None:
    """Clean up the global service registry."""
    global _registry
    _registry = None
