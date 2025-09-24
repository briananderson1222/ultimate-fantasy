"""
Unit tests for sports data validation logic.

Tests cover:
- Player data validation and normalization
- Team data validation
- Schedule/game data validation
- Statistical data validation
- Error handling and edge cases
"""

import pytest
from datetime import datetime, timezone
from typing import Dict, Any, List
from unittest.mock import Mock, patch
import json

# Import the sports data validation components
from domains.sports.services.data_normalizer import DataNormalizer, ValidationError
from domains.sports.models.player import Player, PlayerPosition, InjuryStatus
from domains.sports.models.team import Team
from domains.sports.services.sports_data_service import SportsDataService, SportType


class TestPlayerDataValidation:
    """Test player data validation and normalization."""

    def setup_method(self):
        """Set up test fixtures."""
        self.normalizer = DataNormalizer()

    def test_validate_player_data_valid(self):
        """Test validation of valid player data."""
        player_data = {
            "id": "12345",
            "name": "John Smith",
            "position": "QB",
            "team": "SF",
            "sport": "nfl",
            "height": "6-3",
            "weight": 225,
            "age": 28,
            "experience": 5
        }

        result = self.normalizer.validate_player_data(player_data)

        assert result.is_valid
        assert result.normalized_data["position"] == PlayerPosition.QB
        assert result.normalized_data["team_abbreviation"] == "SF"
        assert result.normalized_data["height_inches"] == 75
        assert result.errors == []

    def test_validate_player_data_missing_required_fields(self):
        """Test validation with missing required fields."""
        player_data = {
            "name": "John Smith",
            "position": "QB"
            # Missing id, team, sport
        }

        result = self.normalizer.validate_player_data(player_data)

        assert not result.is_valid
        assert len(result.errors) >= 3
        assert any("id" in error for error in result.errors)
        assert any("team" in error for error in result.errors)
        assert any("sport" in error for error in result.errors)

    def test_validate_player_data_invalid_position(self):
        """Test validation with invalid position."""
        player_data = {
            "id": "12345",
            "name": "John Smith",
            "position": "INVALID_POS",
            "team": "SF",
            "sport": "nfl"
        }

        result = self.normalizer.validate_player_data(player_data)

        assert not result.is_valid
        assert any("position" in error.lower() for error in result.errors)

    def test_validate_player_data_invalid_sport(self):
        """Test validation with unsupported sport."""
        player_data = {
            "id": "12345",
            "name": "John Smith",
            "position": "QB",
            "team": "SF",
            "sport": "cricket"
        }

        result = self.normalizer.validate_player_data(player_data)

        assert not result.is_valid
        assert any("sport" in error.lower() for error in result.errors)

    def test_normalize_height_formats(self):
        """Test height normalization from various formats."""
        test_cases = [
            ("6-3", 75),
            ("6'3\"", 75),
            ("6 ft 3 in", 75),
            ("75", 75),
            ("1.91m", 75),  # Metric conversion
            ("191cm", 75)
        ]

        for height_input, expected_inches in test_cases:
            result = self.normalizer._normalize_height(height_input)
            assert result == expected_inches, f"Failed for input: {height_input}"

    def test_normalize_weight_formats(self):
        """Test weight normalization from various formats."""
        test_cases = [
            ("225", 225),
            ("225 lbs", 225),
            ("102kg", 225),  # Metric conversion
            ("102.1 kg", 225)
        ]

        for weight_input, expected_lbs in test_cases:
            result = self.normalizer._normalize_weight(weight_input)
            assert abs(result - expected_lbs) <= 1, f"Failed for input: {weight_input}"

    def test_validate_injury_status(self):
        """Test injury status validation."""
        valid_statuses = ["healthy", "questionable", "doubtful", "out", "ir", "suspended"]

        for status in valid_statuses:
            player_data = {
                "id": "12345",
                "name": "John Smith",
                "position": "QB",
                "team": "SF",
                "sport": "nfl",
                "injury_status": status
            }

            result = self.normalizer.validate_player_data(player_data)
            assert result.is_valid or len([e for e in result.errors if "injury" in e.lower()]) == 0

    def test_validate_player_stats(self):
        """Test player statistics validation."""
        stats_data = {
            "passing_yards": 3500,
            "passing_touchdowns": 25,
            "interceptions": 8,
            "completion_percentage": 67.5,
            "games_played": 16
        }

        result = self.normalizer.validate_player_stats(stats_data, "QB")

        assert result.is_valid
        assert result.normalized_data["completion_percentage"] == 67.5
        assert result.normalized_data["games_played"] == 16

    def test_validate_player_stats_negative_values(self):
        """Test validation rejects negative statistical values."""
        stats_data = {
            "passing_yards": -100,  # Invalid
            "passing_touchdowns": 25,
            "games_played": -1  # Invalid
        }

        result = self.normalizer.validate_player_stats(stats_data, "QB")

        assert not result.is_valid
        assert len(result.errors) >= 2


class TestTeamDataValidation:
    """Test team data validation and normalization."""

    def setup_method(self):
        """Set up test fixtures."""
        self.normalizer = DataNormalizer()

    def test_validate_team_data_valid(self):
        """Test validation of valid team data."""
        team_data = {
            "id": "sf",
            "name": "San Francisco 49ers",
            "abbreviation": "SF",
            "city": "San Francisco",
            "conference": "NFC",
            "division": "West",
            "sport": "nfl"
        }

        result = self.normalizer.validate_team_data(team_data)

        assert result.is_valid
        assert result.normalized_data["abbreviation"] == "SF"
        assert result.normalized_data["conference"] == "NFC"
        assert result.errors == []

    def test_validate_team_data_missing_fields(self):
        """Test validation with missing required fields."""
        team_data = {
            "name": "San Francisco 49ers"
            # Missing id, abbreviation, sport
        }

        result = self.normalizer.validate_team_data(team_data)

        assert not result.is_valid
        assert len(result.errors) >= 3

    def test_validate_team_abbreviation_format(self):
        """Test team abbreviation format validation."""
        test_cases = [
            ("SF", True),
            ("LAR", True),
            ("NE", True),
            ("INVALID", False),  # Too long
            ("S", False),        # Too short
            ("s f", False),      # Contains space
            ("12", False)        # Numbers only
        ]

        for abbrev, should_be_valid in test_cases:
            team_data = {
                "id": "test",
                "name": "Test Team",
                "abbreviation": abbrev,
                "sport": "nfl"
            }

            result = self.normalizer.validate_team_data(team_data)
            if should_be_valid:
                assert not any("abbreviation" in error.lower() for error in result.errors)
            else:
                assert any("abbreviation" in error.lower() for error in result.errors)


class TestScheduleDataValidation:
    """Test schedule and game data validation."""

    def setup_method(self):
        """Set up test fixtures."""
        self.normalizer = DataNormalizer()

    def test_validate_game_data_valid(self):
        """Test validation of valid game data."""
        game_data = {
            "id": "game123",
            "home_team": "SF",
            "away_team": "SEA",
            "start_time": "2024-01-15T13:00:00Z",
            "week": 1,
            "season": 2024,
            "sport": "nfl",
            "status": "scheduled"
        }

        result = self.normalizer.validate_game_data(game_data)

        assert result.is_valid
        assert isinstance(result.normalized_data["start_time"], datetime)
        assert result.normalized_data["week"] == 1
        assert result.errors == []

    def test_validate_game_data_invalid_datetime(self):
        """Test validation with invalid datetime format."""
        game_data = {
            "id": "game123",
            "home_team": "SF",
            "away_team": "SEA",
            "start_time": "invalid-datetime",
            "week": 1,
            "season": 2024,
            "sport": "nfl"
        }

        result = self.normalizer.validate_game_data(game_data)

        assert not result.is_valid
        assert any("start_time" in error.lower() for error in result.errors)

    def test_validate_game_data_same_teams(self):
        """Test validation rejects games with same home/away team."""
        game_data = {
            "id": "game123",
            "home_team": "SF",
            "away_team": "SF",  # Same as home team
            "start_time": "2024-01-15T13:00:00Z",
            "week": 1,
            "season": 2024,
            "sport": "nfl"
        }

        result = self.normalizer.validate_game_data(game_data)

        assert not result.is_valid
        assert any("team" in error.lower() for error in result.errors)

    def test_validate_game_week_bounds(self):
        """Test validation of week number bounds."""
        test_cases = [
            (1, True),
            (17, True),
            (18, True),   # Playoffs
            (0, False),   # Too low
            (25, False)   # Too high
        ]

        for week, should_be_valid in test_cases:
            game_data = {
                "id": "game123",
                "home_team": "SF",
                "away_team": "SEA",
                "start_time": "2024-01-15T13:00:00Z",
                "week": week,
                "season": 2024,
                "sport": "nfl"
            }

            result = self.normalizer.validate_game_data(game_data)
            if should_be_valid:
                assert not any("week" in error.lower() for error in result.errors)
            else:
                assert any("week" in error.lower() for error in result.errors)


class TestStatisticalDataValidation:
    """Test validation of statistical data."""

    def setup_method(self):
        """Set up test fixtures."""
        self.normalizer = DataNormalizer()

    def test_validate_passing_stats(self):
        """Test validation of passing statistics."""
        passing_stats = {
            "attempts": 35,
            "completions": 24,
            "yards": 312,
            "touchdowns": 2,
            "interceptions": 1,
            "rating": 98.5
        }

        result = self.normalizer.validate_passing_stats(passing_stats)

        assert result.is_valid
        assert result.normalized_data["completion_percentage"] == pytest.approx(68.57, rel=1e-2)
        assert result.errors == []

    def test_validate_passing_stats_invalid_completion_ratio(self):
        """Test validation rejects impossible completion ratios."""
        passing_stats = {
            "attempts": 20,
            "completions": 25,  # More completions than attempts
            "yards": 312,
            "touchdowns": 2,
            "interceptions": 1
        }

        result = self.normalizer.validate_passing_stats(passing_stats)

        assert not result.is_valid
        assert any("completion" in error.lower() for error in result.errors)

    def test_validate_rushing_stats(self):
        """Test validation of rushing statistics."""
        rushing_stats = {
            "attempts": 22,
            "yards": 145,
            "touchdowns": 1,
            "fumbles": 0,
            "long": 24
        }

        result = self.normalizer.validate_rushing_stats(rushing_stats)

        assert result.is_valid
        assert result.normalized_data["yards_per_attempt"] == pytest.approx(6.59, rel=1e-2)

    def test_validate_receiving_stats(self):
        """Test validation of receiving statistics."""
        receiving_stats = {
            "targets": 12,
            "receptions": 8,
            "yards": 156,
            "touchdowns": 2,
            "drops": 1,
            "long": 45
        }

        result = self.normalizer.validate_receiving_stats(receiving_stats)

        assert result.is_valid
        assert result.normalized_data["catch_percentage"] == pytest.approx(66.67, rel=1e-2)
        assert result.normalized_data["yards_per_reception"] == pytest.approx(19.5, rel=1e-2)


class TestErrorHandlingAndEdgeCases:
    """Test error handling and edge cases in validation."""

    def setup_method(self):
        """Set up test fixtures."""
        self.normalizer = DataNormalizer()

    def test_handle_null_data(self):
        """Test handling of null/None data."""
        result = self.normalizer.validate_player_data(None)

        assert not result.is_valid
        assert any("data" in error.lower() for error in result.errors)

    def test_handle_empty_data(self):
        """Test handling of empty data."""
        result = self.normalizer.validate_player_data({})

        assert not result.is_valid
        assert len(result.errors) > 0

    def test_handle_malformed_json_data(self):
        """Test handling of malformed JSON data."""
        with pytest.raises(ValidationError):
            self.normalizer.validate_player_data("not valid json")

    def test_handle_unexpected_data_types(self):
        """Test handling of unexpected data types."""
        player_data = {
            "id": 12345,  # Should be string
            "name": ["John", "Smith"],  # Should be string
            "position": None,  # Should be string
            "team": "SF",
            "sport": "nfl"
        }

        result = self.normalizer.validate_player_data(player_data)

        assert not result.is_valid
        assert len(result.errors) >= 3

    def test_handle_extreme_values(self):
        """Test handling of extreme statistical values."""
        stats_data = {
            "passing_yards": 99999,  # Extremely high
            "completion_percentage": 150,  # Over 100%
            "games_played": 100  # Too many games
        }

        result = self.normalizer.validate_player_stats(stats_data, "QB")

        assert not result.is_valid
        assert len(result.errors) >= 2

    def test_handle_unicode_names(self):
        """Test handling of unicode characters in names."""
        player_data = {
            "id": "12345",
            "name": "José Rodríguez-Martínez",
            "position": "QB",
            "team": "SF",
            "sport": "nfl"
        }

        result = self.normalizer.validate_player_data(player_data)

        assert result.is_valid
        assert result.normalized_data["name"] == "José Rodríguez-Martínez"

    def test_validate_data_consistency(self):
        """Test cross-field data consistency validation."""
        # Test that injury status is consistent with game participation
        player_data = {
            "id": "12345",
            "name": "John Smith",
            "position": "QB",
            "team": "SF",
            "sport": "nfl",
            "injury_status": "out",
            "games_played": 16  # Inconsistent with being out
        }

        result = self.normalizer.validate_player_data(player_data)

        # Should warn about inconsistency (may not fail validation but should note it)
        assert "warning" in str(result.warnings).lower() or not result.is_valid


class TestSportsDataServiceValidation:
    """Test validation within SportsDataService."""

    def setup_method(self):
        """Set up test fixtures."""
        self.service = SportsDataService()

    @pytest.mark.asyncio
    async def test_validate_search_parameters(self):
        """Test validation of search parameters."""
        # Valid search parameters
        valid_params = {
            "sport": SportType.NFL,
            "position": "QB",
            "team": "SF",
            "limit": 20,
            "offset": 0
        }

        # Should not raise exception
        await self.service.search_players(**valid_params)

    @pytest.mark.asyncio
    async def test_reject_invalid_search_parameters(self):
        """Test rejection of invalid search parameters."""
        invalid_params = {
            "sport": "invalid_sport",
            "position": "INVALID_POS",
            "limit": -1,  # Negative limit
            "offset": -5   # Negative offset
        }

        with pytest.raises(ValidationError):
            await self.service.search_players(**invalid_params)

    @pytest.mark.asyncio
    async def test_validate_pagination_bounds(self):
        """Test validation of pagination parameters."""
        # Test maximum limit enforcement
        with pytest.raises(ValidationError):
            await self.service.search_players(
                sport=SportType.NFL,
                limit=1000  # Exceeds maximum
            )

        # Test reasonable offset
        with pytest.raises(ValidationError):
            await self.service.search_players(
                sport=SportType.NFL,
                offset=100000  # Unreasonably high
            )


@pytest.fixture
def sample_player_data():
    """Fixture providing sample player data for tests."""
    return {
        "id": "12345",
        "name": "John Smith",
        "position": "QB",
        "team": "SF",
        "sport": "nfl",
        "height": "6-3",
        "weight": 225,
        "age": 28,
        "experience": 5,
        "injury_status": "healthy"
    }


@pytest.fixture
def sample_team_data():
    """Fixture providing sample team data for tests."""
    return {
        "id": "sf",
        "name": "San Francisco 49ers",
        "abbreviation": "SF",
        "city": "San Francisco",
        "conference": "NFC",
        "division": "West",
        "sport": "nfl"
    }


@pytest.fixture
def sample_game_data():
    """Fixture providing sample game data for tests."""
    return {
        "id": "game123",
        "home_team": "SF",
        "away_team": "SEA",
        "start_time": "2024-01-15T13:00:00Z",
        "week": 1,
        "season": 2024,
        "sport": "nfl",
        "status": "scheduled"
    }


# Performance tests for validation
class TestValidationPerformance:
    """Test performance of validation operations."""

    def setup_method(self):
        """Set up test fixtures."""
        self.normalizer = DataNormalizer()

    def test_validate_large_player_dataset(self):
        """Test validation performance with large player dataset."""
        import time

        # Generate 1000 player records
        players = []
        for i in range(1000):
            players.append({
                "id": f"player_{i}",
                "name": f"Player {i}",
                "position": "QB",
                "team": "SF",
                "sport": "nfl",
                "height": "6-3",
                "weight": 225
            })

        start_time = time.time()

        valid_count = 0
        for player in players:
            result = self.normalizer.validate_player_data(player)
            if result.is_valid:
                valid_count += 1

        end_time = time.time()
        validation_time = end_time - start_time

        # Should validate 1000 players in under 1 second
        assert validation_time < 1.0
        assert valid_count == 1000

    def test_validate_complex_stats_performance(self):
        """Test validation performance with complex statistical data."""
        import time

        complex_stats = {
            "passing": {
                "attempts": 35, "completions": 24, "yards": 312,
                "touchdowns": 2, "interceptions": 1, "rating": 98.5
            },
            "rushing": {
                "attempts": 5, "yards": 23, "touchdowns": 0
            },
            "receiving": {
                "targets": 0, "receptions": 0, "yards": 0
            },
            "defense": {
                "tackles": 0, "sacks": 0, "interceptions": 0
            }
        }

        start_time = time.time()

        # Validate the same complex stats 100 times
        for _ in range(100):
            self.normalizer.validate_comprehensive_stats(complex_stats, "QB")

        end_time = time.time()
        validation_time = end_time - start_time

        # Should complete in under 100ms
        assert validation_time < 0.1