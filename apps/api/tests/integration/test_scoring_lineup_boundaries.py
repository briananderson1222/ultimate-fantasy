"""Integration tests for scoring-lineup domain boundaries."""

import pytest

from domains.shared.interfaces.lineup_service import LineupServiceInterface
from domains.shared.interfaces.scoring_service import ScoringServiceInterface


class TestScoringLineupBoundaries:
    # Use the scoring_service and lineup_service fixtures from conftest.py

    @pytest.mark.asyncio
    async def test_score_calculation_for_valid_lineup(
        self, scoring_service, lineup_service
    ):
        """Test that scores can only be calculated for valid lineups."""
        lineup_id = "123e4567-e89b-12d3-a456-426614174000"
        period = "week-1"

        lineup = await lineup_service.get_lineup(lineup_id)
        score = await scoring_service.calculate_lineup_score(lineup_id, period)

        assert score.lineup_id == lineup.id
