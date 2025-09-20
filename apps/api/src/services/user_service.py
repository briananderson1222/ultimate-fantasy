from __future__ import annotations

import uuid as _uuid
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
import hashlib
import secrets
import jwt
import re

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from ..models.user import User
from ..models.achievement import Achievement
from ..infrastructure.database.session_factory import get_db_session
from ..infrastructure.logging.domain_logger import get_logger

logger = get_logger(__name__)


class UserServiceError(Exception):
    """Base exception for user service errors"""
    pass


class AuthenticationError(UserServiceError):
    """Authentication related errors"""
    pass


class ValidationError(UserServiceError):
    """Data validation errors"""
    pass


class UserAlreadyExistsError(UserServiceError):
    """User already exists errors"""
    pass


class UserService:
    """
    User service for authentication, registration, and profile management

    Implements T026 requirements:
    - UserService with CRUD operations
    - Authentication, registration, profile management
    - JWT token generation and validation
    """

    def __init__(self, jwt_secret: str = "your-secret-key", jwt_algorithm: str = "HS256"):
        self.jwt_secret = jwt_secret
        self.jwt_algorithm = jwt_algorithm
        self.password_min_length = 8
        self.token_expiry_hours = 24
        self.refresh_token_expiry_days = 30

    # Authentication Methods

    def register_user(
        self,
        username: str,
        email: str,
        password: str,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        db: Optional[Session] = None
    ) -> User:
        """
        Register a new user with validation and password hashing

        Args:
            username: Unique username (3-50 chars, alphanumeric + underscores)
            email: Valid email address
            password: Password (min 8 chars)
            first_name: Optional first name
            last_name: Optional last name
            db: Optional database session

        Returns:
            Created User instance

        Raises:
            ValidationError: Invalid input data
            UserAlreadyExistsError: Username or email already exists
        """
        # Validate input
        self._validate_username(username)
        self._validate_email(email)
        self._validate_password(password)

        with get_db_session() if db is None else db as session:
            # Check if user already exists
            existing_user = session.query(User).filter(
                or_(User.username == username, User.email == email)
            ).first()

            if existing_user:
                if existing_user.username == username:
                    raise UserAlreadyExistsError("Username already exists")
                else:
                    raise UserAlreadyExistsError("Email already exists")

            # Hash password
            password_hash = self._hash_password(password)

            # Create user
            user = User(
                username=username,
                email=email,
                password_hash=password_hash,
                first_name=first_name,
                last_name=last_name,
                display_name=first_name or username,
                email_verification_token=self._generate_verification_token(),
                preferences=User.get_default_preferences(),
                notification_settings=User.get_default_notification_settings(),
                privacy_settings=User.get_default_privacy_settings()
            )

            session.add(user)
            session.flush()  # Get the user_id

            # Create first login achievement
            first_login_achievement = Achievement.create_first_login_achievement(user.user_id)
            session.add(first_login_achievement)

            session.commit()

            logger.info(f"User registered successfully: {username}")
            return user

    def authenticate_user(self, username_or_email: str, password: str, db: Optional[Session] = None) -> User:
        """
        Authenticate user with username/email and password

        Args:
            username_or_email: Username or email address
            password: Plain text password
            db: Optional database session

        Returns:
            Authenticated User instance

        Raises:
            AuthenticationError: Invalid credentials or inactive account
        """
        with get_db_session() if db is None else db as session:
            # Find user by username or email
            user = session.query(User).filter(
                or_(User.username == username_or_email, User.email == username_or_email)
            ).first()

            if not user:
                raise AuthenticationError("Invalid credentials")

            if not user.is_active:
                raise AuthenticationError("Account is deactivated")

            # Verify password
            if not self._verify_password(password, user.password_hash):
                raise AuthenticationError("Invalid credentials")

            # Record login
            user.record_login()
            session.commit()

            logger.info(f"User authenticated successfully: {user.username}")
            return user

    def generate_access_token(self, user: User) -> str:
        """
        Generate JWT access token for user

        Args:
            user: User instance

        Returns:
            JWT access token string
        """
        payload = {
            "user_id": str(user.user_id),
            "username": user.username,
            "email": user.email,
            "is_premium": user.is_premium_active(),
            "exp": datetime.utcnow() + timedelta(hours=self.token_expiry_hours),
            "iat": datetime.utcnow(),
            "type": "access"
        }

        return jwt.encode(payload, self.jwt_secret, algorithm=self.jwt_algorithm)

    def generate_refresh_token(self, user: User) -> str:
        """
        Generate JWT refresh token for user

        Args:
            user: User instance

        Returns:
            JWT refresh token string
        """
        payload = {
            "user_id": str(user.user_id),
            "exp": datetime.utcnow() + timedelta(days=self.refresh_token_expiry_days),
            "iat": datetime.utcnow(),
            "type": "refresh"
        }

        return jwt.encode(payload, self.jwt_secret, algorithm=self.jwt_algorithm)

    def validate_token(self, token: str) -> Dict[str, Any]:
        """
        Validate and decode JWT token

        Args:
            token: JWT token string

        Returns:
            Decoded token payload

        Raises:
            AuthenticationError: Invalid or expired token
        """
        try:
            payload = jwt.decode(token, self.jwt_secret, algorithms=[self.jwt_algorithm])
            return payload
        except jwt.ExpiredSignatureError:
            raise AuthenticationError("Token has expired")
        except jwt.InvalidTokenError:
            raise AuthenticationError("Invalid token")

    def refresh_access_token(self, refresh_token: str, db: Optional[Session] = None) -> tuple[str, User]:
        """
        Generate new access token from refresh token

        Args:
            refresh_token: Valid refresh token
            db: Optional database session

        Returns:
            Tuple of (new_access_token, user)

        Raises:
            AuthenticationError: Invalid refresh token
        """
        payload = self.validate_token(refresh_token)

        if payload.get("type") != "refresh":
            raise AuthenticationError("Invalid token type")

        user = self.get_user_by_id(payload["user_id"], db=db)
        if not user or not user.is_active:
            raise AuthenticationError("Invalid user")

        access_token = self.generate_access_token(user)
        return access_token, user

    # User Management Methods

    def get_user_by_id(self, user_id: str, db: Optional[Session] = None) -> Optional[User]:
        """Get user by ID"""
        with get_db_session() if db is None else db as session:
            return session.query(User).filter(User.user_id == user_id).first()

    def get_user_by_username(self, username: str, db: Optional[Session] = None) -> Optional[User]:
        """Get user by username"""
        with get_db_session() if db is None else db as session:
            return session.query(User).filter(User.username == username).first()

    def get_user_by_email(self, email: str, db: Optional[Session] = None) -> Optional[User]:
        """Get user by email"""
        with get_db_session() if db is None else db as session:
            return session.query(User).filter(User.email == email).first()

    def update_user_profile(
        self,
        user_id: str,
        updates: Dict[str, Any],
        db: Optional[Session] = None
    ) -> User:
        """
        Update user profile information

        Args:
            user_id: User ID
            updates: Dictionary of fields to update
            db: Optional database session

        Returns:
            Updated User instance

        Raises:
            UserServiceError: User not found or validation error
        """
        with get_db_session() if db is None else db as session:
            user = session.query(User).filter(User.user_id == user_id).first()
            if not user:
                raise UserServiceError("User not found")

            # Validate updates
            allowed_fields = {
                'first_name', 'last_name', 'display_name', 'bio', 'avatar_url',
                'phone_number', 'timezone', 'country'
            }

            for field, value in updates.items():
                if field not in allowed_fields:
                    raise ValidationError(f"Field '{field}' cannot be updated")

                if field == 'phone_number' and value:
                    self._validate_phone_number(value)
                elif field == 'country' and value:
                    self._validate_country_code(value)

                setattr(user, field, value)

            session.commit()

            logger.info(f"User profile updated: {user.username}")
            return user

    def update_user_preferences(
        self,
        user_id: str,
        preferences: Dict[str, Any],
        db: Optional[Session] = None
    ) -> User:
        """Update user preferences"""
        with get_db_session() if db is None else db as session:
            user = session.query(User).filter(User.user_id == user_id).first()
            if not user:
                raise UserServiceError("User not found")

            user.update_preferences(preferences)
            session.commit()

            return user

    def update_notification_settings(
        self,
        user_id: str,
        settings: Dict[str, Any],
        db: Optional[Session] = None
    ) -> User:
        """Update user notification settings"""
        with get_db_session() if db is None else db as session:
            user = session.query(User).filter(User.user_id == user_id).first()
            if not user:
                raise UserServiceError("User not found")

            for key, value in settings.items():
                user.set_notification_setting(key, value)

            session.commit()
            return user

    def change_password(
        self,
        user_id: str,
        current_password: str,
        new_password: str,
        db: Optional[Session] = None
    ) -> None:
        """
        Change user password with current password verification

        Args:
            user_id: User ID
            current_password: Current password for verification
            new_password: New password
            db: Optional database session

        Raises:
            AuthenticationError: Invalid current password
            ValidationError: Invalid new password
        """
        with get_db_session() if db is None else db as session:
            user = session.query(User).filter(User.user_id == user_id).first()
            if not user:
                raise UserServiceError("User not found")

            # Verify current password
            if not self._verify_password(current_password, user.password_hash):
                raise AuthenticationError("Invalid current password")

            # Validate new password
            self._validate_password(new_password)

            # Update password
            user.password_hash = self._hash_password(new_password)
            user.clear_password_reset_token()

            session.commit()

            logger.info(f"Password changed for user: {user.username}")

    def request_password_reset(self, email: str, db: Optional[Session] = None) -> str:
        """
        Request password reset token

        Args:
            email: User email address
            db: Optional database session

        Returns:
            Password reset token

        Raises:
            UserServiceError: User not found
        """
        with get_db_session() if db is None else db as session:
            user = session.query(User).filter(User.email == email).first()
            if not user:
                raise UserServiceError("User not found")

            reset_token = self._generate_password_reset_token()
            user.set_password_reset_token(reset_token)

            session.commit()

            logger.info(f"Password reset requested for user: {user.username}")
            return reset_token

    def reset_password(
        self,
        token: str,
        new_password: str,
        db: Optional[Session] = None
    ) -> None:
        """
        Reset password using reset token

        Args:
            token: Password reset token
            new_password: New password
            db: Optional database session

        Raises:
            AuthenticationError: Invalid or expired token
            ValidationError: Invalid new password
        """
        with get_db_session() if db is None else db as session:
            user = session.query(User).filter(
                and_(
                    User.password_reset_token == token,
                    User.password_reset_expires > datetime.utcnow()
                )
            ).first()

            if not user:
                raise AuthenticationError("Invalid or expired reset token")

            # Validate new password
            self._validate_password(new_password)

            # Update password and clear reset token
            user.password_hash = self._hash_password(new_password)
            user.clear_password_reset_token()

            session.commit()

            logger.info(f"Password reset completed for user: {user.username}")

    def verify_email(self, token: str, db: Optional[Session] = None) -> User:
        """
        Verify user email with verification token

        Args:
            token: Email verification token
            db: Optional database session

        Returns:
            Verified User instance

        Raises:
            AuthenticationError: Invalid token
        """
        with get_db_session() if db is None else db as session:
            user = session.query(User).filter(
                User.email_verification_token == token
            ).first()

            if not user:
                raise AuthenticationError("Invalid verification token")

            user.verify_email()
            session.commit()

            logger.info(f"Email verified for user: {user.username}")
            return user

    def deactivate_user(self, user_id: str, db: Optional[Session] = None) -> None:
        """Deactivate user account"""
        with get_db_session() if db is None else db as session:
            user = session.query(User).filter(User.user_id == user_id).first()
            if not user:
                raise UserServiceError("User not found")

            user.deactivate_account()
            session.commit()

            logger.info(f"User deactivated: {user.username}")

    def reactivate_user(self, user_id: str, db: Optional[Session] = None) -> None:
        """Reactivate user account"""
        with get_db_session() if db is None else db as session:
            user = session.query(User).filter(User.user_id == user_id).first()
            if not user:
                raise UserServiceError("User not found")

            user.reactivate_account()
            session.commit()

            logger.info(f"User reactivated: {user.username}")

    def search_users(
        self,
        query: str,
        limit: int = 20,
        offset: int = 0,
        db: Optional[Session] = None
    ) -> List[User]:
        """
        Search users by username, display name, or email

        Args:
            query: Search query
            limit: Maximum results to return
            offset: Results offset for pagination
            db: Optional database session

        Returns:
            List of matching User instances
        """
        with get_db_session() if db is None else db as session:
            search_pattern = f"%{query}%"

            users = session.query(User).filter(
                and_(
                    User.is_active == True,
                    or_(
                        User.username.ilike(search_pattern),
                        User.display_name.ilike(search_pattern),
                        User.email.ilike(search_pattern)
                    )
                )
            ).offset(offset).limit(limit).all()

            return users

    # Private Helper Methods

    def _validate_username(self, username: str) -> None:
        """Validate username format and length"""
        if not username or len(username) < 3 or len(username) > 50:
            raise ValidationError("Username must be 3-50 characters long")

        if not re.match(r'^[a-zA-Z0-9_]+$', username):
            raise ValidationError("Username can only contain letters, numbers, and underscores")

    def _validate_email(self, email: str) -> None:
        """Validate email format"""
        if not email or not re.match(r'^[^@]+@[^@]+\.[^@]+$', email):
            raise ValidationError("Invalid email format")

    def _validate_password(self, password: str) -> None:
        """Validate password strength"""
        if not password or len(password) < self.password_min_length:
            raise ValidationError(f"Password must be at least {self.password_min_length} characters long")

    def _validate_phone_number(self, phone: str) -> None:
        """Validate phone number format"""
        if not re.match(r'^\+?[1-9]\d{1,14}$', phone):
            raise ValidationError("Invalid phone number format")

    def _validate_country_code(self, country: str) -> None:
        """Validate ISO country code"""
        if not re.match(r'^[A-Z]{2}$', country):
            raise ValidationError("Country code must be 2-letter ISO format")

    def _hash_password(self, password: str) -> str:
        """Hash password using SHA-256 with salt"""
        salt = secrets.token_hex(16)
        password_hash = hashlib.sha256((password + salt).encode()).hexdigest()
        return f"{salt}:{password_hash}"

    def _verify_password(self, password: str, stored_hash: str) -> bool:
        """Verify password against stored hash"""
        try:
            salt, password_hash = stored_hash.split(':')
            return hashlib.sha256((password + salt).encode()).hexdigest() == password_hash
        except ValueError:
            return False

    def _generate_verification_token(self) -> str:
        """Generate email verification token"""
        return secrets.token_urlsafe(32)

    def _generate_password_reset_token(self) -> str:
        """Generate password reset token"""
        return secrets.token_urlsafe(32)