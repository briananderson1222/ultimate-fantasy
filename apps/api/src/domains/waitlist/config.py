"""Waitlist domain configuration."""

from typing import Any

from pydantic_settings import BaseSettings


class WaitlistConfig(BaseSettings):
    """Configuration for the Waitlist domain."""

    # Waitlist settings
    max_waitlist_size: int = 50
    auto_invite_enabled: bool = True
    invitation_expiry_hours: int = 72
    waitlist_position_visible: bool = True

    # Notification settings
    notify_on_position_change: bool = True
    notify_on_invitation: bool = True
    email_reminder_hours: int = 24

    # Feature flags
    enable_waitlist_priority: bool = False
    enable_referral_bonus: bool = False
    allow_waitlist_comments: bool = False

    # Limits
    max_waitlists_per_user: int = 10
    min_time_between_joins_hours: int = 1

    # Cache settings
    waitlist_cache_ttl: int = 600  # 10 minutes
    position_cache_ttl: int = 300  # 5 minutes

    # Database settings
    waitlist_db_pool_size: int = 4
    waitlist_db_timeout: int = 20

    class Config:
        env_prefix = "WAITLIST_"
        case_sensitive = False


def get_waitlist_config() -> WaitlistConfig:
    """Get waitlist domain configuration."""
    return WaitlistConfig()


def get_waitlist_limits() -> dict[str, Any]:
    """Get waitlist limits and constraints."""
    config = get_waitlist_config()
    return {
        "max_waitlist_size": config.max_waitlist_size,
        "max_waitlists_per_user": config.max_waitlists_per_user,
        "min_time_between_joins_hours": config.min_time_between_joins_hours,
        "invitation_expiry_hours": config.invitation_expiry_hours,
    }


def get_waitlist_notifications() -> dict[str, Any]:
    """Get waitlist notification settings."""
    config = get_waitlist_config()
    return {
        "notify_on_position_change": config.notify_on_position_change,
        "notify_on_invitation": config.notify_on_invitation,
        "email_reminder_hours": config.email_reminder_hours,
        "waitlist_position_visible": config.waitlist_position_visible,
    }
