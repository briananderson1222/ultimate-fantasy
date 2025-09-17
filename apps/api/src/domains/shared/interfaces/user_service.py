"""
Abstract Base Class for User Service interface.

This interface defines the contract for user domain operations
and enables cross-domain communication without tight coupling.
"""
from abc import ABC, abstractmethod
from typing import Optional


class UserServiceInterface(ABC):
    """Abstract interface for User domain service operations."""

    @abstractmethod
    async def get_user(self, user_id: str) -> "User":
        """
        Get user by ID.

        Args:
            user_id: Unique identifier for the user

        Returns:
            User object

        Raises:
            ValueError: If user_id is invalid or user doesn't exist
        """
        pass

    @abstractmethod
    async def validate_user_permissions(
        self, user_id: str, resource: str, action: str = "read"
    ) -> bool:
        """
        Validate user permissions for a specific resource and action.

        Args:
            user_id: Unique identifier for the user
            resource: Resource identifier (e.g., "league:123", "trading:456")
            action: Action to validate ("read", "write", "admin")

        Returns:
            True if user has permission, False otherwise

        Raises:
            ValueError: If user_id is invalid
        """
        pass

    @abstractmethod
    async def get_user_preferences(self, user_id: str) -> "UserPreferences":
        """
        Get user preferences and settings.

        Args:
            user_id: Unique identifier for the user

        Returns:
            UserPreferences object

        Raises:
            ValueError: If user_id is invalid or user doesn't exist
        """
        pass

    @abstractmethod
    async def get_user_by_email(self, email: str) -> Optional["User"]:
        """
        Get user by email address.

        Args:
            email: User's email address

        Returns:
            User object if found, None otherwise

        Raises:
            ValueError: If email format is invalid
        """
        pass

    @abstractmethod
    async def is_user_active(self, user_id: str) -> bool:
        """
        Check if user account is active.

        Args:
            user_id: Unique identifier for the user

        Returns:
            True if user is active, False otherwise
        """
        pass


# Type hints for forward references
if False:  # TYPE_CHECKING equivalent
    from backend.src.domains.users.models.user import User, UserPreferences