"""
Sports API integrations package.

Provides concrete implementations for external sports data providers:
- ESPN API integration
- The Athletic API integration
- Sports data aggregation and normalization
- Rate limiting and error handling
"""

from .api_client import APIError, RateLimitError, SportsAPIClient
from .athletic_provider import AthleticSportsProvider
from .data_normalizer import (
    normalize_game_data,
    normalize_player_data,
    normalize_stats_data,
)
from .espn_provider import ESPNSportsProvider

__all__ = [
    "APIError",
    "AthleticSportsProvider",
    "ESPNSportsProvider",
    "RateLimitError",
    "SportsAPIClient",
    "normalize_game_data",
    "normalize_player_data",
    "normalize_stats_data",
]
