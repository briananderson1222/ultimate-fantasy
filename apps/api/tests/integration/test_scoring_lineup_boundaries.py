"""Integration tests for scoring-lineup domain boundaries."""
import pytest
from domains.shared.interfaces.scoring_service import ScoringServiceInterface
from domains.shared.interfaces.lineup_service import LineupServiceInterface

class TestScoringLineupBoundaries:
    @pytest.fixture
    def scoring_service(self) -> ScoringServiceInterface:
        from domains.scoring.services.scoring_service import ScoringService
        return ScoringService()

    @pytest.fixture
    def lineup_service(self) -> LineupServiceInterface:
        from domains.lineups.services.lineup_service import LineupService
        return LineupService()

    @pytest.mark.asyncio
    async def test_score_calculation_for_valid_lineup(self, scoring_service, lineup_service):
        """Test that scores can only be calculated for valid lineups."""
        lineup_id = "test-lineup-123"
        period = "week-1"

        lineup = await lineup_service.get_lineup(lineup_id)
        score = await scoring_service.calculate_lineup_score(lineup_id, period)

        assert score.lineup_id == lineup.id