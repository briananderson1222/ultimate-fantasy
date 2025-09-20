"""
Abstract Base Class for League Service interface.

This interface defines the contract for league domain operations
and enables cross-domain communication without tight coupling.
"""

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING


class LeagueServiceInterface(ABC):
    """Abstract interface for League domain service operations."""

    @abstractmethod
    async def get_league_members(self, league_id: str) -> list["User"]:
        """
        Get all members of a league.

        Args:
            league_id: Unique identifier for the league

        Returns:
            List of User objects representing league members

        Raises:
            ValueError: If league_id is invalid or league doesn't exist
        """

    @abstractmethod
    async def validate_league_access(self, league_id: str, user_id: str) -> bool:
        """
        Validate if a user has access to a league.

        Args:
            league_id: Unique identifier for the league
            user_id: Unique identifier for the user

        Returns:
            True if user has access, False otherwise

        Raises:
            ValueError: If league_id or user_id is invalid
        """

    @abstractmethod
    async def get_league_settings(self, league_id: str) -> "LeagueSettings":
        """
        Get league configuration and settings.

        Args:
            league_id: Unique identifier for the league

        Returns:
            LeagueSettings object containing league configuration

        Raises:
            ValueError: If league_id is invalid or league doesn't exist
        """

    @abstractmethod
    async def get_league_by_id(self, league_id: str) -> "League":
        """
        Get league entity by ID.

        Args:
            league_id: Unique identifier for the league

        Returns:
            League object

        Raises:
            ValueError: If league_id is invalid or league doesn't exist
        """

    @abstractmethod
    async def is_league_commissioner(self, league_id: str, user_id: str) -> bool:
        """
        Check if user is the commissioner of a league.

        Args:
            league_id: Unique identifier for the league
            user_id: Unique identifier for the user

        Returns:
            True if user is commissioner, False otherwise
        """


# Type hints for forward references
if TYPE_CHECKING:
    from domains.leagues.models.league import League, LeagueSettings
    from domains.users.models.user import User