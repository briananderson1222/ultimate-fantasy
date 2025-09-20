"""Scoring domain configuration."""

from typing import Any

from pydantic_settings import BaseSettings


class ScoringConfig(BaseSettings):
    """Configuration for the Scoring domain."""

    # Scoring calculation
    scoring_update_interval_minutes: int = 15
    enable_real_time_scoring: bool = True
    enable_fractional_scoring: bool = True
    decimal_places: int = 2

    # Default scoring rules (can be overridden per league)
    default_passing_td: float = 4.0
    default_rushing_td: float = 6.0
    default_receiving_td: float = 6.0
    default_passing_yard_points: float = 0.04  # 1 point per 25 yards
    default_rushing_yard_points: float = 0.1  # 1 point per 10 yards
    default_receiving_yard_points: float = 0.1  # 1 point per 10 yards

    # Performance settings
    enable_stat_caching: bool = True
    batch_score_calculations: bool = True
    max_concurrent_calculations: int = 10

    # Feature flags
    enable_bonus_scoring: bool = True
    enable_negative_scoring: bool = True
    enable_position_limits: bool = True

    # Cache settings
    score_cache_ttl: int = 120  # 2 minutes
    stats_cache_ttl: int = 300  # 5 minutes

    # Database settings
    scoring_db_pool_size: int = 12
    scoring_db_timeout: int = 45

    class Config:
        env_prefix = "SCORING_"
        case_sensitive = False


def get_scoring_config() -> ScoringConfig:
    """Get scoring domain configuration."""
    return ScoringConfig()


def get_default_scoring_rules() -> dict[str, float]:
    """Get default scoring rules."""
    config = get_scoring_config()
    return {
        "passing_td": config.default_passing_td,
        "rushing_td": config.default_rushing_td,
        "receiving_td": config.default_receiving_td,
        "passing_yard_points": config.default_passing_yard_points,
        "rushing_yard_points": config.default_rushing_yard_points,
        "receiving_yard_points": config.default_receiving_yard_points,
    }


def get_scoring_performance_settings() -> dict[str, Any]:
    """Get scoring performance settings."""
    config = get_scoring_config()
    return {
        "scoring_update_interval_minutes": config.scoring_update_interval_minutes,
        "enable_real_time_scoring": config.enable_real_time_scoring,
        "batch_score_calculations": config.batch_score_calculations,
        "max_concurrent_calculations": config.max_concurrent_calculations,
        "enable_stat_caching": config.enable_stat_caching,
    }
