"""
Abstract Base Class for Trading Service interface.

This interface defines the contract for trading domain operations
and enables cross-domain communication without tight coupling.
"""
from abc import ABC, abstractmethod


class TradingServiceInterface(ABC):
    """Abstract interface for Trading domain service operations."""

    @abstractmethod
    async def validate_trade_eligibility(self, user_id: str, league_id: str) -> bool:
        """
        Validate if a user is eligible to make trades in a league.

        Args:
            user_id: Unique identifier for the user
            league_id: Unique identifier for the league

        Returns:
            True if user is eligible to trade, False otherwise

        Raises:
            ValueError: If user_id or league_id is invalid
        """

    @abstractmethod
    async def process_waiver_claim(self, waiver_id: str, user_id: str) -> "Transaction":
        """
        Process a waiver claim for a user.

        Args:
            waiver_id: Unique identifier for the waiver
            user_id: Unique identifier for the user making the claim

        Returns:
            Transaction object representing the processed claim

        Raises:
            ValueError: If waiver_id is invalid or claim cannot be processed
        """

    @abstractmethod
    async def get_active_waivers(self, league_id: str) -> list["Waiver"]:
        """
        Get all active waivers for a league.

        Args:
            league_id: Unique identifier for the league

        Returns:
            List of active Waiver objects ordered by priority

        Raises:
            ValueError: If league_id is invalid
        """

    @abstractmethod
    async def get_user_transactions(self, user_id: str, league_id: str) -> list["Transaction"]:
        """
        Get all transactions for a user in a specific league.

        Args:
            user_id: Unique identifier for the user
            league_id: Unique identifier for the league

        Returns:
            List of Transaction objects
        """

    @abstractmethod
    async def validate_waiver_claim(self, waiver_id: str, user_id: str) -> bool:
        """
        Validate if a user can claim a specific waiver.

        Args:
            waiver_id: Unique identifier for the waiver
            user_id: Unique identifier for the user

        Returns:
            True if claim is valid, False otherwise
        """

    @abstractmethod
    async def get_trade_deadline(self, league_id: str) -> "datetime":
        """
        Get the trade deadline for a league.

        Args:
            league_id: Unique identifier for the league

        Returns:
            Datetime of trade deadline

        Raises:
            ValueError: If league_id is invalid
        """


# Type hints for forward references
if False:  # TYPE_CHECKING equivalent
    from datetime import datetime

    from backend.src.domains.trading.models.transaction import Transaction
    from backend.src.domains.trading.models.waiver import Waiver
