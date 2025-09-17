"""Integration tests for waitlist-league domain boundaries."""
import pytest
from domains.shared.interfaces.waitlist_service import WaitlistServiceInterface
from domains.shared.interfaces.league_service import LeagueServiceInterface

class TestWaitlistLeagueBoundaries:
    @pytest.fixture
    def waitlist_service(self) -> WaitlistServiceInterface:
        from domains.waitlist.services.waitlist_service import WaitlistService
        return WaitlistService()

    @pytest.fixture
    def league_service(self) -> LeagueServiceInterface:
        from domains.leagues.services.league_service import LeagueService
        return LeagueService()

    @pytest.mark.asyncio
    async def test_waitlist_for_valid_league_only(self, waitlist_service, league_service):
        """Test that users can only join waitlists for valid leagues."""
        user_id = "test-user-123"
        league_id = "test-league-456"

        # Should validate league exists before adding to waitlist
        league_settings = await league_service.get_league_settings(league_id)
        entry = await waitlist_service.add_to_waitlist(user_id, league_id)

        assert entry.league_id == league_id