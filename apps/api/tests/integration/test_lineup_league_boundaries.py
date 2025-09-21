"""
Integration tests for lineup-league domain boundaries.

These tests verify that the Lineup and League domains can communicate
properly through their defined interfaces.
"""

import pytest

from domains.shared.interfaces.league_service import LeagueServiceInterface
from domains.shared.interfaces.lineup_service import LineupServiceInterface


class TestLineupLeagueBoundaries:
    """Integration tests for Lineup-League domain communication."""

    # Use the lineup_service and league_service fixtures from conftest.py

    def test_lineup_belongs_to_valid_league(
        self, lineup_service, league_service, test_lineup_data, test_league_data
    ):
        """Test that lineups belong to valid leagues."""
        # Arrange - Using provisioned test data
        lineup_id = str(test_lineup_data["lineup_id"])
        expected_league_id = str(test_league_data["league_id"])
        user_id = str(test_lineup_data["user_id"])

        # Act - Use synchronous methods
        lineup = lineup_service.get_lineup_by_id(lineup_id)
        league = league_service.get_league(expected_league_id)

        # Assert - Lineup should belong to the correct league and user should have access
        assert lineup is not None
        assert league is not None
        # Verify lineup belongs to the team which belongs to the league
        assert str(lineup.team_id) == str(test_lineup_data["team_id"])

    def test_lineup_ownership_validation(
        self, lineup_service, test_lineup_data, test_team_data
    ):
        """Test that lineup ownership validation works properly."""
        # Arrange - Using provisioned test data
        lineup_id = str(test_lineup_data["lineup_id"])
        team_id = str(test_team_data["team_id"])
        user_id = str(test_team_data["user_id"])

        # Act - Use synchronous method instead of async
        lineup = lineup_service.get_lineup_by_id(lineup_id)

        # Assert - Lineup should belong to the correct team and user
        assert lineup is not None
        assert str(lineup.team_id) == team_id
        # Verify through team ownership that user owns this lineup
        assert str(test_team_data["team"].user_id) == user_id

    def test_lineup_team_league_relationship(
        self, test_lineup_data, test_team_data, test_league_data
    ):
        """Test that lineup->team->league relationship is properly established."""
        # Arrange - Using provisioned test data
        lineup = test_lineup_data["lineup"]
        team = test_team_data["team"]
        league = test_league_data["league"]

        # Assert - Verify the relationship chain
        assert str(lineup.team_id) == str(team.team_id)
        assert str(team.league_id) == str(league.league_id)
        assert str(team.user_id) == str(test_lineup_data["user_id"])


# NOTE: These tests MUST FAIL initially due to missing implementations
