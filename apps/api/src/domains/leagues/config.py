"""League domain configuration."""

from typing import Dict, Any
from pydantic_settings import BaseSettings


class LeagueConfig(BaseSettings):
    """Configuration for the League domain."""

    # Domain-specific settings
    max_league_size: int = 12
    min_league_size: int = 4
    default_season_length: int = 17
    auto_advance_weeks: bool = True

    # Feature flags
    enable_league_branding: bool = True
    enable_custom_rules: bool = True
    enable_commissioner_tools: bool = True

    # Cache settings
    league_cache_ttl: int = 300  # 5 minutes
    member_cache_ttl: int = 600  # 10 minutes

    # Database settings
    league_db_pool_size: int = 5
    league_db_timeout: int = 30

    class Config:
        env_prefix = "LEAGUE_"
        case_sensitive = False


def get_league_config() -> LeagueConfig:
    """Get league domain configuration."""
    return LeagueConfig()


def get_league_feature_flags() -> Dict[str, bool]:
    """Get league domain feature flags."""
    config = get_league_config()
    return {
        "enable_league_branding": config.enable_league_branding,
        "enable_custom_rules": config.enable_custom_rules,
        "enable_commissioner_tools": config.enable_commissioner_tools,
    }


def get_league_limits() -> Dict[str, Any]:
    """Get league domain limits and constraints."""
    config = get_league_config()
    return {
        "max_league_size": config.max_league_size,
        "min_league_size": config.min_league_size,
        "default_season_length": config.default_season_length,
        "auto_advance_weeks": config.auto_advance_weeks,
    }