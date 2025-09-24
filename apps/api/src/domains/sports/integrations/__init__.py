"""
Sports API integrations package.

Provides concrete implementations for external sports data providers:
- ESPN API integration
- The Athletic API integration
- Sports data aggregation and normalization
- Rate limiting and error handling
"""

from .espn_provider import ESPNSportsProvider
from .athletic_provider import AthleticSportsProvider
from .api_client import SportsAPIClient, APIError, RateLimitError
from .data_normalizer import normalize_player_data, normalize_game_data, normalize_stats_data

__all__ = [
    "ESPNSportsProvider",
    "AthleticSportsProvider",
    "SportsAPIClient",
    "APIError",
    "RateLimitError",
    "normalize_player_data",
    "normalize_game_data",
    "normalize_stats_data"
]