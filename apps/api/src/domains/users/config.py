"""User domain configuration."""

from typing import Dict, Any
from pydantic_settings import BaseSettings


class UserConfig(BaseSettings):
    """Configuration for the User domain."""

    # Authentication settings
    jwt_secret_key: str = "dev-secret-key"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7

    # User preferences
    default_timezone: str = "UTC"
    default_language: str = "en"
    enable_email_notifications: bool = True
    enable_push_notifications: bool = False

    # Security settings
    password_min_length: int = 8
    password_require_special: bool = True
    max_login_attempts: int = 5
    lockout_duration_minutes: int = 15

    # Cache settings
    user_cache_ttl: int = 900  # 15 minutes
    preferences_cache_ttl: int = 1800  # 30 minutes

    # Database settings
    user_db_pool_size: int = 10
    user_db_timeout: int = 30

    class Config:
        env_prefix = "USER_"
        case_sensitive = False


def get_user_config() -> UserConfig:
    """Get user domain configuration."""
    return UserConfig()


def get_user_security_settings() -> Dict[str, Any]:
    """Get user domain security settings."""
    config = get_user_config()
    return {
        "password_min_length": config.password_min_length,
        "password_require_special": config.password_require_special,
        "max_login_attempts": config.max_login_attempts,
        "lockout_duration_minutes": config.lockout_duration_minutes,
    }


def get_user_notification_settings() -> Dict[str, bool]:
    """Get user domain notification settings."""
    config = get_user_config()
    return {
        "enable_email_notifications": config.enable_email_notifications,
        "enable_push_notifications": config.enable_push_notifications,
    }