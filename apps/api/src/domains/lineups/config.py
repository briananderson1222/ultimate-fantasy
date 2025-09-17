"""Lineup domain configuration."""

from typing import Any

from pydantic_settings import BaseSettings


class LineupConfig(BaseSettings):
    """Configuration for the Lineup domain."""

    # Lineup constraints
    max_players_per_lineup: int = 9
    min_players_per_lineup: int = 7
    roster_positions: list[str] = [
        "QB", "RB", "WR", "TE", "FLEX", "K", "DEF"
    ]

    # Deadline settings
    lineup_lock_hours_before: int = 1
    allow_late_substitutions: bool = False
    auto_fill_empty_slots: bool = True

    # Feature flags
    enable_bench_players: bool = True
    enable_lineup_optimizer: bool = False
    enable_injury_notifications: bool = True

    # Cache settings
    lineup_cache_ttl: int = 180  # 3 minutes
    player_status_cache_ttl: int = 60  # 1 minute

    # Database settings
    lineup_db_pool_size: int = 8
    lineup_db_timeout: int = 25

    class Config:
        env_prefix = "LINEUP_"
        case_sensitive = False


def get_lineup_config() -> LineupConfig:
    """Get lineup domain configuration."""
    return LineupConfig()


def get_lineup_constraints() -> dict[str, Any]:
    """Get lineup domain constraints."""
    config = get_lineup_config()
    return {
        "max_players_per_lineup": config.max_players_per_lineup,
        "min_players_per_lineup": config.min_players_per_lineup,
        "roster_positions": config.roster_positions,
        "lineup_lock_hours_before": config.lineup_lock_hours_before,
    }


def get_lineup_features() -> dict[str, bool]:
    """Get lineup domain feature flags."""
    config = get_lineup_config()
    return {
        "enable_bench_players": config.enable_bench_players,
        "enable_lineup_optimizer": config.enable_lineup_optimizer,
        "enable_injury_notifications": config.enable_injury_notifications,
        "allow_late_substitutions": config.allow_late_substitutions,
        "auto_fill_empty_slots": config.auto_fill_empty_slots,
    }
