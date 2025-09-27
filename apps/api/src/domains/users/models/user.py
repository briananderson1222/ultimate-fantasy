from __future__ import annotations

import uuid as _uuid
from datetime import datetime, timedelta
from typing import Any

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    Index,
    Integer,
    String,
)
from sqlalchemy.dialects.postgresql import JSON, UUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from domains.shared.models.base import Base


class User(Base):
    """Platform users with authentication and profile management."""

    __tablename__ = "users"

    user_id: Mapped[_uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=_uuid.uuid4
    )
    username: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)
    email: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    cognito_sub: Mapped[str | None] = mapped_column(
        String(128), nullable=True, unique=True
    )

    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    is_email_verified: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False
    )
    email_verification_token: Mapped[str | None] = mapped_column(
        String(255), nullable=True
    )
    password_reset_token: Mapped[str | None] = mapped_column(String(255), nullable=True)
    password_reset_expires: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    first_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    last_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    display_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    bio: Mapped[str | None] = mapped_column(String(500), nullable=True)
    avatar_url: Mapped[str | None] = mapped_column(String(500), nullable=True)

    phone_number: Mapped[str | None] = mapped_column(String(20), nullable=True)
    timezone: Mapped[str] = mapped_column(String(50), nullable=False, default="UTC")
    country: Mapped[str | None] = mapped_column(String(2), nullable=True)

    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    is_admin: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    is_premium: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    premium_expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    preferences: Mapped[dict[str, Any] | None] = mapped_column(
        JSON, nullable=True, default=dict
    )
    notification_settings: Mapped[dict[str, Any] | None] = mapped_column(
        JSON, nullable=True, default=dict
    )
    privacy_settings: Mapped[dict[str, Any] | None] = mapped_column(
        JSON, nullable=True, default=dict
    )

    last_login_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    last_active_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    login_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    __table_args__ = (
        CheckConstraint("login_count >= 0", name="non_negative_login_count"),
        Index("idx_user_username", "username", unique=True),
        Index("idx_user_email", "email", unique=True),
        Index("idx_user_cognito_sub", "cognito_sub", unique=True),
        Index("idx_user_is_active", "is_active"),
        Index("idx_user_is_premium", "is_premium"),
        Index("idx_user_last_active", "last_active_at"),
        Index("idx_user_created_at", "created_at"),
        Index("idx_user_email_verified", "is_email_verified"),
        Index("idx_user_email_verification", "email_verification_token"),
        Index("idx_user_password_reset", "password_reset_token"),
        Index("idx_user_password_reset_expires", "password_reset_expires"),
    )

    def __repr__(self) -> str:  # pragma: no cover - repr helper
        return f"<User(username='{self.username}', email='{self.email}', active={self.is_active})>"

    def record_login(self) -> None:
        now = datetime.utcnow()
        self.last_login_at = now
        self.last_active_at = now
        self.login_count += 1

    def update_activity(self) -> None:
        self.last_active_at = datetime.utcnow()

    def verify_email(self) -> None:
        self.is_email_verified = True
        self.email_verification_token = None

    def set_password_reset_token(self, token: str, expires_hours: int = 24) -> None:
        self.password_reset_token = token
        self.password_reset_expires = datetime.utcnow() + timedelta(hours=expires_hours)

    def clear_password_reset_token(self) -> None:
        self.password_reset_token = None
        self.password_reset_expires = None

    def is_password_reset_valid(self) -> bool:
        if not self.password_reset_token or not self.password_reset_expires:
            return False
        return datetime.utcnow() < self.password_reset_expires

    def activate_premium(self, duration_days: int) -> None:
        self.is_premium = True
        self.premium_expires_at = datetime.utcnow() + timedelta(days=duration_days)

    def deactivate_premium(self) -> None:
        self.is_premium = False
        self.premium_expires_at = None

    def is_premium_active(self) -> bool:
        if not self.is_premium:
            return False
        if not self.premium_expires_at:
            return True
        return datetime.utcnow() < self.premium_expires_at

    def deactivate_account(self) -> None:
        self.is_active = False

    def reactivate_account(self) -> None:
        self.is_active = True

    def get_preference(self, key: str, default: Any = None) -> Any:
        if not self.preferences:
            return default
        return self.preferences.get(key, default)

    def set_preference(self, key: str, value: Any) -> None:
        if self.preferences is None:
            self.preferences = {}
        self.preferences[key] = value

    def update_preferences(self, new_preferences: dict[str, Any]) -> None:
        if self.preferences is None:
            self.preferences = {}
        self.preferences.update(new_preferences)

    def get_notification_setting(self, key: str, default: Any = None) -> Any:
        if not self.notification_settings:
            return default
        return self.notification_settings.get(key, default)

    def set_notification_setting(self, key: str, value: Any) -> None:
        if self.notification_settings is None:
            self.notification_settings = {}
        self.notification_settings[key] = value

    def get_privacy_setting(self, key: str, default: Any = None) -> Any:
        if not self.privacy_settings:
            return default
        return self.privacy_settings.get(key, default)

    def set_privacy_setting(self, key: str, value: Any) -> None:
        if self.privacy_settings is None:
            self.privacy_settings = {}
        self.privacy_settings[key] = value

    def get_full_name(self) -> str:
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        if self.display_name:
            return self.display_name
        return self.username

    def get_display_data(self, include_private: bool = False) -> dict[str, Any]:
        data = {
            "id": str(self.user_id),
            "username": self.username,
            "display_name": self.display_name or self.username,
            "full_name": self.get_full_name(),
            "avatar_url": self.avatar_url,
            "bio": self.bio,
            "is_premium": self.is_premium_active(),
            "created_at": self.created_at.isoformat(),
            "last_active_at": (
                self.last_active_at.isoformat() if self.last_active_at else None
            ),
        }

        if include_private:
            data.update(
                {
                    "email": self.email,
                    "first_name": self.first_name,
                    "last_name": self.last_name,
                    "phone_number": self.phone_number,
                    "timezone": self.timezone,
                    "country": self.country,
                    "is_email_verified": self.is_email_verified,
                    "preferences": self.preferences,
                    "notification_settings": self.notification_settings,
                    "privacy_settings": self.privacy_settings,
                    "login_count": self.login_count,
                    "last_login_at": (
                        self.last_login_at.isoformat() if self.last_login_at else None
                    ),
                }
            )

        return data

    @classmethod
    def get_default_preferences(cls) -> dict[str, Any]:
        return {
            "theme": "light",
            "language": "en",
            "date_format": "MM/DD/YYYY",
            "time_format": "12h",
            "draft_auto_pick": False,
            "trade_notifications": True,
            "waiver_notifications": True,
            "injury_alerts": True,
            "weekly_summary": True,
        }

    @classmethod
    def get_default_notification_settings(cls) -> dict[str, Any]:
        return {
            "email_enabled": True,
            "push_enabled": True,
            "sms_enabled": False,
            "trade_proposals": True,
            "draft_reminders": True,
            "lineup_reminders": True,
            "injury_alerts": True,
            "waiver_results": True,
            "league_updates": True,
            "marketing_emails": False,
        }

    @classmethod
    def get_default_privacy_settings(cls) -> dict[str, Any]:
        return {
            "profile_visibility": "public",
            "email_visibility": "private",
            "phone_visibility": "private",
            "activity_visibility": "friends",
            "league_visibility": "public",
            "stats_visibility": "public",
            "allow_friend_requests": True,
            "allow_league_invites": True,
        }
