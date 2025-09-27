"""
Sports data provider factory.

Creates and configures sports data providers based on configuration.
"""

import logging
import os

from domains.shared.enums import DataProvider
from domains.sports.services.sports_data_service import (
    MockSportsDataProvider,
    SportsDataProvider,
)

from .athletic_provider import AthleticSportsProvider
from .espn_provider import ESPNSportsProvider

logger = logging.getLogger(__name__)


class ProviderFactory:
    """Factory for creating sports data providers."""

    @staticmethod
    def create_provider(provider: DataProvider, **kwargs) -> SportsDataProvider:
        """
        Create a sports data provider instance.

        Args:
            provider: Provider type
            **kwargs: Provider-specific configuration

        Returns:
            SportsDataProvider instance

        Raises:
            ValueError: If provider is not supported
        """
        if provider == DataProvider.ESPN:
            api_key = kwargs.get("api_key") or os.getenv("ESPN_API_KEY")
            return ESPNSportsProvider(api_key=api_key)

        elif provider == DataProvider.THE_ATHLETIC:
            api_key = kwargs.get("api_key") or os.getenv("ATHLETIC_API_KEY")
            if not api_key:
                logger.warning(
                    "The Athletic API key not provided, falling back to mock provider"
                )
                return MockSportsDataProvider()
            return AthleticSportsProvider(api_key=api_key)

        elif provider == DataProvider.MOCK:
            return MockSportsDataProvider()

        else:
            raise ValueError(f"Unsupported provider: {provider}")

    @staticmethod
    def create_providers(
        primary_provider: DataProvider = DataProvider.ESPN,
        fallback_providers: list[DataProvider] | None = None,
        **provider_configs,
    ) -> list[SportsDataProvider]:
        """
        Create a list of providers with primary and fallbacks.

        Args:
            primary_provider: Primary provider
            fallback_providers: List of fallback providers
            **provider_configs: Provider-specific configurations

        Returns:
            List of SportsDataProvider instances
        """
        if fallback_providers is None:
            fallback_providers = [DataProvider.THE_ATHLETIC, DataProvider.MOCK]

        providers = []

        # Create primary provider
        try:
            config = provider_configs.get(primary_provider.value, {})
            primary = ProviderFactory.create_provider(primary_provider, **config)
            providers.append(primary)
            logger.info(f"Created primary provider: {primary_provider.value}")
        except Exception as e:
            logger.error(
                f"Failed to create primary provider {primary_provider.value}: {e}"
            )

        # Create fallback providers
        for fallback in fallback_providers:
            if fallback == primary_provider:
                continue  # Skip if same as primary

            try:
                config = provider_configs.get(fallback.value, {})
                fallback_provider = ProviderFactory.create_provider(fallback, **config)
                providers.append(fallback_provider)
                logger.info(f"Created fallback provider: {fallback.value}")
            except Exception as e:
                logger.warning(
                    f"Failed to create fallback provider {fallback.value}: {e}"
                )

        # Ensure we always have at least the mock provider
        if not providers:
            logger.warning("No providers created, falling back to mock provider")
            providers.append(MockSportsDataProvider())

        return providers

    @staticmethod
    def get_available_providers() -> list[DataProvider]:
        """
        Get list of available providers based on environment configuration.

        Returns:
            List of available DataProvider enums
        """
        available = [DataProvider.MOCK]  # Mock is always available

        # Check ESPN availability (no API key required for public endpoints)
        available.append(DataProvider.ESPN)

        # Check The Athletic availability
        if os.getenv("ATHLETIC_API_KEY"):
            available.append(DataProvider.THE_ATHLETIC)

        return available

    @staticmethod
    def validate_provider_config(provider: DataProvider, config: dict) -> bool:
        """
        Validate provider configuration.

        Args:
            provider: Provider type
            config: Configuration dictionary

        Returns:
            True if configuration is valid
        """
        if provider == DataProvider.ESPN:
            # ESPN public API doesn't require API key for basic endpoints
            return True

        elif provider == DataProvider.THE_ATHLETIC:
            # The Athletic requires API key
            return "api_key" in config and config["api_key"]

        elif provider == DataProvider.MOCK:
            # Mock provider has no requirements
            return True

        else:
            return False

    @staticmethod
    async def health_check_providers(providers: list[SportsDataProvider]) -> dict:
        """
        Check health status of all providers.

        Args:
            providers: List of providers to check

        Returns:
            Dictionary with provider health status
        """
        health_status = {}

        for i, provider in enumerate(providers):
            provider_name = f"provider_{i}"

            try:
                if hasattr(provider, "client") and provider.client:
                    await provider.client.health_check()
                    health_status[provider_name] = "healthy"
                else:
                    # For providers without client (like mock), assume healthy
                    health_status[provider_name] = "healthy"
            except Exception as e:
                logger.warning(f"Provider {provider_name} health check failed: {e}")
                health_status[provider_name] = "unhealthy"

        return health_status


def configure_sports_providers(
    primary_provider: str | None = None,
    athletic_api_key: str | None = None,
    espn_api_key: str | None = None,
) -> list[SportsDataProvider]:
    """
    Configure sports data providers based on environment and parameters.

    Args:
        primary_provider: Primary provider name (espn, athletic, mock)
        athletic_api_key: The Athletic API key
        espn_api_key: ESPN API key (optional)

    Returns:
        List of configured providers
    """
    # Determine primary provider
    if primary_provider:
        primary = DataProvider(primary_provider.upper())
    # Auto-detect based on available configuration
    elif athletic_api_key or os.getenv("ATHLETIC_API_KEY"):
        primary = DataProvider.THE_ATHLETIC
    else:
        primary = DataProvider.ESPN

    # Configure provider-specific settings
    provider_configs = {}

    if espn_api_key or os.getenv("ESPN_API_KEY"):
        provider_configs["espn"] = {
            "api_key": espn_api_key or os.getenv("ESPN_API_KEY")
        }

    if athletic_api_key or os.getenv("ATHLETIC_API_KEY"):
        provider_configs["athletic"] = {
            "api_key": athletic_api_key or os.getenv("ATHLETIC_API_KEY")
        }

    # Create providers
    providers = ProviderFactory.create_providers(
        primary_provider=primary, **provider_configs
    )

    logger.info(f"Configured {len(providers)} sports data providers")
    return providers
