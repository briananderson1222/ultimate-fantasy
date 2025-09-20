from __future__ import annotations

import uuid as _uuid
from datetime import datetime, timedelta
from typing import Optional, Dict, Any

from sqlalchemy import String, Integer, DateTime, Boolean, Index, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID, JSON
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from .base import Base


class User(Base):
    """
    Platform users with authentication and profile management

    Implements T025 requirements:
    - User entity for authentication and profile management
    - Add preferences JSON and notification settings
    - Include security and privacy controls
    """
    __tablename__ = "users"

    # Primary identification
    user_id: Mapped[_uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=_uuid.uuid4
    )
    username: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)
    email: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)

    # Authentication
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    is_email_verified: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    email_verification_token: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    password_reset_token: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    password_reset_expires: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Profile information
    first_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    last_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    display_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    bio: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    avatar_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    # Contact and location
    phone_number: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    timezone: Mapped[str] = mapped_column(String(50), nullable=False, default="UTC")
    country: Mapped[Optional[str]] = mapped_column(String(2), nullable=True)  # ISO country code

    # Account status and settings
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    is_premium: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    premium_expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # User preferences (JSON object)
    preferences: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True, default=dict)
    notification_settings: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True, default=dict)
    privacy_settings: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True, default=dict)

    # Activity tracking
    last_login_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    last_active_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    login_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now()
    )

    # Validation constraints
    __table_args__ = (
        # Username validation (alphanumeric + underscores, 3-50 chars)
        CheckConstraint(
            "username ~ '^[a-zA-Z0-9_]{3,50}$'",
            name="valid_username"
        ),
        # Email validation (basic format check)
        CheckConstraint(
            "email ~ '^[^@]+@[^@]+\\.[^@]+$'",
            name="valid_email_format"
        ),
        # Phone number validation (optional, basic format)
        CheckConstraint(
            "phone_number IS NULL OR phone_number ~ '^\\+?[1-9]\\d{1,14}$'",
            name="valid_phone_format"
        ),
        # Country code validation (2-letter ISO codes)
        CheckConstraint(
            "country IS NULL OR country ~ '^[A-Z]{2}$'",
            name="valid_country_code"
        ),
        # Login count must be non-negative
        CheckConstraint(
            "login_count >= 0",
            name="non_negative_login_count"
        ),
        # Premium expiration should be in future if user is premium
        CheckConstraint(
            "NOT (is_premium = true AND premium_expires_at IS NOT NULL AND premium_expires_at <= NOW())",
            name="valid_premium_expiration"
        ),
        # Common query indexes
        Index('idx_user_username', 'username', unique=True),
        Index('idx_user_email', 'email', unique=True),
        Index('idx_user_is_active', 'is_active'),
        Index('idx_user_is_premium', 'is_premium'),
        Index('idx_user_last_active', 'last_active_at'),
        Index('idx_user_created_at', 'created_at'),
        Index('idx_user_email_verified', 'is_email_verified'),
        # Security indexes
        Index('idx_user_email_verification', 'email_verification_token'),
        Index('idx_user_password_reset', 'password_reset_token'),
        Index('idx_user_password_reset_expires', 'password_reset_expires'),
    )

    def __repr__(self) -> str:
        return f"<User(username='{self.username}', email='{self.email}', active={self.is_active})>"

    def record_login(self) -> None:
        """Record user login"""
        now = datetime.utcnow()
        self.last_login_at = now
        self.last_active_at = now
        self.login_count += 1

    def update_activity(self) -> None:
        """Update last active timestamp"""
        self.last_active_at = datetime.utcnow()

    def verify_email(self) -> None:
        """Mark email as verified and clear verification token"""
        self.is_email_verified = True
        self.email_verification_token = None

    def set_password_reset_token(self, token: str, expires_hours: int = 24) -> None:
        """Set password reset token with expiration"""
        self.password_reset_token = token
        self.password_reset_expires = datetime.utcnow() + timedelta(hours=expires_hours)

    def clear_password_reset_token(self) -> None:
        """Clear password reset token"""
        self.password_reset_token = None
        self.password_reset_expires = None

    def is_password_reset_valid(self) -> bool:
        """Check if password reset token is valid and not expired"""
        if not self.password_reset_token or not self.password_reset_expires:
            return False
        return datetime.utcnow() < self.password_reset_expires

    def activate_premium(self, duration_days: int) -> None:
        """Activate premium subscription"""
        self.is_premium = True
        self.premium_expires_at = datetime.utcnow() + timedelta(days=duration_days)

    def deactivate_premium(self) -> None:
        """Deactivate premium subscription"""
        self.is_premium = False
        self.premium_expires_at = None

    def is_premium_active(self) -> bool:
        """Check if premium subscription is active"""
        if not self.is_premium:
            return False
        if self.premium_expires_at is None:
            return True  # Lifetime premium
        return datetime.utcnow() < self.premium_expires_at

    def deactivate_account(self) -> None:
        """Deactivate user account"""
        self.is_active = False

    def reactivate_account(self) -> None:
        """Reactivate user account"""
        self.is_active = True

    def get_preference(self, key: str, default: Any = None) -> Any:
        """Get specific preference value"""
        if not self.preferences:
            return default
        return self.preferences.get(key, default)

    def set_preference(self, key: str, value: Any) -> None:
        """Set specific preference value"""
        if self.preferences is None:
            self.preferences = {}
        self.preferences[key] = value

    def update_preferences(self, new_preferences: Dict[str, Any]) -> None:
        """Update multiple preferences at once"""
        if self.preferences is None:
            self.preferences = {}
        self.preferences.update(new_preferences)

    def get_notification_setting(self, key: str, default: Any = None) -> Any:
        """Get specific notification setting"""
        if not self.notification_settings:
            return default
        return self.notification_settings.get(key, default)

    def set_notification_setting(self, key: str, value: Any) -> None:
        """Set specific notification setting"""
        if self.notification_settings is None:
            self.notification_settings = {}
        self.notification_settings[key] = value

    def get_privacy_setting(self, key: str, default: Any = None) -> Any:
        """Get specific privacy setting"""
        if not self.privacy_settings:
            return default
        return self.privacy_settings.get(key, default)

    def set_privacy_setting(self, key: str, value: Any) -> None:
        """Set specific privacy setting"""
        if self.privacy_settings is None:
            self.privacy_settings = {}
        self.privacy_settings[key] = value

    def get_full_name(self) -> str:
        """Get user's full name or fallback to display name/username"""
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        elif self.display_name:
            return self.display_name
        else:
            return self.username

    def get_display_data(self, include_private: bool = False) -> Dict[str, Any]:
        """Get user data for display"""
        data = {
            "id": str(self.user_id),
            "username": self.username,
            "display_name": self.display_name or self.username,
            "full_name": self.get_full_name(),
            "avatar_url": self.avatar_url,
            "bio": self.bio,
            "is_premium": self.is_premium_active(),
            "created_at": self.created_at.isoformat(),
            "last_active_at": self.last_active_at.isoformat() if self.last_active_at else None
        }

        if include_private:
            data.update({
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
                "last_login_at": self.last_login_at.isoformat() if self.last_login_at else None
            })

        return data

    @classmethod
    def get_default_preferences(cls) -> Dict[str, Any]:
        """Get default user preferences"""
        return {
            "theme": "light",
            "language": "en",
            "date_format": "MM/DD/YYYY",
            "time_format": "12h",
            "draft_auto_pick": False,
            "trade_notifications": True,
            "waiver_notifications": True,
            "injury_alerts": True,
            "weekly_summary": True
        }

    @classmethod
    def get_default_notification_settings(cls) -> Dict[str, Any]:
        """Get default notification settings"""
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
            "marketing_emails": False
        }

    @classmethod
    def get_default_privacy_settings(cls) -> Dict[str, Any]:
        """Get default privacy settings"""
        return {
            "profile_visibility": "public",
            "email_visibility": "private",
            "phone_visibility": "private",
            "activity_visibility": "friends",
            "league_visibility": "public",
            "stats_visibility": "public",
            "allow_friend_requests": True,
            "allow_league_invites": True
        }