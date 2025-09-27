from __future__ import annotations

import hashlib
import os
import re
import secrets
import uuid as _uuid
from datetime import datetime, timedelta
from typing import Any

import jwt
from sqlalchemy import and_, or_
from sqlalchemy.orm import Session

from domains.shared.events.publisher import DomainEventPublisher
from domains.shared.exceptions import (
    AccountDisabledError,
    AuthenticationError,
    EmailAlreadyExistsError,
    InvalidTokenError,
    TokenExpiredError,
    UsernameAlreadyExistsError,
    UserNotFoundError,
    ValidationError,
    WeakPasswordError,
)
from domains.shared.interfaces.user_service import UserServiceInterface
from domains.shared.models.achievement import Achievement
from domains.users.models.user import User
from domains.users.models.user_preference import UserPreference
from infrastructure.database.session_factory import get_session_factory
from infrastructure.events.dispatcher import get_event_dispatcher


class UserService(UserServiceInterface):
    """Domain user service providing registration, auth, and profile helpers."""

    def __init__(
        self,
        session: Session | None = None,
        *,
        jwt_secret: str | None = None,
        jwt_algorithm: str = "HS256",
    ) -> None:
        if session is None:
            factory = get_session_factory()
            self.session = factory.get_sync_session()
            self._owns_session = True
        else:
            self.session = session
            self._owns_session = False

        self.jwt_secret = (
            jwt_secret
            or os.getenv("AUTH_DEV_SECRET")
            or os.getenv("AUTH_SECRET")
            or "dev-secret"
        )
        self.jwt_algorithm = jwt_algorithm
        self.password_min_length = int(os.getenv("AUTH_PASSWORD_MIN_LENGTH", "8"))
        self.token_expiry_hours = int(os.getenv("AUTH_ACCESS_TOKEN_HOURS", "24"))
        self.refresh_token_expiry_days = int(os.getenv("AUTH_REFRESH_TOKEN_DAYS", "30"))

        try:
            dispatcher = get_event_dispatcher()
            self.event_publisher: DomainEventPublisher | None = DomainEventPublisher(
                dispatcher, "users"
            )
        except RuntimeError:
            self.event_publisher = None

    # ---------------------------------------------------------------------
    # Registration & Authentication
    # ---------------------------------------------------------------------
    def create_user(
        self,
        *,
        username: str,
        email: str,
        password: str,
        first_name: str | None = None,
        last_name: str | None = None,
        date_of_birth: datetime | None = None,
        timezone: str = "UTC",
        db: Session | None = None,
    ) -> User:
        session = db or self.session
        if session is None:
            raise RuntimeError("Database session not available")

        username_normalized = username.strip().lower()
        self._validate_username(username_normalized)
        self._validate_email(email)
        self._validate_password(password)

        if session.query(User).filter(User.username == username_normalized).first():
            raise UsernameAlreadyExistsError("Username already exists")
        if session.query(User).filter(User.email == email).first():
            raise EmailAlreadyExistsError("Email already exists")

        password_hash = self._hash_password(password)
        user = User(
            username=username_normalized,
            email=email,
            password_hash=password_hash,
            first_name=first_name,
            last_name=last_name,
            display_name=first_name or username_normalized,
            timezone=timezone,
            preferences=User.get_default_preferences(),
            notification_settings=User.get_default_notification_settings(),
            privacy_settings=User.get_default_privacy_settings(),
        )
        session.add(user)
        session.flush()

        achievement = Achievement.create_first_login_achievement(user.user_id)
        session.add(achievement)
        session.commit()

        if self.event_publisher:
            self._publish_event(
                "user_registered",
                str(user.user_id),
                {
                    "user_id": str(user.user_id),
                    "username": user.username,
                    "email": user.email,
                },
            )

        return user

    def authenticate_user(
        self,
        *,
        username_or_email: str,
        password: str,
        db: Session | None = None,
    ) -> User:
        session = db or self.session
        if session is None:
            raise RuntimeError("Database session not available")

        user = (
            session.query(User)
            .filter(
                or_(
                    User.username == username_or_email.lower(),
                    User.email == username_or_email,
                )
            )
            .first()
        )
        if not user:
            raise AuthenticationError("Invalid credentials")
        if not user.is_active:
            raise AccountDisabledError("Account is deactivated")
        if not self._verify_password(password, user.password_hash):
            raise AuthenticationError("Invalid credentials")

        user.record_login()
        session.commit()
        return user

    def create_access_token(
        self,
        user_id: str,
        *,
        expires_in: int | None = None,
        db: Session | None = None,
    ) -> str:
        user = self.get_user_sync(user_id, db)
        payload = {
            "user_id": str(user.user_id),
            "username": getattr(
                user,
                "username",
                user.email.split("@")[0] if user.email else f"user_{user_id}",
            ),
            "email": user.email,
            "is_premium": user.is_premium_active(),
            "iat": datetime.utcnow(),
            "type": "access",
        }
        exp_delta = (
            timedelta(seconds=expires_in)
            if expires_in is not None
            else timedelta(hours=self.token_expiry_hours)
        )
        payload["exp"] = datetime.utcnow() + exp_delta
        return jwt.encode(payload, self.jwt_secret, algorithm=self.jwt_algorithm)

    def create_refresh_token(self, user_id: str, db: Session | None = None) -> str:
        user = self.get_user_sync(user_id, db)
        payload = {
            "user_id": str(user.user_id),
            "iat": datetime.utcnow(),
            "exp": datetime.utcnow() + timedelta(days=self.refresh_token_expiry_days),
            "type": "refresh",
        }
        return jwt.encode(payload, self.jwt_secret, algorithm=self.jwt_algorithm)

    def validate_token(self, token: str) -> dict[str, Any]:
        try:
            return jwt.decode(token, self.jwt_secret, algorithms=[self.jwt_algorithm])
        except jwt.ExpiredSignatureError as exc:
            raise TokenExpiredError("Token has expired") from exc
        except jwt.InvalidTokenError as exc:
            raise InvalidTokenError("Invalid token") from exc

    def refresh_access_token(
        self, refresh_token: str, db: Session | None = None
    ) -> dict[str, Any]:
        payload = self.validate_token(refresh_token)
        if payload.get("type") != "refresh":
            raise InvalidTokenError("Invalid token type")

        user = self.get_user_sync(payload["user_id"], db)
        if not user.is_active:
            raise AccountDisabledError("Account is deactivated")

        access_token = self.create_access_token(payload["user_id"], db=db)
        new_refresh = self.create_refresh_token(payload["user_id"], db=db)
        return {
            "access_token": access_token,
            "refresh_token": new_refresh,
            "token_type": "bearer",
            "expires_in": self.token_expiry_hours * 3600,
            "user_id": str(user.user_id),
        }

    def invalidate_token(self, token: str, db: Session | None = None) -> None:
        # Token blacklisting not implemented; method retained for interface compatibility.
        return None

    def log_user_activity(
        self,
        *,
        user_id: str,
        activity_type: str,
        ip_address: str | None = None,
        user_agent: str | None = None,
        db: Session | None = None,
    ) -> None:
        session = db or self.session
        if session is None:
            raise RuntimeError("Database session not available")
        user = session.query(User).filter(User.user_id == user_id).first()
        if not user:
            raise UserNotFoundError("User not found")
        user.update_activity()
        session.commit()

    def initiate_password_reset(self, email: str, db: Session | None = None) -> str:
        session = db or self.session
        if session is None:
            raise RuntimeError("Database session not available")
        user = session.query(User).filter(User.email == email).first()
        if not user:
            raise UserNotFoundError("User not found")
        token = secrets.token_urlsafe(32)
        user.set_password_reset_token(token)
        session.commit()
        return token

    def reset_password(
        self, *, token: str, new_password: str, db: Session | None = None
    ) -> None:
        session = db or self.session
        if session is None:
            raise RuntimeError("Database session not available")
        user = (
            session.query(User)
            .filter(
                and_(
                    User.password_reset_token == token,
                    User.password_reset_expires > datetime.utcnow(),
                )
            )
            .first()
        )
        if not user:
            raise InvalidTokenError("Invalid or expired reset token")
        self._validate_password(new_password)
        user.password_hash = self._hash_password(new_password)
        user.clear_password_reset_token()
        session.commit()

    def change_password(
        self,
        *,
        user_id: str,
        current_password: str,
        new_password: str,
        db: Session | None = None,
    ) -> None:
        session = db or self.session
        if session is None:
            raise RuntimeError("Database session not available")
        user = session.query(User).filter(User.user_id == user_id).first()
        if not user:
            raise UserNotFoundError("User not found")
        if not self._verify_password(current_password, user.password_hash):
            raise AuthenticationError("Invalid current password")
        self._validate_password(new_password)
        user.password_hash = self._hash_password(new_password)
        user.clear_password_reset_token()
        session.commit()

    # ------------------------------------------------------------------
    # Profile Management
    # ------------------------------------------------------------------
    def get_user_sync(self, user_id: str, db: Session | None = None) -> User:
        session = db or self.session
        if session is None:
            raise RuntimeError("Database session not available")

        # Convert string to UUID if necessary
        if isinstance(user_id, str):
            try:
                user_id_uuid = _uuid.UUID(user_id)
            except ValueError:
                raise UserNotFoundError("Invalid user ID format")
        else:
            user_id_uuid = user_id

        user = session.query(User).filter(User.user_id == user_id_uuid).first()
        if not user:
            raise UserNotFoundError("User not found")
        return user

    def update_user_profile(
        self,
        *,
        user_id: str,
        updates: dict[str, Any],
        db: Session | None = None,
    ) -> User:
        session = db or self.session
        if session is None:
            raise RuntimeError("Database session not available")
        user = session.query(User).filter(User.user_id == user_id).first()
        if not user:
            raise UserNotFoundError("User not found")

        allowed_fields = {
            "first_name",
            "last_name",
            "display_name",
            "bio",
            "avatar_url",
            "phone_number",
            "timezone",
            "country",
        }
        for field, value in updates.items():
            if field not in allowed_fields:
                raise ValidationError(f"Field '{field}' cannot be updated")
            if field == "phone_number" and value:
                self._validate_phone_number(value)
            if field == "country" and value:
                self._validate_country_code(value)
            setattr(user, field, value)
        session.commit()
        return user

    def update_user_preferences(
        self,
        *,
        user_id: str,
        preferences: dict[str, Any],
        db: Session | None = None,
    ) -> User:
        user = self.get_user_sync(user_id, db)
        user.update_preferences(preferences)
        (db or self.session).commit()
        return user

    def update_notification_settings(
        self,
        *,
        user_id: str,
        settings: dict[str, Any],
        db: Session | None = None,
    ) -> User:
        user = self.get_user_sync(user_id, db)
        for key, value in settings.items():
            user.set_notification_setting(key, value)
        (db or self.session).commit()
        return user

    def delete_user_account(
        self,
        *,
        user_id: str,
        password: str | None = None,
        db: Session | None = None,
    ) -> None:
        session = db or self.session
        user = self.get_user_sync(user_id, session)
        if password and not self._verify_password(password, user.password_hash):
            raise AuthenticationError("Invalid password")
        user.deactivate_account()
        session.commit()

    def resend_verification_email(self, user_id: str, db: Session | None = None) -> str:
        user = self.get_user_sync(user_id, db)
        token = secrets.token_urlsafe(32)
        user.email_verification_token = token
        (db or self.session).commit()
        return token

    def verify_email(self, token: str, db: Session | None = None) -> User:
        session = db or self.session
        if session is None:
            raise RuntimeError("Database session not available")
        user = (
            session.query(User).filter(User.email_verification_token == token).first()
        )
        if not user:
            raise InvalidTokenError("Invalid verification token")
        user.verify_email()
        session.commit()
        return user

    def get_user_sessions(
        self, user_id: str, db: Session | None = None
    ) -> list[dict[str, Any]]:
        # Session management not yet implemented; return empty list for compatibility.
        self.get_user_sync(user_id, db)
        return []

    def revoke_session(
        self, user_id: str, session_id: str, db: Session | None = None
    ) -> bool:
        self.get_user_sync(user_id, db)
        return True

    def revoke_all_sessions(self, user_id: str, db: Session | None = None) -> int:
        self.get_user_sync(user_id, db)
        return 0

    # ------------------------------------------------------------------
    # Interface implementations (async) for other domains
    # ------------------------------------------------------------------
    async def get_user(self, user_id: str) -> User:  # type: ignore[override]
        return self.get_user_sync(user_id, None)

    async def validate_user_permissions(
        self, user_id: str, resource: str, action: str = "read"
    ) -> bool:
        try:
            user = self.get_user_sync(user_id, None)
        except UserNotFoundError:
            return False
        return user.is_active

    async def get_user_preferences(self, user_id: str) -> UserPreference:
        session = self.session
        if session is None:
            raise RuntimeError("Database session not available")

        user_pref = (
            session.query(UserPreference)
            .filter(UserPreference.user_id == user_id)
            .first()
        )
        if not user_pref:
            # Create default preferences if they don't exist
            user_pref = UserPreference(user_id=user_id)
            session.add(user_pref)
            session.commit()

        return user_pref

    async def get_user_by_email(self, email: str) -> User | None:
        session = self.session
        if session is None:
            return None
        return session.query(User).filter(User.email == email).first()

    async def is_user_active(self, user_id: str) -> bool:
        try:
            user = self.get_user_sync(user_id, None)
        except UserNotFoundError:
            return False
        return user.is_active

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _publish_event(
        self, event: str, entity_id: str, payload: dict[str, Any]
    ) -> None:
        if not self.event_publisher:
            return
        import asyncio

        task = asyncio.create_task(
            self.event_publisher.publish_event(event, entity_id, payload)
        )
        task.add_done_callback(lambda t: t.exception())

    def _validate_username(self, username: str) -> None:
        if not username or len(username) < 3 or len(username) > 50:
            raise ValidationError("Username must be 3-50 characters long")
        if not re.match(r"^[a-zA-Z0-9_]+$", username):
            raise ValidationError(
                "Username can only contain letters, numbers, and underscores"
            )

    def _validate_email(self, email: str) -> None:
        if not email or not re.match(r"^[^@]+@[^@]+\.[^@]+$", email):
            raise ValidationError("Invalid email format")

    def _validate_password(self, password: str) -> None:
        if not password or len(password) < self.password_min_length:
            raise WeakPasswordError(
                f"Password must be at least {self.password_min_length} characters long"
            )

    def _validate_phone_number(self, phone: str) -> None:
        if not re.match(r"^\+?[1-9]\d{1,14}$", phone):
            raise ValidationError("Invalid phone number format")

    def _validate_country_code(self, country: str) -> None:
        if not re.match(r"^[A-Z]{2}$", country):
            raise ValidationError("Country code must be a 2-letter ISO value")

    def _hash_password(self, password: str) -> str:
        salt = secrets.token_hex(16)
        password_hash = hashlib.sha256((password + salt).encode()).hexdigest()
        return f"{salt}:{password_hash}"

    def _verify_password(self, password: str, stored_hash: str) -> bool:
        try:
            salt, password_hash = stored_hash.split(":")
        except ValueError:
            return False
        return hashlib.sha256((password + salt).encode()).hexdigest() == password_hash

    def ensure_user_from_claims(
        self, claims: dict[str, Any], db: Session | None = None
    ) -> User:
        """Ensure user exists based on JWT claims, create if necessary."""
        session = db or self.session
        if session is None:
            raise RuntimeError("Database session not available")

        sub = claims.get("sub")
        email = claims.get("email")
        username = claims.get("username")

        if not sub:
            raise AuthenticationError("Invalid claims: missing sub")

        # Try to find existing user
        user = session.query(User).filter(User.cognito_sub == sub).first()

        if user:
            return user

        # Create new user from claims
        if not email:
            raise AuthenticationError("Invalid claims: missing email")

        # Generate username if not provided
        if not username:
            username = email.split("@")[0].lower()
            # Ensure uniqueness
            counter = 1
            base_username = username
            while session.query(User).filter(User.username == username).first():
                username = f"{base_username}{counter}"
                counter += 1

        user = User(
            username=username,
            email=email,
            cognito_sub=sub,
            password_hash="external_auth:no_local_password",  # Placeholder for external auth users
            display_name=username,
            preferences=User.get_default_preferences(),
            notification_settings=User.get_default_notification_settings(),
            privacy_settings=User.get_default_privacy_settings(),
        )

        session.add(user)
        session.commit()
        return user

    def __del__(self) -> None:  # pragma: no cover - best effort cleanup
        if getattr(self, "_owns_session", False) and self.session is not None:
            try:
                self.session.close()
            except Exception:  # noqa: BLE001
                pass
