"""
Abstract Base Class for Lineup Service interface.

This interface defines the contract for lineup domain operations
and enables cross-domain communication without tight coupling.
"""

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING


class LineupServiceInterface(ABC):
    """Abstract interface for Lineup domain service operations."""

    @abstractmethod
    async def get_lineup(self, lineup_id: str) -> "Lineup":
        """
        Get lineup by ID.

        Args:
            lineup_id: Unique identifier for the lineup

        Returns:
            Lineup object

        Raises:
            ValueError: If lineup_id is invalid or lineup doesn't exist
        """

    @abstractmethod
    async def validate_lineup_ownership(self, lineup_id: str, user_id: str) -> bool:
        """
        Validate if a user owns a specific lineup.

        Args:
            lineup_id: Unique identifier for the lineup
            user_id: Unique identifier for the user

        Returns:
            True if user owns the lineup, False otherwise

        Raises:
            ValueError: If lineup_id or user_id is invalid
        """

    @abstractmethod
    async def get_lineup_by_user_league(self, user_id: str, league_id: str) -> "Lineup":
        """
        Get user's lineup for a specific league.

        Args:
            user_id: Unique identifier for the user
            league_id: Unique identifier for the league

        Returns:
            Lineup object for the user in the specified league

        Raises:
            ValueError: If user doesn't have a lineup in the league
        """

    @abstractmethod
    async def get_lineups_by_league(self, league_id: str) -> list["Lineup"]:
        """
        Get all lineups for a specific league.

        Args:
            league_id: Unique identifier for the league

        Returns:
            List of Lineup objects for the league
        """

    @abstractmethod
    async def is_lineup_active(self, lineup_id: str) -> bool:
        """
        Check if a lineup is active for the current period.

        Args:
            lineup_id: Unique identifier for the lineup

        Returns:
            True if lineup is active, False otherwise
        """

    @abstractmethod
    async def get_lineup_slots(self, lineup_id: str) -> list[dict]:
        """
        Get all slots for a specific lineup.

        Args:
            lineup_id: Unique identifier for the lineup

        Returns:
            List of dict (ie. LineupSlot objects)
        """


# Type hints for forward references
if TYPE_CHECKING:
    from domains.lineups.models.lineup import Lineup
