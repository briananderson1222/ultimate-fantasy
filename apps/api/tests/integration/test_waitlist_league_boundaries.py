"""Integration tests for waitlist-league domain boundaries."""

import pytest

from domains.shared.interfaces.league_service import LeagueServiceInterface
from domains.shared.interfaces.waitlist_service import WaitlistServiceInterface


class TestWaitlistLeagueBoundaries:
    # Use the waitlist_service and league_service fixtures from conftest.py

    @pytest.mark.asyncio
    async def test_waitlist_for_valid_league_only(
        self, waitlist_service, league_service
    ):
        """Test that users can only join waitlists for valid leagues."""
        user_id = "6ba7b811-9dad-11d1-80b4-00c04fd430c8"
        league_id = "6ba7b812-9dad-11d1-80b4-00c04fd430c8"

        # Should validate league exists before adding to waitlist
        league_settings = await league_service.get_league_settings(league_id)
        entry = await waitlist_service.add_to_waitlist(user_id, league_id)

        assert entry.league_id == league_id
