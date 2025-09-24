"""
Unit tests for trade evaluation algorithms and trade management logic.

Tests cover:
- Trade fairness evaluation
- Value calculation algorithms
- Trade validation and constraints
- Multi-team trade scenarios
- Trade timeline and expiration
"""

import pytest
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from unittest.mock import Mock, patch
from dataclasses import dataclass
from decimal import Decimal

# Import trade evaluation components
from domains.trading.algorithms.trade_evaluator import (
    TradeEvaluator, TradeAnalysis, FairnessRating, TradeRecommendation
)
from domains.trading.services.enhanced_trade_service import EnhancedTradeService
from models.trade import Trade, TradeStatus, TradeParticipant
from models.player import Player, PlayerPosition
from models.team import Team
from models.league import League


@dataclass
class MockPlayer:
    """Mock player for testing."""
    id: str
    name: str
    position: PlayerPosition
    team: str
    fantasy_points_avg: float
    season_projection: float
    injury_risk: float
    consistency_score: float
    trend: str  # "up", "down", "stable"


@dataclass
class MockTeam:
    """Mock team for testing."""
    id: str
    name: str
    owner_id: str
    current_record: Dict[str, int]
    playoff_odds: float
    needs: List[str]  # Position needs


class TestTradeEvaluator:
    """Test the core trade evaluation algorithm."""

    def setup_method(self):
        """Set up test fixtures."""
        self.evaluator = TradeEvaluator()

        # Create mock players with different values
        self.players = {
            "elite_qb": MockPlayer(
                "p1", "Elite QB", PlayerPosition.QB, "KC",
                fantasy_points_avg=25.5, season_projection=408.0,
                injury_risk=0.1, consistency_score=0.9, trend="stable"
            ),
            "good_rb": MockPlayer(
                "p2", "Good RB", PlayerPosition.RB, "SF",
                fantasy_points_avg=18.2, season_projection=291.2,
                injury_risk=0.3, consistency_score=0.7, trend="up"
            ),
            "wr1": MockPlayer(
                "p3", "WR1", PlayerPosition.WR, "BUF",
                fantasy_points_avg=16.8, season_projection=268.8,
                injury_risk=0.2, consistency_score=0.8, trend="stable"
            ),
            "aging_rb": MockPlayer(
                "p4", "Aging RB", PlayerPosition.RB, "TB",
                fantasy_points_avg=14.5, season_projection=232.0,
                injury_risk=0.5, consistency_score=0.6, trend="down"
            ),
            "boom_bust_wr": MockPlayer(
                "p5", "Boom/Bust WR", PlayerPosition.WR, "MIA",
                fantasy_points_avg=13.2, season_projection=211.2,
                injury_risk=0.2, consistency_score=0.4, trend="up"
            )
        }

        # Create mock teams
        self.teams = {
            "contender": MockTeam(
                "team1", "Contender", "user1",
                current_record={"wins": 8, "losses": 2},
                playoff_odds=0.95,
                needs=["RB"]
            ),
            "rebuilding": MockTeam(
                "team2", "Rebuilding", "user2",
                current_record={"wins": 3, "losses": 7},
                playoff_odds=0.05,
                needs=["QB", "WR"]
            )
        }

    def test_calculate_player_value_elite_player(self):
        """Test value calculation for elite player."""
        player = self.players["elite_qb"]

        value = self.evaluator.calculate_player_value(player)

        # Elite QB should have high value
        assert value > 80.0
        assert isinstance(value, float)

    def test_calculate_player_value_aging_player(self):
        """Test value calculation accounts for age/trend."""
        aging_player = self.players["aging_rb"]
        good_player = self.players["good_rb"]

        aging_value = self.evaluator.calculate_player_value(aging_player)
        good_value = self.evaluator.calculate_player_value(good_player)

        # Aging player should have lower value despite similar stats
        assert aging_value < good_value

    def test_calculate_player_value_injury_risk(self):
        """Test value calculation accounts for injury risk."""
        low_risk = MockPlayer(
            "safe", "Safe Player", PlayerPosition.RB, "GB",
            fantasy_points_avg=15.0, season_projection=240.0,
            injury_risk=0.1, consistency_score=0.8, trend="stable"
        )

        high_risk = MockPlayer(
            "risky", "Risky Player", PlayerPosition.RB, "GB",
            fantasy_points_avg=15.0, season_projection=240.0,
            injury_risk=0.6, consistency_score=0.8, trend="stable"
        )

        safe_value = self.evaluator.calculate_player_value(low_risk)
        risky_value = self.evaluator.calculate_player_value(high_risk)

        assert safe_value > risky_value

    def test_evaluate_simple_trade_fair(self):
        """Test evaluation of a fair 1-for-1 trade."""
        trade_data = {
            "team1_gives": [self.players["good_rb"]],
            "team1_gets": [self.players["wr1"]],
            "team2_gives": [self.players["wr1"]],
            "team2_gets": [self.players["good_rb"]]
        }

        analysis = self.evaluator.evaluate_trade(
            trade_data, self.teams["contender"], self.teams["rebuilding"]
        )

        assert analysis.fairness_rating in [FairnessRating.FAIR, FairnessRating.SLIGHTLY_FAVORS_TEAM1, FairnessRating.SLIGHTLY_FAVORS_TEAM2]
        assert abs(analysis.value_difference) < 20.0  # Close in value

    def test_evaluate_lopsided_trade(self):
        """Test evaluation of a lopsided trade."""
        trade_data = {
            "team1_gives": [self.players["elite_qb"]],
            "team1_gets": [self.players["boom_bust_wr"]],
            "team2_gives": [self.players["boom_bust_wr"]],
            "team2_gets": [self.players["elite_qb"]]
        }

        analysis = self.evaluator.evaluate_trade(
            trade_data, self.teams["contender"], self.teams["rebuilding"]
        )

        assert analysis.fairness_rating in [FairnessRating.HEAVILY_FAVORS_TEAM2, FairnessRating.MODERATELY_FAVORS_TEAM2]
        assert analysis.value_difference > 30.0

    def test_evaluate_trade_with_team_context(self):
        """Test evaluation considers team context and needs."""
        # Contender trading for win-now player
        trade_data = {
            "team1_gives": [self.players["good_rb"]],
            "team1_gets": [self.players["aging_rb"]],
            "team2_gives": [self.players["aging_rb"]],
            "team2_gets": [self.players["good_rb"]]
        }

        contender_analysis = self.evaluator.evaluate_trade(
            trade_data, self.teams["contender"], self.teams["rebuilding"]
        )

        # Should consider team needs and playoff status
        assert contender_analysis.team_fit_score > 0.5

    def test_calculate_positional_premium(self):
        """Test positional value premiums."""
        qb_premium = self.evaluator.calculate_positional_premium(PlayerPosition.QB)
        rb_premium = self.evaluator.calculate_positional_premium(PlayerPosition.RB)
        k_premium = self.evaluator.calculate_positional_premium(PlayerPosition.K)

        # QB should have highest premium, K lowest
        assert qb_premium > rb_premium > k_premium

    def test_evaluate_multi_player_trade(self):
        """Test evaluation of multi-player trade."""
        trade_data = {
            "team1_gives": [self.players["elite_qb"], self.players["boom_bust_wr"]],
            "team1_gets": [self.players["good_rb"], self.players["wr1"]],
            "team2_gives": [self.players["good_rb"], self.players["wr1"]],
            "team2_gets": [self.players["elite_qb"], self.players["boom_bust_wr"]]
        }

        analysis = self.evaluator.evaluate_trade(
            trade_data, self.teams["contender"], self.teams["rebuilding"]
        )

        assert isinstance(analysis.value_difference, float)
        assert analysis.fairness_rating is not None
        assert len(analysis.detailed_breakdown) > 0

    def test_calculate_trade_urgency_factor(self):
        """Test urgency factor calculation based on league context."""
        # Trade deadline approaching
        deadline_soon = datetime.now() + timedelta(days=2)
        urgency_high = self.evaluator.calculate_urgency_factor(deadline_soon)

        # Trade deadline far away
        deadline_far = datetime.now() + timedelta(days=30)
        urgency_low = self.evaluator.calculate_urgency_factor(deadline_far)

        assert urgency_high > urgency_low

    def test_risk_adjustment_calculation(self):
        """Test risk adjustment in value calculations."""
        high_risk_player = MockPlayer(
            "risky", "High Risk", PlayerPosition.RB, "MIA",
            fantasy_points_avg=20.0, season_projection=320.0,
            injury_risk=0.8, consistency_score=0.3, trend="down"
        )

        safe_player = MockPlayer(
            "safe", "Safe Player", PlayerPosition.RB, "GB",
            fantasy_points_avg=18.0, season_projection=288.0,
            injury_risk=0.1, consistency_score=0.9, trend="stable"
        )

        risky_value = self.evaluator.calculate_player_value(high_risk_player)
        safe_value = self.evaluator.calculate_player_value(safe_player)

        # Despite higher raw stats, risky player should have lower adjusted value
        assert safe_value > risky_value


class TestEnhancedTradeService:
    """Test the enhanced trade service with AI evaluation."""

    def setup_method(self):
        """Set up test fixtures."""
        self.trade_service = EnhancedTradeService()

    @pytest.mark.asyncio
    async def test_propose_trade(self):
        """Test proposing a new trade."""
        trade_proposal = {
            "proposing_team_id": "team1",
            "receiving_team_id": "team2",
            "proposed_players": ["player1", "player2"],
            "requested_players": ["player3"],
            "message": "Let's make a deal!"
        }

        with patch.object(self.trade_service, '_validate_trade_proposal') as mock_validate:
            mock_validate.return_value = True

            with patch.object(self.trade_service, '_create_trade_record') as mock_create:
                mock_trade = Mock(spec=Trade)
                mock_trade.id = "trade123"
                mock_create.return_value = mock_trade

                trade_id = await self.trade_service.propose_trade(trade_proposal)

                assert trade_id == "trade123"
                mock_validate.assert_called_once()
                mock_create.assert_called_once()

    @pytest.mark.asyncio
    async def test_evaluate_trade_proposal(self):
        """Test AI evaluation of trade proposal."""
        trade_id = "trade123"

        with patch.object(self.trade_service, '_get_trade') as mock_get:
            mock_trade = Mock(spec=Trade)
            mock_trade.proposed_players = ["player1"]
            mock_trade.requested_players = ["player2"]
            mock_get.return_value = mock_trade

            with patch.object(self.trade_service, '_run_ai_evaluation') as mock_ai:
                mock_analysis = Mock(spec=TradeAnalysis)
                mock_analysis.fairness_rating = FairnessRating.FAIR
                mock_analysis.recommendation = TradeRecommendation.ACCEPT
                mock_ai.return_value = mock_analysis

                evaluation = await self.trade_service.evaluate_trade(trade_id)

                assert evaluation.fairness_rating == FairnessRating.FAIR
                assert evaluation.recommendation == TradeRecommendation.ACCEPT

    @pytest.mark.asyncio
    async def test_respond_to_trade_accept(self):
        """Test accepting a trade."""
        trade_id = "trade123"
        team_id = "team2"

        with patch.object(self.trade_service, '_validate_trade_response') as mock_validate:
            mock_validate.return_value = True

            with patch.object(self.trade_service, '_process_trade_acceptance') as mock_process:
                result = await self.trade_service.respond_to_trade(
                    trade_id, team_id, "accept"
                )

                assert result.success
                mock_process.assert_called_once()

    @pytest.mark.asyncio
    async def test_respond_to_trade_reject(self):
        """Test rejecting a trade."""
        trade_id = "trade123"
        team_id = "team2"

        with patch.object(self.trade_service, '_validate_trade_response') as mock_validate:
            mock_validate.return_value = True

            with patch.object(self.trade_service, '_update_trade_status') as mock_update:
                result = await self.trade_service.respond_to_trade(
                    trade_id, team_id, "reject", "Not interested"
                )

                assert result.success
                mock_update.assert_called_with(trade_id, TradeStatus.REJECTED)

    @pytest.mark.asyncio
    async def test_counter_trade_proposal(self):
        """Test making a counter-proposal."""
        original_trade_id = "trade123"
        counter_proposal = {
            "proposed_players": ["player3"],
            "requested_players": ["player1", "player4"],
            "message": "Counter-offer"
        }

        with patch.object(self.trade_service, '_create_counter_trade') as mock_counter:
            counter_trade_id = "trade124"
            mock_counter.return_value = counter_trade_id

            result = await self.trade_service.counter_trade(
                original_trade_id, "team2", counter_proposal
            )

            assert result.success
            assert result.counter_trade_id == counter_trade_id

    @pytest.mark.asyncio
    async def test_expire_trade(self):
        """Test trade expiration handling."""
        trade_id = "trade123"

        with patch.object(self.trade_service, '_get_trade') as mock_get:
            mock_trade = Mock(spec=Trade)
            mock_trade.expires_at = datetime.now() - timedelta(hours=1)  # Expired
            mock_trade.status = TradeStatus.PENDING
            mock_get.return_value = mock_trade

            with patch.object(self.trade_service, '_update_trade_status') as mock_update:
                await self.trade_service.check_trade_expiration(trade_id)

                mock_update.assert_called_with(trade_id, TradeStatus.EXPIRED)

    @pytest.mark.asyncio
    async def test_process_trade_veto(self):
        """Test league veto handling."""
        trade_id = "trade123"
        veto_reason = "Collusion suspected"

        with patch.object(self.trade_service, '_validate_veto_authority') as mock_validate:
            mock_validate.return_value = True

            with patch.object(self.trade_service, '_update_trade_status') as mock_update:
                result = await self.trade_service.veto_trade(
                    trade_id, "commissioner", veto_reason
                )

                assert result.success
                mock_update.assert_called_with(trade_id, TradeStatus.VETOED)


class TestTradeValidation:
    """Test trade validation logic."""

    def setup_method(self):
        """Set up test fixtures."""
        self.trade_service = EnhancedTradeService()

    def test_validate_trade_participants(self):
        """Test validation of trade participants."""
        # Valid trade between different teams
        valid_result = self.trade_service._validate_participants("team1", "team2")
        assert valid_result

        # Invalid trade - same team
        invalid_result = self.trade_service._validate_participants("team1", "team1")
        assert not invalid_result

    def test_validate_player_ownership(self):
        """Test validation of player ownership."""
        team_roster = ["player1", "player2", "player3"]

        # Valid - team owns all proposed players
        valid_players = ["player1", "player2"]
        assert self.trade_service._validate_player_ownership(valid_players, team_roster)

        # Invalid - team doesn't own player4
        invalid_players = ["player1", "player4"]
        assert not self.trade_service._validate_player_ownership(invalid_players, team_roster)

    def test_validate_roster_limits(self):
        """Test validation of roster size limits after trade."""
        current_roster_size = 15
        max_roster_size = 16
        players_gained = 2
        players_lost = 1

        # Valid trade - stays within limits
        result = self.trade_service._validate_roster_limits(
            current_roster_size, max_roster_size, players_gained, players_lost
        )
        assert result

        # Invalid trade - exceeds roster limit
        players_gained = 3
        result = self.trade_service._validate_roster_limits(
            current_roster_size, max_roster_size, players_gained, players_lost
        )
        assert not result

    def test_validate_trade_deadline(self):
        """Test validation against trade deadline."""
        # Before deadline
        deadline = datetime.now() + timedelta(days=7)
        assert self.trade_service._validate_trade_deadline(deadline)

        # After deadline
        deadline = datetime.now() - timedelta(days=1)
        assert not self.trade_service._validate_trade_deadline(deadline)

    def test_validate_position_requirements(self):
        """Test validation of position requirements after trade."""
        current_positions = {"QB": 2, "RB": 3, "WR": 4, "TE": 1}
        min_requirements = {"QB": 1, "RB": 2, "WR": 3, "TE": 1}

        # Losing one QB but still meeting minimum
        players_lost = [MockPlayer("qb1", "QB1", PlayerPosition.QB, "KC", 20.0, 320.0, 0.1, 0.8, "stable")]
        players_gained = [MockPlayer("wr1", "WR1", PlayerPosition.WR, "BUF", 15.0, 240.0, 0.2, 0.7, "up")]

        result = self.trade_service._validate_position_requirements(
            current_positions, min_requirements, players_lost, players_gained
        )
        assert result

        # Losing too many at a position
        players_lost = [
            MockPlayer("qb1", "QB1", PlayerPosition.QB, "KC", 20.0, 320.0, 0.1, 0.8, "stable"),
            MockPlayer("qb2", "QB2", PlayerPosition.QB, "BUF", 18.0, 288.0, 0.2, 0.7, "stable")
        ]

        result = self.trade_service._validate_position_requirements(
            current_positions, min_requirements, players_lost, players_gained
        )
        assert not result


class TestTradeRecommendations:
    """Test AI-powered trade recommendations."""

    def setup_method(self):
        """Set up test fixtures."""
        self.trade_service = EnhancedTradeService()

    @pytest.mark.asyncio
    async def test_generate_trade_recommendations(self):
        """Test generation of trade recommendations for team."""
        team_id = "team1"

        with patch.object(self.trade_service, '_analyze_team_needs') as mock_needs:
            mock_needs.return_value = ["RB", "WR"]

            with patch.object(self.trade_service, '_find_potential_partners') as mock_partners:
                mock_partners.return_value = ["team2", "team3"]

                with patch.object(self.trade_service, '_generate_ai_recommendations') as mock_ai:
                    mock_recommendations = [
                        TradeRecommendation(
                            partner_team="team2",
                            give_players=["player1"],
                            get_players=["player2"],
                            confidence=0.85,
                            reasoning="Addresses RB need"
                        )
                    ]
                    mock_ai.return_value = mock_recommendations

                    recommendations = await self.trade_service.get_trade_recommendations(team_id)

                    assert len(recommendations) > 0
                    assert recommendations[0].confidence > 0.8

    @pytest.mark.asyncio
    async def test_analyze_team_weaknesses(self):
        """Test analysis of team weaknesses for trade targeting."""
        team_id = "team1"

        with patch.object(self.trade_service, '_get_team_roster') as mock_roster:
            mock_roster.return_value = [
                MockPlayer("qb1", "QB", PlayerPosition.QB, "KC", 25.0, 400.0, 0.1, 0.9, "stable"),
                MockPlayer("rb1", "RB", PlayerPosition.RB, "SF", 12.0, 192.0, 0.4, 0.5, "down"),  # Weak
                MockPlayer("wr1", "WR", PlayerPosition.WR, "BUF", 18.0, 288.0, 0.2, 0.8, "up"),
            ]

            weaknesses = await self.trade_service._analyze_team_weaknesses(team_id)

            assert "RB" in weaknesses
            assert weaknesses["RB"]["severity"] > 0.5

    @pytest.mark.asyncio
    async def test_find_mutual_benefit_trades(self):
        """Test finding trades that benefit both teams."""
        team1_id = "team1"
        team2_id = "team2"

        with patch.object(self.trade_service, '_get_complementary_needs') as mock_needs:
            mock_needs.return_value = {
                "team1_needs": ["RB"],
                "team2_needs": ["WR"],
                "team1_surplus": ["WR"],
                "team2_surplus": ["RB"]
            }

            mutual_trades = await self.trade_service._find_mutual_benefit_trades(team1_id, team2_id)

            assert len(mutual_trades) > 0
            assert mutual_trades[0]["mutual_benefit_score"] > 0.7


class TestTradePerformance:
    """Test trade evaluation performance."""

    def setup_method(self):
        """Set up test fixtures."""
        self.evaluator = TradeEvaluator()

    def test_evaluate_many_trades_performance(self):
        """Test performance when evaluating many trades."""
        import time

        # Create 100 mock trades to evaluate
        trades = []
        for i in range(100):
            trade = {
                "team1_gives": [self.create_mock_player(f"p{i*2}")],
                "team1_gets": [self.create_mock_player(f"p{i*2+1}")],
                "team2_gives": [self.create_mock_player(f"p{i*2+1}")],
                "team2_gets": [self.create_mock_player(f"p{i*2}")]
            }
            trades.append(trade)

        team1 = MockTeam("team1", "Team 1", "user1", {"wins": 5, "losses": 5}, 0.5, ["RB"])
        team2 = MockTeam("team2", "Team 2", "user2", {"wins": 6, "losses": 4}, 0.7, ["WR"])

        start_time = time.time()

        for trade in trades:
            self.evaluator.evaluate_trade(trade, team1, team2)

        end_time = time.time()
        evaluation_time = end_time - start_time

        # Should evaluate 100 trades in under 1 second
        assert evaluation_time < 1.0

    def create_mock_player(self, player_id: str) -> MockPlayer:
        """Create a mock player for performance testing."""
        return MockPlayer(
            player_id, f"Player {player_id}", PlayerPosition.RB, "SF",
            fantasy_points_avg=15.0, season_projection=240.0,
            injury_risk=0.2, consistency_score=0.7, trend="stable"
        )

    def test_complex_multi_team_trade_performance(self):
        """Test performance of complex multi-team trade evaluation."""
        import time

        # 3-team trade with multiple players
        complex_trade = {
            "team1_gives": [self.create_mock_player(f"p{i}") for i in range(3)],
            "team1_gets": [self.create_mock_player(f"p{i}") for i in range(10, 12)],
            "team2_gives": [self.create_mock_player(f"p{i}") for i in range(10, 13)],
            "team2_gets": [self.create_mock_player(f"p{i}") for i in range(3, 5)],
            "team3_gives": [self.create_mock_player(f"p{i}") for i in range(5, 6)],
            "team3_gets": [self.create_mock_player(f"p{i}") for i in range(12, 13)]
        }

        team1 = MockTeam("team1", "Team 1", "user1", {"wins": 5, "losses": 5}, 0.5, ["RB"])
        team2 = MockTeam("team2", "Team 2", "user2", {"wins": 6, "losses": 4}, 0.7, ["WR"])

        start_time = time.time()

        analysis = self.evaluator.evaluate_trade(complex_trade, team1, team2)

        end_time = time.time()
        evaluation_time = end_time - start_time

        # Should handle complex trade quickly
        assert evaluation_time < 0.1
        assert analysis is not None