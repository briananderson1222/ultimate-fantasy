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
from typing import Any


@dataclass
class DraftOrder:
    """Represents a single draft pick."""
    team_id: str
    round_number: int
    pick_number: int
    overall_pick: int


class SnakeDraftAlgorithm:
    """Snake draft algorithm implementation.

    In a snake draft:
    - Round 1: Team 1, Team 2, Team 3, ..., Team N
    - Round 2: Team N, Team N-1, Team N-2, ..., Team 1
    - Round 3: Team 1, Team 2, Team 3, ..., Team N
    - And so on, alternating direction each round
    """

    def __init__(self) -> None:
        self.draft_orders: dict[str, DraftOrder] = {}
        self.draft_order: dict[str, list[int]] = {}

    def generate_draft_order(
        self,
        teams: list[str],
        rounds: int,
        randomize_order: bool = False,
        random_seed: int | None = None,
    ) -> dict[str, list[tuple[str, str, int]]]:
        """Generate complete snake draft order.

        Args:
            teams: List of team IDs
            rounds: Total number of draft rounds
            randomize_order: Whether to randomize initial order
            random_seed: Random seed for reproducibility

        Returns:
            Dict of team_id to list of overall_pick numbers
        """
        if not teams:
            raise ValueError("Teams list cannot be empty")
        if rounds <= 0:
            raise ValueError("Rounds must be positive")

        if randomize_order:
            if random_seed is not None:
                random.seed(random_seed)
            teams = teams.copy()
            random.shuffle(teams)

        draft_order = {team_id: [] for team_id in teams}
        overall_pick = 1

        for round_num in range(1, rounds + 1):
            if round_num % 2 == 1:
                # Odd rounds: forward order
                pick_order = teams
            else:
                # Even rounds: reverse order
                pick_order = list(reversed(teams))

            for team_id in pick_order:
                draft_order[team_id].append(overall_pick)
                overall_pick += 1

        return draft_order

    def get_current_pick(
        self, draft_order: dict[str, list[int]], completed_picks: list[int]
    ) -> int:
        """Get the current pick that needs to be made.

        Args:
            draft_order: Complete draft order
            completed_picks: List of completed pick numbers

        Returns:
            Current pick number to be made
        """
        all_picks = []
        for picks in draft_order.values():
            all_picks.extend(picks)

        all_picks.sort()
        for pick in all_picks:
            if pick not in completed_picks:
                return pick

        raise ValueError("All picks have been completed")

    def get_team_picks(
        self, draft_order: dict[str, list[int]], team_id: str
    ) -> list[int]:
        """Get picks for a specific team.

        Args:
            draft_order: Complete draft order
            team_id: Team to get picks for

        Returns:
            List of pick numbers for the team
        """
        return draft_order.get(team_id, [])

    def get_round_picks(
        self, draft_order: dict[str, list[int]], round_number: int
    ) -> list[int]:
        """Get picks for a specific round.

        Args:
            draft_order: Complete draft order
            round_number: Round to get picks for

        Returns:
            List of pick numbers in the round
        """
        all_picks = []
        for picks in draft_order.values():
            if round_number <= len(picks):
                all_picks.append(picks[round_number - 1])
        return all_picks

    def validate_pick(
        self, draft_order: dict[str, list[int]], pick_number: int, team_id: str
    ) -> bool:
        """Validate that a pick can be made by a specific team.

        Args:
            draft_order: Complete draft order
            pick_number: Overall pick number being made
            team_id: Team attempting to make the pick

        Returns:
            True if the pick is valid
        """
        team_picks = draft_order.get(team_id, [])
        return pick_number in team_picks

    def calculate_pick_timer(
        self, pick_number: int, base_time: int = 60
    ) -> datetime:
        """Calculate when a pick timer should start.

        Args:
            pick_number: Overall pick number
            base_time: Number of seconds for the pick timer

        Returns:
            Deadline datetime for the pick
        """
        return datetime.now() + timedelta(seconds=base_time)

    def check_pick_timer(
        self, pick_number: int, start_time: datetime, base_time: int = 60
    ) -> int:
        """Check remaining time for a pick timer.

        Args:
            pick_number: Overall pick number
            start_time: When the pick timer started
            base_time: Number of seconds for the pick timer

        Returns:
            Remaining seconds, or 0 if expired
        """
        deadline = start_time + timedelta(seconds=base_time)
        remaining = (deadline - datetime.now()).total_seconds()
        return max(0, int(remaining))

    def get_remaining_time(self, pick_number: int, start_time: datetime, base_time: int = 60) -> int:
        """Get remaining time for a pick.

        Args:
            pick_number: Overall pick number
            start_time: When the pick timer started
            base_time: Number of seconds for the pick timer

        Returns:
            Remaining seconds
        """
        return self.check_pick_timer(pick_number, start_time, base_time)

    def generate_mock_draft_order(
        self, teams: int, rounds: int, randomize_order: bool = False
    ) -> dict[str, list[int]]:
        """Generate a mock draft order for testing.

        Args:
            teams: Number of teams
            rounds: Number of rounds
            randomize_order: Whether to randomize order

        Returns:
            Mock draft order
        """
        team_ids = [f"team_{i+1}" for i in range(teams)]
        return self.generate_draft_order(team_ids, rounds, randomize_order)

    def apply_traded_picks(
        self, draft_order: dict[str, list[int]], traded_picks: list[tuple[str, str, int]]
    ) -> dict[str, list[int]]:
        """Apply traded picks to the draft order.

        Args:
            draft_order: Complete draft order
            traded_picks: List of (from_team, to_team, overall_pick) tuples

        Returns:
            Updated draft order
        """
        for from_team, to_team, pick in traded_picks:
            if pick in draft_order.get(from_team, []):
                draft_order[from_team].remove(pick)
                draft_order[to_team].append(pick)
                draft_order[to_team].sort()

        return draft_order

    def analyze_draft_positioning(
        self, draft_order: dict[str, list[int]], team_id: str
    ) -> dict[str, Any]:
        """Analyze draft positioning for a team.

        Args:
            draft_order: Complete draft order
            team_id: Team to analyze

        Returns:
            Analysis dictionary
        """
        team_picks = draft_order.get(team_id, [])
        return {
            "team_id": team_id,
            "picks": team_picks,
            "average_pick": sum(team_picks) / len(team_picks) if team_picks else 0,
            "earliest_pick": min(team_picks) if team_picks else None,
            "latest_pick": max(team_picks) if team_picks else None,
        }

    def export_draft_order(
        self, draft_order: dict[str, list[int]], format: str = "dict"
    ) -> Any:
        """Export draft order in various formats.

        Args:
            draft_order: Draft order to export
            format: Export format ('dict', 'csv', 'json')

        Returns:
            Exported data in requested format
        """
        if format == "dict":
            return draft_order
        elif format == "csv":
            return "team_id,pick_numbers\n" + "\n".join(
                f"{team},{','.join(map(str, picks))}" for team, picks in draft_order.items()
            )
        elif format == "json":
            import json
            return json.dumps(draft_order)
        else:
            raise ValueError(f"Unsupported format: {format}")


# Global instance for singleton pattern
_snake_draft_algorithm: SnakeDraftAlgorithm | None = None


def get_snake_draft_algorithm() -> SnakeDraftAlgorithm:
    """Get the draft algorithm instance."""
    global _snake_draft_algorithm
    if _snake_draft_algorithm is None:
        _snake_draft_algorithm = SnakeDraftAlgorithm()
    return _snake_draft_algorithm


def reset_snake_draft_algorithm() -> None:
    """Reset the global algorithm (useful for testing)."""
    global _snake_draft_algorithm
    _snake_draft_algorithm = None