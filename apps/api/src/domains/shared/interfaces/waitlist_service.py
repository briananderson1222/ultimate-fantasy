"""
Abstract Base Class for Waitlist Service interface.

This interface defines the contract for waitlist domain operations
and enables cross-domain communication without tight coupling.
"""

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Optional


class WaitlistServiceInterface(ABC):
    """Abstract interface for Waitlist domain service operations."""

    @abstractmethod
    async def add_to_waitlist(self, user_id: str, league_id: str) -> "WaitlistEntry":
        """
        Add a user to a league's waitlist.

        Args:
            user_id: Unique identifier for the user
            league_id: Unique identifier for the league

        Returns:
            WaitlistEntry object representing the waitlist position

        Raises:
            ValueError: If user is already on waitlist or league is full
        """

    @abstractmethod
    async def process_waitlist_invite(self, invite_id: str) -> bool:
        """
        Process a waitlist invitation (accept/decline).

        Args:
            invite_id: Unique identifier for the invitation

        Returns:
            True if invitation was successfully processed, False otherwise

        Raises:
            ValueError: If invite_id is invalid or expired
        """

    @abstractmethod
    async def get_waitlist_position(self, entry_id: str) -> int:
        """
        Get the current position of a waitlist entry.

        Args:
            entry_id: Unique identifier for the waitlist entry

        Returns:
            Current position in waitlist (1-based)

        Raises:
            ValueError: If entry_id is invalid or entry not found
        """

    @abstractmethod
    async def get_league_waitlist(self, league_id: str) -> list["WaitlistEntry"]:
        """
        Get all waitlist entries for a league, ordered by position.

        Args:
            league_id: Unique identifier for the league

        Returns:
            List of WaitlistEntry objects ordered by priority
        """

    @abstractmethod
    async def remove_from_waitlist(self, entry_id: str) -> bool:
        """
        Remove an entry from the waitlist.

        Args:
            entry_id: Unique identifier for the waitlist entry

        Returns:
            True if successfully removed, False if entry not found
        """

    @abstractmethod
    async def send_waitlist_invite(self, entry_id: str) -> "WaitlistInvite":
        """
        Send an invitation to a waitlisted user.

        Args:
            entry_id: Unique identifier for the waitlist entry

        Returns:
            WaitlistInvite object representing the sent invitation

        Raises:
            ValueError: If entry_id is invalid or user already invited
        """

    @abstractmethod
    async def get_user_waitlist_status(
        self, user_id: str, league_id: str
    ) -> Optional["WaitlistEntry"]:
        """
        Get user's waitlist status for a specific league.

        Args:
            user_id: Unique identifier for the user
            league_id: Unique identifier for the league

        Returns:
            WaitlistEntry if user is on waitlist, None otherwise
        """


# Type hints for forward references
if TYPE_CHECKING:
    from domains.waitlist.models.waitlist_entry import WaitlistEntry
    from domains.waitlist.models.waitlist_invite import WaitlistInvite
