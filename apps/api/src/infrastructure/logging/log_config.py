"""Logging configuration for domain-specific logging."""

import os
import logging
from typing import Dict, Any
from pydantic_settings import BaseSettings


class LogConfig(BaseSettings):
    """Logging configuration settings."""

    # Global logging settings
    log_level: str = "INFO"
    log_format: str = "%(asctime)s - %(name)s - %(levelname)s - [%(domain)s] - %(message)s"
    log_file_path: str = "logs/ultimate_fantasy.log"

    # Domain-specific log levels
    leagues_log_level: str = "INFO"
    users_log_level: str = "INFO"
    lineups_log_level: str = "INFO"
    trading_log_level: str = "INFO"
    scoring_log_level: str = "INFO"
    waitlist_log_level: str = "INFO"

    # Feature flags
    enable_domain_separation: bool = True
    enable_file_logging: bool = True
    enable_console_logging: bool = True
    enable_request_id_tracking: bool = True

    # Performance settings
    log_rotation_size: str = "10MB"
    log_backup_count: int = 5

    class Config:
        env_prefix = "LOG_"
        case_sensitive = False


def get_log_config() -> LogConfig:
    """Get logging configuration."""
    return LogConfig()


def get_domain_log_levels() -> Dict[str, str]:
    """Get domain-specific log levels."""
    config = get_log_config()
    return {
        "leagues": config.leagues_log_level,
        "users": config.users_log_level,
        "lineups": config.lineups_log_level,
        "trading": config.trading_log_level,
        "scoring": config.scoring_log_level,
        "waitlist": config.waitlist_log_level,
    }


def setup_log_directory() -> None:
    """Create log directory if it doesn't exist."""
    config = get_log_config()
    log_dir = os.path.dirname(config.log_file_path)
    if log_dir and not os.path.exists(log_dir):
        os.makedirs(log_dir, exist_ok=True)