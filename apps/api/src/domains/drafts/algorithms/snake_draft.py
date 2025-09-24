"""
Snake draft algorithm implementation for fantasy sports drafts.

Provides comprehensive snake draft functionality including:
- Dynamic draft order calculation with round-by-round reversals
- Pick order generation for any number of teams and rounds
- Draft position tracking and validation
- Time-based pick progression
- Auto-pick handling when timer expires
- Draft order randomization and seeding
- Support for keeper/dynasty draft modifications
- Pick trading and compensation logic
"""

import random
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from uuid import UUID

try:
    from infrastructure.logging.domain_logger import get_logger
except ImportError:
    import logging
    get_logger = logging.getLogger  # type: ignore[assignment]

logger = get_logger(__name__)


@dataclass
class DraftPick:
    """Represents a single draft pick."""

    overall_pick: int
    round_number: int
    pick_in_round: int
    team_id: str
    player_id: Optional[str] = None
    pick_time: Optional[datetime] = None
    is_autopick: bool = False
    is_keeper: bool = False
    original_team_id: Optional[str] = None  # For traded picks


@dataclass
class DraftOrder:
    """Represents the complete draft order."""

    teams: List[str]
    total_rounds: int
    picks: List[DraftPick]
    randomized_at: Optional[datetime] = None
    seed: Optional[int] = None


class SnakeDraftError(Exception):
    """Snake draft algorithm errors."""
    pass


class SnakeDraftAlgorithm:
    """
    Snake draft algorithm implementation.

    In a snake draft:
    - Round 1: Team 1, Team 2, Team 3, ..., Team N
    - Round 2: Team N, Team N-1, Team N-2, ..., Team 1
    - Round 3: Team 1, Team 2, Team 3, ..., Team N
    - And so on, alternating direction each round
    """

    def __init__(self):
        self.draft_orders: Dict[str, DraftOrder] = {}

    def generate_draft_order(
        self,
        teams: List[str],
        total_rounds: int,
        randomize: bool = True,
        seed: Optional[int] = None,
        keeper_picks: Optional[Dict[str, List[int]]] = None,
        traded_picks: Optional[List[Tuple[str, str, int]]] = None,
        draft_id: Optional[str] = None,
    ) -> DraftOrder:
        """
        Generate complete snake draft order.

        Args:
            teams: List of team IDs in draft
            total_rounds: Total number of draft rounds
            randomize: Whether to randomize initial order
            seed: Random seed for reproducible randomization
            keeper_picks: Dict of team_id -> list of round numbers for keepers
            traded_picks: List of (from_team, to_team, overall_pick) tuples
            draft_id: Optional draft ID for caching

        Returns:
            Complete draft order with all picks

        Raises:
            SnakeDraftError: If parameters are invalid
        """
        if not teams:
            raise SnakeDraftError("At least one team is required")

        if total_rounds < 1:
            raise SnakeDraftError("At least one round is required")

        if len(teams) != len(set(teams)):
            raise SnakeDraftError("Duplicate teams not allowed")

        logger.info(
            f"Generating snake draft order",
            extra={
                "teams_count": len(teams),
                "total_rounds": total_rounds,
                "randomize": randomize,
                "draft_id": draft_id,
            }
        )

        # Create working copy of teams
        draft_teams = teams.copy()

        # Randomize order if requested
        randomized_at = None
        if randomize:
            if seed is not None:
                random.seed(seed)
            random.shuffle(draft_teams)
            randomized_at = datetime.utcnow()
            logger.info(f"Randomized draft order: {draft_teams}")

        # Generate picks for each round
        all_picks = []
        overall_pick = 1

        for round_num in range(1, total_rounds + 1):
            # Determine if this is an odd or even round
            is_odd_round = round_num % 2 == 1

            # For odd rounds, use normal order; for even rounds, reverse
            round_teams = draft_teams if is_odd_round else list(reversed(draft_teams))

            for pick_in_round, team_id in enumerate(round_teams, 1):
                pick = DraftPick(
                    overall_pick=overall_pick,
                    round_number=round_num,
                    pick_in_round=pick_in_round,
                    team_id=team_id,
                    original_team_id=team_id,
                )

                # Check if this is a keeper pick
                if keeper_picks and team_id in keeper_picks:
                    if round_num in keeper_picks[team_id]:
                        pick.is_keeper = True
                        # Keeper picks might have predetermined players
                        logger.debug(f"Marked pick {overall_pick} as keeper for team {team_id}")

                all_picks.append(pick)
                overall_pick += 1

        # Apply traded picks
        if traded_picks:
            all_picks = self._apply_traded_picks(all_picks, traded_picks)

        # Create draft order object
        draft_order = DraftOrder(
            teams=draft_teams,
            total_rounds=total_rounds,
            picks=all_picks,
            randomized_at=randomized_at,
            seed=seed,
        )

        # Cache if draft_id provided
        if draft_id:
            self.draft_orders[draft_id] = draft_order

        logger.info(
            f"Generated snake draft order with {len(all_picks)} picks",
            extra={"draft_id": draft_id, "total_picks": len(all_picks)}
        )

        return draft_order

    def get_current_pick(
        self,
        draft_order: DraftOrder,
        completed_picks: List[str],
    ) -> Optional[DraftPick]:
        """
        Get the current pick that needs to be made.

        Args:
            draft_order: Complete draft order
            completed_picks: List of overall pick numbers that are completed

        Returns:
            Current pick to be made, or None if draft is complete
        """
        completed_set = set(completed_picks)

        for pick in draft_order.picks:
            if pick.overall_pick not in completed_set:
                return pick

        return None  # Draft is complete

    def get_team_picks(
        self,
        draft_order: DraftOrder,
        team_id: str,
    ) -> List[DraftPick]:
        """
        Get all picks for a specific team.

        Args:
            draft_order: Complete draft order
            team_id: Team to get picks for

        Returns:
            List of picks for the team
        """
        return [pick for pick in draft_order.picks if pick.team_id == team_id]

    def get_round_picks(
        self,
        draft_order: DraftOrder,
        round_number: int,
    ) -> List[DraftPick]:
        """
        Get all picks for a specific round.

        Args:
            draft_order: Complete draft order
            round_number: Round to get picks for

        Returns:
            List of picks in the round
        """
        return [pick for pick in draft_order.picks if pick.round_number == round_number]

    def validate_pick(
        self,
        draft_order: DraftOrder,
        overall_pick: int,
        team_id: str,
        completed_picks: List[str],
    ) -> bool:
        """
        Validate that a pick can be made by a specific team.

        Args:
            draft_order: Complete draft order
            overall_pick: Overall pick number being made
            team_id: Team attempting to make the pick
            completed_picks: List of completed pick numbers

        Returns:
            True if pick is valid, False otherwise
        """
        # Find the pick
        pick = next(
            (p for p in draft_order.picks if p.overall_pick == overall_pick),
            None
        )

        if not pick:
            logger.warning(f"Pick {overall_pick} not found in draft order")
            return False

        # Check if it's the team's turn
        if pick.team_id != team_id:
            logger.warning(f"Pick {overall_pick} belongs to {pick.team_id}, not {team_id}")
            return False

        # Check if this is the next pick
        current_pick = self.get_current_pick(draft_order, completed_picks)
        if not current_pick or current_pick.overall_pick != overall_pick:
            expected = current_pick.overall_pick if current_pick else "draft complete"
            logger.warning(f"Expected pick {expected}, but got {overall_pick}")
            return False

        return True

    def calculate_pick_deadline(
        self,
        pick_start_time: datetime,
        timer_seconds: int,
    ) -> datetime:
        """
        Calculate when a pick timer expires.

        Args:
            pick_start_time: When the pick timer started
            timer_seconds: Number of seconds for the timer

        Returns:
            Deadline datetime for the pick
        """
        return pick_start_time + timedelta(seconds=timer_seconds)

    def is_pick_expired(
        self,
        pick_start_time: datetime,
        timer_seconds: int,
        current_time: Optional[datetime] = None,
    ) -> bool:
        """
        Check if a pick timer has expired.

        Args:
            pick_start_time: When the pick timer started
            timer_seconds: Number of seconds for the timer
            current_time: Current time (defaults to now)

        Returns:
            True if pick has expired, False otherwise
        """
        current_time = current_time or datetime.utcnow()
        deadline = self.calculate_pick_deadline(pick_start_time, timer_seconds)
        return current_time >= deadline

    def get_time_remaining(
        self,
        pick_start_time: datetime,
        timer_seconds: int,
        current_time: Optional[datetime] = None,
    ) -> int:
        """
        Get remaining time in seconds for a pick.

        Args:
            pick_start_time: When the pick timer started
            timer_seconds: Number of seconds for the timer
            current_time: Current time (defaults to now)

        Returns:
            Remaining seconds (0 if expired)
        """
        current_time = current_time or datetime.utcnow()
        deadline = self.calculate_pick_deadline(pick_start_time, timer_seconds)
        remaining = (deadline - current_time).total_seconds()
        return max(0, int(remaining))

    def generate_mock_draft_order(
        self,
        num_teams: int,
        rounds: int = 15,
        randomize: bool = True,
    ) -> DraftOrder:
        """
        Generate a mock draft order for testing.

        Args:
            num_teams: Number of teams
            rounds: Number of rounds
            randomize: Whether to randomize order

        Returns:
            Mock draft order
        """
        teams = [f"team_{i+1}" for i in range(num_teams)]
        return self.generate_draft_order(
            teams=teams,
            total_rounds=rounds,
            randomize=randomize,
        )

    # Private helper methods

    def _apply_traded_picks(
        self,
        picks: List[DraftPick],
        traded_picks: List[Tuple[str, str, int]],
    ) -> List[DraftPick]:
        """Apply traded picks to the draft order."""
        picks_dict = {pick.overall_pick: pick for pick in picks}

        for from_team, to_team, overall_pick in traded_picks:
            if overall_pick in picks_dict:
                pick = picks_dict[overall_pick]
                if pick.original_team_id is None:
                    pick.original_team_id = pick.team_id
                pick.team_id = to_team
                logger.info(f"Traded pick {overall_pick} from {from_team} to {to_team}")
            else:
                logger.warning(f"Cannot trade non-existent pick {overall_pick}")

        return list(picks_dict.values())

    def get_pick_analysis(
        self,
        draft_order: DraftOrder,
        team_id: str,
    ) -> Dict[str, any]:
        """
        Analyze draft positioning for a team.

        Args:
            draft_order: Complete draft order
            team_id: Team to analyze

        Returns:
            Analysis dictionary with pick distribution data
        """
        team_picks = self.get_team_picks(draft_order, team_id)

        if not team_picks:
            return {"error": f"Team {team_id} not found in draft"}

        # Calculate pick distribution
        picks_by_round = {}
        early_picks = 0  # Top third of round
        middle_picks = 0  # Middle third
        late_picks = 0   # Bottom third

        teams_count = len(draft_order.teams)

        for pick in team_picks:
            picks_by_round[pick.round_number] = pick.pick_in_round

            # Categorize pick position within round
            if pick.pick_in_round <= teams_count // 3:
                early_picks += 1
            elif pick.pick_in_round <= 2 * teams_count // 3:
                middle_picks += 1
            else:
                late_picks += 1

        # Calculate average draft position
        total_pick_value = sum(pick.overall_pick for pick in team_picks)
        avg_pick_position = total_pick_value / len(team_picks)

        # Find team's initial draft position
        initial_position = next(
            (i + 1 for i, team in enumerate(draft_order.teams) if team == team_id),
            None
        )

        return {
            "team_id": team_id,
            "total_picks": len(team_picks),
            "initial_draft_position": initial_position,
            "average_pick_position": round(avg_pick_position, 1),
            "picks_by_round": picks_by_round,
            "pick_distribution": {
                "early_round_picks": early_picks,
                "middle_round_picks": middle_picks,
                "late_round_picks": late_picks,
            },
            "keeper_picks": len([p for p in team_picks if p.is_keeper]),
            "traded_picks": len([p for p in team_picks if p.original_team_id != p.team_id]),
        }

    def export_draft_order(
        self,
        draft_order: DraftOrder,
        format: str = "dict",
    ) -> any:
        """
        Export draft order in various formats.

        Args:
            draft_order: Draft order to export
            format: Export format ('dict', 'csv', 'json')

        Returns:
            Exported data in requested format
        """
        if format == "dict":
            return {
                "teams": draft_order.teams,
                "total_rounds": draft_order.total_rounds,
                "total_picks": len(draft_order.picks),
                "randomized_at": draft_order.randomized_at.isoformat() if draft_order.randomized_at else None,
                "seed": draft_order.seed,
                "picks": [
                    {
                        "overall_pick": pick.overall_pick,
                        "round": pick.round_number,
                        "pick_in_round": pick.pick_in_round,
                        "team_id": pick.team_id,
                        "is_keeper": pick.is_keeper,
                        "original_team": pick.original_team_id,
                    }
                    for pick in draft_order.picks
                ]
            }
        elif format == "csv":
            # Return CSV-ready data
            csv_data = []
            csv_data.append("Overall Pick,Round,Pick in Round,Team ID,Is Keeper,Original Team")

            for pick in draft_order.picks:
                csv_data.append(
                    f"{pick.overall_pick},{pick.round_number},{pick.pick_in_round},"
                    f"{pick.team_id},{pick.is_keeper},{pick.original_team_id or pick.team_id}"
                )

            return "\n".join(csv_data)
        else:
            # JSON format
            import json
            return json.dumps(self.export_draft_order(draft_order, "dict"), indent=2)


# Global algorithm instance
_snake_draft_algorithm: Optional[SnakeDraftAlgorithm] = None


def get_snake_draft_algorithm() -> SnakeDraftAlgorithm:
    """Get the global snake draft algorithm instance."""
    global _snake_draft_algorithm
    if _snake_draft_algorithm is None:
        _snake_draft_algorithm = SnakeDraftAlgorithm()
    return _snake_draft_algorithm


def reset_snake_draft_algorithm():
    """Reset the global algorithm (useful for testing)."""
    global _snake_draft_algorithm
    _snake_draft_algorithm = None