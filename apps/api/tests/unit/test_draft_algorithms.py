"""
Unit tests for draft algorithms and draft management logic.

Tests cover:
- Snake draft order calculation
- Auto-draft algorithm
- Draft timer and timeout handling
- Pick validation and constraints
- Draft state management
"""

import pytest
from datetime import datetime, timedelta
from typing import List, Dict, Any
from unittest.mock import Mock, AsyncMock, patch
from dataclasses import dataclass

# Import draft algorithm components
from domains.drafts.algorithms.snake_draft import SnakeDraftAlgorithm, DraftOrder
from domains.drafts.services.draft_service import DraftService, DraftPick
from domains.drafts.services.draft_timer import DraftTimer, TimerState
from domains.drafts.models.draft import Draft, DraftStatus
from domains.leagues.models.league import League
from domains.leagues.models.team import Team
from domains.sports.models.player import Player


@dataclass
class MockTeam:
    """Mock team for testing."""

    id: str
    name: str
    owner_id: str
    draft_position: int


@dataclass
class MockPlayer:
    """Mock player for testing."""

    id: str
    name: str
    position: str
    team: str
    overall_rank: int
    position_rank: int


class TestSnakeDraftAlgorithm:
    """Test the snake draft order calculation algorithm."""

    def setup_method(self):
        """Set up test fixtures."""
        self.algorithm = SnakeDraftAlgorithm()

        # Create mock teams
        self.teams = ["team1", "team2", "team3", "team4"]

    def test_generate_snake_order_round_1(self):
        """Test snake draft order for round 1 (normal order)."""
        draft_order = self.algorithm.generate_draft_order(self.teams, total_rounds=3)

        round_1_picks = [pick for pick in draft_order.picks if pick.round_number == 1]

        assert len(round_1_picks) == 4
        assert round_1_picks[0].team_id == "team1"
        assert round_1_picks[1].team_id == "team2"
        assert round_1_picks[2].team_id == "team3"
        assert round_1_picks[3].team_id == "team4"

        # Check pick numbers
        assert round_1_picks[0].overall_pick == 1
        assert round_1_picks[1].overall_pick == 2
        assert round_1_picks[2].overall_pick == 3
        assert round_1_picks[3].overall_pick == 4

    def test_generate_snake_order_round_2(self):
        """Test snake draft order for round 2 (reversed order)."""
        draft_order = self.algorithm.generate_draft_order(self.teams, total_rounds=3)

        round_2_picks = [pick for pick in draft_order.picks if pick.round == 2]

        assert len(round_2_picks) == 4
        assert round_2_picks[0].team_id == "team4"  # Reversed
        assert round_2_picks[1].team_id == "team3"
        assert round_2_picks[2].team_id == "team2"
        assert round_2_picks[3].team_id == "team1"

        # Check pick numbers continue sequentially
        assert round_2_picks[0].pick_number == 5
        assert round_2_picks[1].pick_number == 6
        assert round_2_picks[2].pick_number == 7
        assert round_2_picks[3].pick_number == 8

    def test_generate_snake_order_round_3(self):
        """Test snake draft order for round 3 (back to normal order)."""
        draft_order = self.algorithm.generate_draft_order(self.teams, total_rounds=3)

        round_3_picks = [pick for pick in draft_order.picks if pick.round == 3]

        assert len(round_3_picks) == 4
        assert round_3_picks[0].team_id == "team1"  # Back to normal
        assert round_3_picks[1].team_id == "team2"
        assert round_3_picks[2].team_id == "team3"
        assert round_3_picks[3].team_id == "team4"

    def test_generate_draft_order_total_picks(self):
        """Test total number of picks generated."""
        draft_order = self.algorithm.generate_draft_order(self.teams, total_rounds=15)

        expected_total = len(self.teams) * 15
        assert len(draft_order.picks) == expected_total

    def test_find_current_pick(self):
        """Test finding the current pick in draft order."""
        draft_order = self.algorithm.generate_draft_order(self.teams, total_rounds=3)

        # No picks made yet - should be pick 1
        current_pick = self.algorithm.get_current_pick(draft_order, [])
        assert current_pick.overall_pick == 1
        assert current_pick.team_id == "team1"

    def test_find_current_pick_after_picks(self):
        """Test finding current pick after some picks have been made."""
        draft_order = self.algorithm.generate_draft_order(self.teams, total_rounds=3)

        # Simulate 3 picks made
        completed_picks = [
            DraftPick(pick_number=1, team_id="team1", player_id="player1"),
            DraftPick(pick_number=2, team_id="team2", player_id="player2"),
            DraftPick(pick_number=3, team_id="team3", player_id="player3"),
        ]

        current_pick = self.algorithm.find_current_pick(draft_order, completed_picks)
        assert current_pick.pick_number == 4
        assert current_pick.team_id == "team4"

    def test_get_team_next_pick(self):
        """Test getting a specific team's next pick."""
        draft_order = self.algorithm.generate_draft_order(self.teams, total_rounds=3)

        # Team 3's first pick should be pick 3
        next_pick = self.algorithm.get_team_next_pick(draft_order, "team3", [])
        assert next_pick.pick_number == 3
        assert next_pick.team_id == "team3"
        assert next_pick.round == 1

    def test_get_team_next_pick_after_round_1(self):
        """Test getting team's next pick after round 1 is complete."""
        draft_order = self.algorithm.generate_draft_order(self.teams, total_rounds=3)

        # Simulate round 1 complete
        completed_picks = [
            DraftPick(pick_number=i + 1, team_id=f"team{i+1}", player_id=f"player{i+1}")
            for i in range(4)
        ]

        # Team 3's next pick should be pick 6 (round 2, position 2 in snake)
        next_pick = self.algorithm.get_team_next_pick(
            draft_order, "team3", completed_picks
        )
        assert next_pick.pick_number == 6
        assert next_pick.team_id == "team3"
        assert next_pick.round == 2

    def test_validate_pick_order(self):
        """Test validation of pick order."""
        draft_order = self.algorithm.generate_draft_order(self.teams, total_rounds=3)

        # Valid pick (team1 picking first)
        assert self.algorithm.validate_pick_order(draft_order, [], "team1")

        # Invalid pick (team2 trying to pick first)
        assert not self.algorithm.validate_pick_order(draft_order, [], "team2")

    def test_calculate_draft_position_value(self):
        """Test calculation of draft position value."""
        # Earlier picks should have higher value
        value_1 = self.algorithm.calculate_pick_value(1, 12)  # 1st overall in 12-team
        value_12 = self.algorithm.calculate_pick_value(12, 12)  # 12th overall
        value_13 = self.algorithm.calculate_pick_value(13, 12)  # 1st pick round 2

        assert value_1 > value_12
        assert value_12 > value_13  # Snake draft makes this pick valuable


class TestAutoDraftAlgorithm:
    """Test the auto-draft algorithm for automated player selection."""

    def setup_method(self):
        """Set up test fixtures."""
        self.algorithm = SnakeDraftAlgorithm()

        # Create mock available players
        self.available_players = [
            MockPlayer("p1", "Player 1", "QB", "SF", 1, 1),
            MockPlayer("p2", "Player 2", "RB", "DAL", 2, 1),
            MockPlayer("p3", "Player 3", "WR", "GB", 3, 1),
            MockPlayer("p4", "Player 4", "QB", "KC", 4, 2),
            MockPlayer("p5", "Player 5", "RB", "CMC", 5, 2),
        ]

        # Mock team with current roster
        self.team_roster = {"QB": 0, "RB": 0, "WR": 0, "TE": 0, "K": 0, "DEF": 0}

    def test_auto_draft_best_available(self):
        """Test auto-draft selects best available player."""
        pick = self.algorithm.auto_draft_pick(
            self.available_players, self.team_roster, strategy="best_available"
        )

        # Should pick highest overall ranked available player
        assert pick.player_id == "p1"
        assert pick.player_name == "Player 1"

    def test_auto_draft_positional_need(self):
        """Test auto-draft considers positional needs."""
        # Team already has QB, should prioritize other positions
        roster_with_qb = self.team_roster.copy()
        roster_with_qb["QB"] = 1

        pick = self.algorithm.auto_draft_pick(
            self.available_players, roster_with_qb, strategy="positional_need"
        )

        # Should skip QB and pick best RB
        assert pick.player_id == "p2"
        assert pick.player_name == "Player 2"

    def test_auto_draft_balanced_approach(self):
        """Test auto-draft with balanced approach strategy."""
        pick = self.algorithm.auto_draft_pick(
            self.available_players, self.team_roster, strategy="balanced"
        )

        # Should consider both value and need
        assert pick.player_id in ["p1", "p2", "p3"]

    def test_auto_draft_no_available_players(self):
        """Test auto-draft when no players are available."""
        pick = self.algorithm.auto_draft_pick(
            [], self.team_roster, strategy="best_available"
        )

        assert pick is None

    def test_auto_draft_position_requirements(self):
        """Test auto-draft respects position requirements."""
        # Mock league settings requiring minimum positions
        position_requirements = {
            "QB": {"min": 1, "max": 2},
            "RB": {"min": 2, "max": 4},
            "WR": {"min": 3, "max": 6},
            "TE": {"min": 1, "max": 2},
            "K": {"min": 1, "max": 1},
            "DEF": {"min": 1, "max": 1},
        }

        # Team needs QB (required position)
        empty_roster = {pos: 0 for pos in position_requirements.keys()}

        pick = self.algorithm.auto_draft_pick(
            self.available_players,
            empty_roster,
            strategy="positional_need",
            position_requirements=position_requirements,
        )

        # Should prioritize required position
        assert pick.player_id == "p1"  # Best QB available


class TestDraftTimer:
    """Test draft timer functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.timer = DraftTimer()

    @pytest.mark.asyncio
    async def test_start_timer(self):
        """Test starting the draft timer."""
        duration = 60  # 60 seconds

        await self.timer.start_timer("team1", duration)

        assert self.timer.state == TimerState.RUNNING
        assert self.timer.current_team == "team1"
        assert self.timer.remaining_time <= duration

    @pytest.mark.asyncio
    async def test_timer_expiration(self):
        """Test timer expiration and auto-draft."""
        duration = 1  # 1 second for quick test

        # Mock auto-draft callback
        auto_draft_called = False

        async def mock_auto_draft(team_id):
            nonlocal auto_draft_called
            auto_draft_called = True
            return MockPlayer("auto", "Auto Pick", "QB", "SF", 1, 1)

        self.timer.set_auto_draft_callback(mock_auto_draft)

        await self.timer.start_timer("team1", duration)

        # Wait for timer to expire
        import asyncio

        await asyncio.sleep(1.1)

        assert self.timer.state == TimerState.EXPIRED
        assert auto_draft_called

    @pytest.mark.asyncio
    async def test_pause_timer(self):
        """Test pausing the draft timer."""
        await self.timer.start_timer("team1", 60)
        initial_time = self.timer.remaining_time

        await self.timer.pause()

        assert self.timer.state == TimerState.PAUSED

        # Wait a bit and check time didn't decrease
        import asyncio

        await asyncio.sleep(0.5)

        assert self.timer.remaining_time == initial_time

    @pytest.mark.asyncio
    async def test_resume_timer(self):
        """Test resuming a paused timer."""
        await self.timer.start_timer("team1", 60)
        await self.timer.pause()

        await self.timer.resume()

        assert self.timer.state == TimerState.RUNNING

    @pytest.mark.asyncio
    async def test_reset_timer(self):
        """Test resetting the timer."""
        await self.timer.start_timer("team1", 60)

        await self.timer.reset()

        assert self.timer.state == TimerState.STOPPED
        assert self.timer.current_team is None
        assert self.timer.remaining_time == 0

    def test_get_timer_status(self):
        """Test getting timer status."""
        status = self.timer.get_status()

        assert "state" in status
        assert "remaining_time" in status
        assert "current_team" in status


class TestDraftService:
    """Test the main draft service functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.draft_service = DraftService()

        # Mock dependencies
        self.mock_league = Mock(spec=League)
        self.mock_league.id = "league1"
        self.mock_league.draft_settings = {
            "rounds": 15,
            "pick_time_limit": 90,
            "auto_draft_enabled": True,
        }

    @pytest.mark.asyncio
    async def test_create_draft(self):
        """Test creating a new draft."""
        teams = [
            {"id": "team1", "name": "Team 1", "owner_id": "user1"},
            {"id": "team2", "name": "Team 2", "owner_id": "user2"},
        ]

        with patch.object(self.draft_service, "_create_draft_order") as mock_order:
            mock_order.return_value = Mock()

            draft = await self.draft_service.create_draft(self.mock_league.id, teams)

            assert draft.league_id == self.mock_league.id
            assert draft.status == DraftStatus.CREATED
            assert len(draft.teams) == 2

    @pytest.mark.asyncio
    async def test_start_draft(self):
        """Test starting a draft."""
        draft_id = "draft1"

        with patch.object(self.draft_service, "_get_draft") as mock_get:
            mock_draft = Mock(spec=Draft)
            mock_draft.status = DraftStatus.CREATED
            mock_get.return_value = mock_draft

            with patch.object(
                self.draft_service, "_start_first_pick_timer"
            ) as mock_timer:
                await self.draft_service.start_draft(draft_id)

                assert mock_draft.status == DraftStatus.IN_PROGRESS
                mock_timer.assert_called_once()

    @pytest.mark.asyncio
    async def test_make_pick_valid(self):
        """Test making a valid draft pick."""
        draft_id = "draft1"
        team_id = "team1"
        player_id = "player1"

        with patch.object(self.draft_service, "_validate_pick") as mock_validate:
            mock_validate.return_value = True

            with patch.object(self.draft_service, "_is_team_turn") as mock_turn:
                mock_turn.return_value = True

                with patch.object(self.draft_service, "_record_pick") as mock_record:
                    result = await self.draft_service.make_pick(
                        draft_id, team_id, player_id
                    )

                    assert result.success
                    mock_record.assert_called_once()

    @pytest.mark.asyncio
    async def test_make_pick_invalid_turn(self):
        """Test making a pick when it's not the team's turn."""
        draft_id = "draft1"
        team_id = "team1"
        player_id = "player1"

        with patch.object(self.draft_service, "_is_team_turn") as mock_turn:
            mock_turn.return_value = False

            result = await self.draft_service.make_pick(draft_id, team_id, player_id)

            assert not result.success
            assert "turn" in result.error.lower()

    @pytest.mark.asyncio
    async def test_make_pick_player_unavailable(self):
        """Test making a pick for an unavailable player."""
        draft_id = "draft1"
        team_id = "team1"
        player_id = "player1"

        with patch.object(self.draft_service, "_is_team_turn") as mock_turn:
            mock_turn.return_value = True

            with patch.object(self.draft_service, "_validate_pick") as mock_validate:
                mock_validate.return_value = False

                result = await self.draft_service.make_pick(
                    draft_id, team_id, player_id
                )

                assert not result.success
                assert "available" in result.error.lower()

    @pytest.mark.asyncio
    async def test_get_available_players(self):
        """Test getting available players for draft."""
        draft_id = "draft1"

        with patch.object(self.draft_service, "_get_drafted_players") as mock_drafted:
            mock_drafted.return_value = {"player1", "player2"}

            with patch.object(self.draft_service, "_get_all_players") as mock_all:
                mock_all.return_value = [
                    MockPlayer("player1", "P1", "QB", "SF", 1, 1),
                    MockPlayer("player2", "P2", "RB", "DAL", 2, 1),
                    MockPlayer("player3", "P3", "WR", "GB", 3, 1),
                ]

                available = await self.draft_service.get_available_players(draft_id)

                # Should only return player3 (not drafted)
                assert len(available) == 1
                assert available[0].id == "player3"

    @pytest.mark.asyncio
    async def test_get_draft_status(self):
        """Test getting current draft status."""
        draft_id = "draft1"

        with patch.object(self.draft_service, "_get_draft") as mock_get:
            mock_draft = Mock(spec=Draft)
            mock_draft.status = DraftStatus.IN_PROGRESS
            mock_draft.current_pick = 5
            mock_draft.total_picks = 30
            mock_get.return_value = mock_draft

            status = await self.draft_service.get_draft_status(draft_id)

            assert status["status"] == DraftStatus.IN_PROGRESS
            assert status["current_pick"] == 5
            assert status["total_picks"] == 30
            assert status["progress_percentage"] == pytest.approx(16.67, rel=1e-2)

    @pytest.mark.asyncio
    async def test_complete_draft(self):
        """Test completing a draft when all picks are made."""
        draft_id = "draft1"

        with patch.object(self.draft_service, "_get_draft") as mock_get:
            mock_draft = Mock(spec=Draft)
            mock_draft.total_picks = 30
            mock_draft.completed_picks = 30
            mock_get.return_value = mock_draft

            with patch.object(self.draft_service, "_finalize_draft") as mock_finalize:
                await self.draft_service._check_draft_completion(draft_id)

                mock_finalize.assert_called_once()


class TestDraftValidation:
    """Test draft validation logic."""

    def setup_method(self):
        """Set up test fixtures."""
        self.draft_service = DraftService()

    def test_validate_pick_available_player(self):
        """Test validation passes for available player."""
        available_players = ["player1", "player2", "player3"]

        result = self.draft_service._validate_player_availability(
            "player2", available_players
        )

        assert result

    def test_validate_pick_unavailable_player(self):
        """Test validation fails for unavailable player."""
        available_players = ["player1", "player2", "player3"]

        result = self.draft_service._validate_player_availability(
            "player4", available_players
        )

        assert not result

    def test_validate_roster_constraints(self):
        """Test validation of roster constraints."""
        current_roster = {"QB": 1, "RB": 2, "WR": 1}
        max_positions = {"QB": 2, "RB": 4, "WR": 6}

        # Adding another QB should be valid
        result = self.draft_service._validate_roster_constraints(
            current_roster, "QB", max_positions
        )
        assert result

        # Adding third QB when max is 2 should be invalid
        current_roster["QB"] = 2
        result = self.draft_service._validate_roster_constraints(
            current_roster, "QB", max_positions
        )
        assert not result


class TestDraftPerformance:
    """Test draft algorithm performance."""

    def setup_method(self):
        """Set up test fixtures."""
        self.algorithm = SnakeDraftAlgorithm()

    def test_large_league_draft_order_performance(self):
        """Test performance with large league (20 teams, 20 rounds)."""
        import time

        # Create 20 teams
        teams = [MockTeam(f"team{i}", f"Team {i}", f"user{i}", i) for i in range(1, 21)]

        start_time = time.time()

        draft_order = self.algorithm.generate_draft_order(teams, total_rounds=20)

        end_time = time.time()
        generation_time = end_time - start_time

        # Should generate 400 picks quickly
        assert len(draft_order.picks) == 400
        assert generation_time < 0.1  # Under 100ms

    def test_current_pick_lookup_performance(self):
        """Test performance of finding current pick in large draft."""
        import time

        teams = [MockTeam(f"team{i}", f"Team {i}", f"user{i}", i) for i in range(1, 13)]
        draft_order = self.algorithm.generate_draft_order(teams, total_rounds=15)

        # Simulate 100 completed picks
        completed_picks = [
            DraftPick(
                pick_number=i + 1,
                team_id=f"team{(i % 12) + 1}",
                player_id=f"player{i+1}",
            )
            for i in range(100)
        ]

        start_time = time.time()

        current_pick = self.algorithm.find_current_pick(draft_order, completed_picks)

        end_time = time.time()
        lookup_time = end_time - start_time

        assert current_pick.pick_number == 101
        assert lookup_time < 0.01  # Under 10ms
