"""
Abstract Base Class for Scoring Service interface.

This interface defines the contract for scoring domain operations
and enables cross-domain communication without tight coupling.
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Any


class ScoringServiceInterface(ABC):
    """Abstract interface for Scoring domain service operations."""

    @abstractmethod
    async def calculate_lineup_score(self, lineup_id: str, period: str) -> "Score":
        """
        Calculate total score for a lineup in a specific period.

        Args:
            lineup_id: Unique identifier for the lineup
            period: Scoring period (e.g., "week-1", "season")

        Returns:
            Score object with calculated total points

        Raises:
            ValueError: If lineup_id is invalid or period is not found
        """
        pass

    @abstractmethod
    async def get_scoring_rules(self, league_id: str) -> "ScoringRules":
        """
        Get scoring rules for a specific league.

        Args:
            league_id: Unique identifier for the league

        Returns:
            ScoringRules object containing point values and rules

        Raises:
            ValueError: If league_id is invalid or rules not found
        """
        pass

    @abstractmethod
    async def audit_score_calculation(self, score_id: str) -> "ScoreAudit":
        """
        Get audit trail for a score calculation.

        Args:
            score_id: Unique identifier for the score

        Returns:
            ScoreAudit object with calculation details and history

        Raises:
            ValueError: If score_id is invalid
        """
        pass

    @abstractmethod
    async def get_player_performance(
        self, player_id: str, period: str
    ) -> "PlayerPerformance":
        """
        Get performance data for a specific player in a period.

        Args:
            player_id: Unique identifier for the player
            period: Performance period

        Returns:
            PlayerPerformance object with stats and points

        Raises:
            ValueError: If player_id is invalid or period not found
        """
        pass

    @abstractmethod
    async def get_league_standings(self, league_id: str, period: str) -> List[Dict[str, Any]]:
        """
        Get current standings for a league in a specific period.

        Args:
            league_id: Unique identifier for the league
            period: Scoring period

        Returns:
            List of standings data ordered by rank

        Raises:
            ValueError: If league_id is invalid
        """
        pass

    @abstractmethod
    async def recalculate_scores(self, league_id: str, period: str) -> List["Score"]:
        """
        Recalculate all scores for a league in a specific period.

        Args:
            league_id: Unique identifier for the league
            period: Scoring period to recalculate

        Returns:
            List of updated Score objects

        Raises:
            ValueError: If league_id is invalid
        """
        pass


# Type hints for forward references
if False:  # TYPE_CHECKING equivalent
    from backend.src.domains.scoring.models.score import Score
    from backend.src.domains.scoring.models.scoring_rule import ScoringRules
    from backend.src.domains.scoring.models.score_audit import ScoreAudit
    from backend.src.domains.scoring.models.player_performance import PlayerPerformance