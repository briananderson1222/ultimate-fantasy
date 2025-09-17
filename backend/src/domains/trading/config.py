"""Trading domain configuration."""

from typing import Dict, Any
from pydantic_settings import BaseSettings


class TradingConfig(BaseSettings):
    """Configuration for the Trading domain."""

    # Waiver settings
    waiver_period_hours: int = 48
    waiver_priority_type: str = "rolling"  # rolling, inverse_standings, faab
    max_waiver_claims_per_week: int = 5

    # Trade settings
    trade_review_period_hours: int = 24
    require_commissioner_approval: bool = False
    enable_trade_vetoing: bool = True
    veto_threshold_percentage: int = 51

    # Feature flags
    enable_waiver_bidding: bool = False
    enable_trade_analyzer: bool = True
    enable_keeper_trades: bool = False

    # Limits
    max_trades_per_week: int = 3
    max_roster_moves_per_week: int = 10

    # Cache settings
    waiver_cache_ttl: int = 300  # 5 minutes
    trade_cache_ttl: int = 600  # 10 minutes

    # Database settings
    trading_db_pool_size: int = 6
    trading_db_timeout: int = 30

    class Config:
        env_prefix = "TRADING_"
        case_sensitive = False


def get_trading_config() -> TradingConfig:
    """Get trading domain configuration."""
    return TradingConfig()


def get_waiver_settings() -> Dict[str, Any]:
    """Get waiver-specific settings."""
    config = get_trading_config()
    return {
        "waiver_period_hours": config.waiver_period_hours,
        "waiver_priority_type": config.waiver_priority_type,
        "max_waiver_claims_per_week": config.max_waiver_claims_per_week,
        "enable_waiver_bidding": config.enable_waiver_bidding,
    }


def get_trade_settings() -> Dict[str, Any]:
    """Get trade-specific settings."""
    config = get_trading_config()
    return {
        "trade_review_period_hours": config.trade_review_period_hours,
        "require_commissioner_approval": config.require_commissioner_approval,
        "enable_trade_vetoing": config.enable_trade_vetoing,
        "veto_threshold_percentage": config.veto_threshold_percentage,
        "max_trades_per_week": config.max_trades_per_week,
    }