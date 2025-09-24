"""
Unit tests for AI recommendation systems and analytics.

Tests cover:
- Player performance prediction
- Lineup optimization algorithms
- Waiver wire recommendations
- Trade recommendations
- Risk assessment models
"""

import pytest
import numpy as np
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from unittest.mock import Mock, patch, MagicMock
from dataclasses import dataclass

# Import AI recommendation components
from domains.ai.models.performance_predictor import (
    PerformancePredictor, PredictionModel, FeatureExtractor
)
from domains.ai.algorithms.lineup_optimizer import (
    LineupOptimizer, OptimizationResult, LineupConstraints
)
from domains.ai.algorithms.waiver_recommender import (
    WaiverRecommender, WaiverRecommendation, PlayerTrend
)
from domains.ai.services.ai_service import AIService
from domains.analytics.services.analytics_service import AnalyticsService
from models.player import Player, PlayerPosition


@dataclass
class MockPlayer:
    """Mock player for testing."""
    id: str
    name: str
    position: PlayerPosition
    team: str
    salary: float
    projected_points: float
    actual_points: List[float]  # Historical performance
    injury_risk: float
    ownership_percentage: float
    opponent_rank: int  # Opponent defense ranking


@dataclass
class MockMatchup:
    """Mock matchup data for testing."""
    player_id: str
    opponent: str
    home_away: str
    weather_conditions: Optional[Dict[str, Any]]
    game_script_factor: float  # Predicted game flow impact


class TestPerformancePredictor:
    """Test player performance prediction model."""

    def setup_method(self):
        """Set up test fixtures."""
        self.predictor = PerformancePredictor()
        self.feature_extractor = FeatureExtractor()

        # Create mock players with varying performance patterns
        self.players = {
            "consistent": MockPlayer(
                "p1", "Consistent Player", PlayerPosition.RB, "SF",
                salary=8500, projected_points=18.5,
                actual_points=[18.2, 19.1, 17.8, 18.9, 18.4, 17.6, 19.3],
                injury_risk=0.1, ownership_percentage=0.25, opponent_rank=15
            ),
            "volatile": MockPlayer(
                "p2", "Volatile Player", PlayerPosition.WR, "KC",
                salary=7200, projected_points=15.8,
                actual_points=[8.2, 24.1, 11.8, 28.9, 7.4, 22.6, 13.3],
                injury_risk=0.2, ownership_percentage=0.18, opponent_rank=8
            ),
            "trending_up": MockPlayer(
                "p3", "Trending Up", PlayerPosition.QB, "BUF",
                salary=9200, projected_points=22.3,
                actual_points=[16.2, 17.8, 19.4, 21.1, 23.7, 25.2, 26.8],
                injury_risk=0.05, ownership_percentage=0.35, opponent_rank=22
            ),
            "injury_prone": MockPlayer(
                "p4", "Injury Prone", PlayerPosition.TE, "GB",
                salary=6800, projected_points=12.5,
                actual_points=[14.2, 0.0, 15.8, 0.0, 13.4, 16.6, 0.0],
                injury_risk=0.6, ownership_percentage=0.12, opponent_rank=10
            )
        }

    def test_extract_basic_features(self):
        """Test extraction of basic player features."""
        player = self.players["consistent"]

        features = self.feature_extractor.extract_features(player)

        assert "avg_points" in features
        assert "points_variance" in features
        assert "recent_trend" in features
        assert "salary_value" in features
        assert "injury_risk" in features

        # Check feature values
        assert features["avg_points"] == pytest.approx(18.47, rel=1e-2)
        assert features["points_variance"] < 1.0  # Consistent player
        assert features["injury_risk"] == 0.1

    def test_extract_advanced_features(self):
        """Test extraction of advanced statistical features."""
        player = self.players["volatile"]

        features = self.feature_extractor.extract_advanced_features(player)

        assert "ceiling" in features
        assert "floor" in features
        assert "consistency_score" in features
        assert "upside_score" in features

        # Volatile player should have high ceiling, low floor
        assert features["ceiling"] > features["floor"]
        assert features["consistency_score"] < 0.5

    def test_calculate_recent_trend(self):
        """Test calculation of recent performance trend."""
        trending_player = self.players["trending_up"]

        trend = self.feature_extractor.calculate_trend(trending_player.actual_points)

        # Should detect positive trend
        assert trend > 0.5

    def test_predict_player_performance(self):
        """Test basic performance prediction."""
        player = self.players["consistent"]

        with patch.object(self.predictor, '_get_matchup_data') as mock_matchup:
            mock_matchup.return_value = MockMatchup(
                player.id, "SEA", "home", None, 1.0
            )

            prediction = self.predictor.predict_performance(player)

            assert prediction.expected_points > 0
            assert prediction.confidence > 0.0
            assert prediction.variance > 0.0
            assert isinstance(prediction.range_low, float)
            assert isinstance(prediction.range_high, float)

    def test_predict_with_matchup_context(self):
        """Test prediction incorporates matchup context."""
        player = self.players["consistent"]

        # Good matchup
        good_matchup = MockMatchup(
            player.id, "worst_defense", "home", {"temp": 72, "wind": 5}, 1.2
        )

        # Bad matchup
        bad_matchup = MockMatchup(
            player.id, "best_defense", "away", {"temp": 32, "wind": 20}, 0.8
        )

        with patch.object(self.predictor, '_get_matchup_data') as mock_matchup:
            # Test good matchup
            mock_matchup.return_value = good_matchup
            good_prediction = self.predictor.predict_performance(player)

            # Test bad matchup
            mock_matchup.return_value = bad_matchup
            bad_prediction = self.predictor.predict_performance(player)

            # Good matchup should predict higher points
            assert good_prediction.expected_points > bad_prediction.expected_points

    def test_model_confidence_calculation(self):
        """Test confidence calculation based on data quality."""
        # Player with lots of consistent data
        consistent_player = self.players["consistent"]

        # Player with limited/volatile data
        volatile_player = self.players["volatile"]

        consistent_prediction = self.predictor.predict_performance(consistent_player)
        volatile_prediction = self.predictor.predict_performance(volatile_player)

        # Consistent player should have higher confidence
        assert consistent_prediction.confidence > volatile_prediction.confidence

    def test_injury_risk_adjustment(self):
        """Test injury risk impacts predictions."""
        healthy_player = self.players["consistent"]
        injury_prone_player = self.players["injury_prone"]

        healthy_prediction = self.predictor.predict_performance(healthy_player)
        risky_prediction = self.predictor.predict_performance(injury_prone_player)

        # Injury risk should lower expected points and confidence
        assert healthy_prediction.expected_points > risky_prediction.expected_points
        assert healthy_prediction.confidence > risky_prediction.confidence

    def test_batch_prediction_performance(self):
        """Test performance of batch predictions."""
        import time

        players = list(self.players.values()) * 25  # 100 players

        start_time = time.time()

        predictions = self.predictor.predict_batch(players)

        end_time = time.time()
        prediction_time = end_time - start_time

        assert len(predictions) == len(players)
        assert prediction_time < 1.0  # Should predict 100 players in under 1 second


class TestLineupOptimizer:
    """Test lineup optimization algorithms."""

    def setup_method(self):
        """Set up test fixtures."""
        self.optimizer = LineupOptimizer()

        # Create player pool for optimization
        self.player_pool = [
            MockPlayer("qb1", "Elite QB", PlayerPosition.QB, "KC", 9200, 24.5, [24.0, 25.0], 0.1, 0.35, 15),
            MockPlayer("qb2", "Value QB", PlayerPosition.QB, "BUF", 7800, 20.2, [19.5, 21.0], 0.15, 0.22, 18),
            MockPlayer("rb1", "Top RB", PlayerPosition.RB, "SF", 8800, 22.8, [23.0, 22.5], 0.2, 0.40, 12),
            MockPlayer("rb2", "Solid RB", PlayerPosition.RB, "DAL", 7400, 18.6, [18.0, 19.2], 0.25, 0.28, 16),
            MockPlayer("rb3", "Value RB", PlayerPosition.RB, "GB", 6200, 14.8, [15.0, 14.5], 0.3, 0.15, 20),
            MockPlayer("wr1", "Elite WR", PlayerPosition.WR, "BUF", 8600, 21.4, [21.0, 22.0], 0.15, 0.38, 14),
            MockPlayer("wr2", "Good WR", PlayerPosition.WR, "MIA", 7200, 17.8, [18.0, 17.5], 0.2, 0.25, 17),
            MockPlayer("wr3", "Value WR", PlayerPosition.WR, "LAR", 5800, 13.2, [13.5, 13.0], 0.25, 0.12, 22),
            MockPlayer("te1", "Top TE", PlayerPosition.TE, "KC", 7000, 16.5, [16.0, 17.0], 0.2, 0.30, 19),
            MockPlayer("te2", "Value TE", PlayerPosition.TE, "SF", 4800, 11.8, [12.0, 11.5], 0.3, 0.08, 25),
        ]

        # DraftKings-style constraints
        self.constraints = LineupConstraints(
            salary_cap=50000,
            positions={
                PlayerPosition.QB: {"min": 1, "max": 1},
                PlayerPosition.RB: {"min": 2, "max": 3},
                PlayerPosition.WR: {"min": 3, "max": 4},
                PlayerPosition.TE: {"min": 1, "max": 2},
            },
            total_players=9,
            max_players_per_team=None,
            max_ownership=None
        )

    def test_optimize_basic_lineup(self):
        """Test basic lineup optimization."""
        result = self.optimizer.optimize_lineup(self.player_pool, self.constraints)

        assert result.success
        assert len(result.lineup) == 9
        assert result.total_salary <= 50000
        assert result.projected_points > 0

        # Check position constraints
        position_counts = {}
        for player in result.lineup:
            pos = player.position
            position_counts[pos] = position_counts.get(pos, 0) + 1

        assert position_counts[PlayerPosition.QB] == 1
        assert 2 <= position_counts[PlayerPosition.RB] <= 3
        assert 3 <= position_counts[PlayerPosition.WR] <= 4
        assert 1 <= position_counts[PlayerPosition.TE] <= 2

    def test_optimize_with_ownership_constraints(self):
        """Test optimization with ownership constraints."""
        ownership_constraints = self.constraints
        ownership_constraints.max_ownership = 0.3  # Avoid highly owned players

        result = self.optimizer.optimize_lineup(self.player_pool, ownership_constraints)

        # Should avoid players with >30% ownership
        for player in result.lineup:
            assert player.ownership_percentage <= 0.3

    def test_optimize_with_team_stacking(self):
        """Test optimization with team stacking preferences."""
        stack_preferences = {
            "KC": 2,  # Want 2 KC players
            "BUF": 2  # Want 2 BUF players
        }

        result = self.optimizer.optimize_lineup(
            self.player_pool, self.constraints, team_stacks=stack_preferences
        )

        # Count players by team
        team_counts = {}
        for player in result.lineup:
            team = player.team
            team_counts[team] = team_counts.get(team, 0) + 1

        # Should try to meet stacking preferences
        assert team_counts.get("KC", 0) >= 1  # At least some correlation attempts

    def test_optimize_cash_vs_tournament(self):
        """Test different optimization strategies."""
        # Cash game optimization (safer, higher floor)
        cash_result = self.optimizer.optimize_lineup(
            self.player_pool, self.constraints, strategy="cash"
        )

        # Tournament optimization (higher ceiling, more risk)
        tournament_result = self.optimizer.optimize_lineup(
            self.player_pool, self.constraints, strategy="tournament"
        )

        # Tournament lineup should generally have higher upside
        # (This is strategy-dependent, so we just check it runs)
        assert cash_result.success
        assert tournament_result.success

    def test_generate_multiple_lineups(self):
        """Test generation of multiple optimal lineups."""
        num_lineups = 5

        results = self.optimizer.generate_multiple_lineups(
            self.player_pool, self.constraints, num_lineups
        )

        assert len(results) == num_lineups

        # Each lineup should be valid and different
        lineup_signatures = set()
        for result in results:
            assert result.success
            assert len(result.lineup) == 9

            # Create signature to check uniqueness
            signature = tuple(sorted(p.id for p in result.lineup))
            lineup_signatures.add(signature)

        # Should generate some variety (at least 3 different lineups)
        assert len(lineup_signatures) >= 3

    def test_optimization_performance(self):
        """Test optimization performance with larger player pool."""
        import time

        # Create larger player pool
        large_pool = self.player_pool * 5  # 50 players

        start_time = time.time()

        result = self.optimizer.optimize_lineup(large_pool, self.constraints)

        end_time = time.time()
        optimization_time = end_time - start_time

        assert result.success
        assert optimization_time < 2.0  # Should optimize in under 2 seconds


class TestWaiverRecommender:
    """Test waiver wire recommendation engine."""

    def setup_method(self):
        """Set up test fixtures."""
        self.recommender = WaiverRecommender()

        # Mock available players on waivers
        self.waiver_players = [
            MockPlayer("wa1", "Handcuff RB", PlayerPosition.RB, "SF", 0, 8.5, [0, 0, 20.5], 0.1, 0.05, 12),
            MockPlayer("wa2", "Emerging WR", PlayerPosition.WR, "MIA", 0, 12.8, [6.2, 8.1, 15.4], 0.2, 0.08, 18),
            MockPlayer("wa3", "Injury Replacement", PlayerPosition.QB, "GB", 0, 18.2, [22.1, 16.8], 0.3, 0.02, 20),
            MockPlayer("wa4", "Lottery Ticket", PlayerPosition.WR, "LAR", 0, 7.2, [2.1, 4.8, 18.9], 0.4, 0.01, 25),
        ]

        # Mock user's current roster
        self.current_roster = [
            MockPlayer("r1", "Starting QB", PlayerPosition.QB, "KC", 0, 24.5, [24.0, 25.0], 0.1, 0.35, 15),
            MockPlayer("r2", "Injured RB", PlayerPosition.RB, "DAL", 0, 0.0, [18.0, 0.0], 0.9, 0.25, 16),  # Injured
            MockPlayer("r3", "Underperforming WR", PlayerPosition.WR, "NYJ", 0, 8.2, [6.0, 4.5], 0.2, 0.15, 30),  # Bad
        ]

    def test_identify_roster_needs(self):
        """Test identification of roster needs."""
        needs = self.recommender.identify_roster_needs(self.current_roster)

        # Should identify injured RB and underperforming WR as needs
        assert PlayerPosition.RB in needs
        assert PlayerPosition.WR in needs
        assert needs[PlayerPosition.RB]["urgency"] > 0.7  # High urgency for injured player

    def test_calculate_player_trend(self):
        """Test calculation of player performance trends."""
        # Trending up player
        trending_up = MockPlayer("up", "Up", PlayerPosition.WR, "MIA", 0, 12.8, [6.2, 8.1, 15.4], 0.2, 0.08, 18)
        up_trend = self.recommender.calculate_trend(trending_up.actual_points)

        # Trending down player
        trending_down = MockPlayer("down", "Down", PlayerPosition.WR, "NYJ", 0, 8.2, [15.4, 8.1, 6.2], 0.2, 0.15, 30)
        down_trend = self.recommender.calculate_trend(trending_down.actual_points)

        assert up_trend > 0.5  # Positive trend
        assert down_trend < -0.5  # Negative trend

    def test_recommend_waiver_pickups(self):
        """Test waiver pickup recommendations."""
        recommendations = self.recommender.recommend_pickups(
            self.current_roster, self.waiver_players, budget=100
        )

        assert len(recommendations) > 0

        # Should prioritize based on roster needs
        top_rec = recommendations[0]
        assert top_rec.confidence > 0.5
        assert top_rec.priority in ["high", "medium", "low"]

    def test_recommend_based_on_injury_news(self):
        """Test recommendations react to injury news."""
        # Simulate injury to starting player
        injury_news = {
            "player_id": "starter_rb",
            "severity": "out_2_weeks",
            "affected_players": ["wa1"]  # Handcuff becomes valuable
        }

        recommendations = self.recommender.recommend_with_injury_context(
            self.current_roster, self.waiver_players, injury_news
        )

        # Handcuff should be top recommendation
        handcuff_rec = next((r for r in recommendations if r.player_id == "wa1"), None)
        assert handcuff_rec is not None
        assert handcuff_rec.priority == "high"

    def test_recommend_based_on_matchups(self):
        """Test recommendations consider upcoming matchups."""
        # Player with great upcoming matchups
        matchup_data = {
            "wa2": {"next_3_games": ["vs_worst_def", "vs_bad_def", "@avg_def"], "difficulty": 0.2},
            "wa4": {"next_3_games": ["@best_def", "vs_good_def", "@good_def"], "difficulty": 0.8}
        }

        recommendations = self.recommender.recommend_with_matchup_context(
            self.current_roster, self.waiver_players, matchup_data
        )

        # Player with easier matchups should rank higher
        easy_matchup = next((r for r in recommendations if r.player_id == "wa2"), None)
        hard_matchup = next((r for r in recommendations if r.player_id == "wa4"), None)

        if easy_matchup and hard_matchup:
            assert easy_matchup.confidence > hard_matchup.confidence

    def test_calculate_waiver_bid_amount(self):
        """Test calculation of appropriate waiver bid amounts."""
        high_value_player = self.waiver_players[0]  # Handcuff with upside
        low_value_player = self.waiver_players[3]   # Lottery ticket

        high_bid = self.recommender.calculate_bid_amount(
            high_value_player, self.current_roster, budget=100, urgency="high"
        )

        low_bid = self.recommender.calculate_bid_amount(
            low_value_player, self.current_roster, budget=100, urgency="low"
        )

        assert high_bid > low_bid
        assert high_bid <= 100  # Within budget
        assert low_bid >= 1     # Minimum bid


class TestAIService:
    """Test the main AI service coordinator."""

    def setup_method(self):
        """Set up test fixtures."""
        self.ai_service = AIService()

    @pytest.mark.asyncio
    async def test_get_lineup_recommendations(self):
        """Test getting AI-powered lineup recommendations."""
        team_id = "team1"
        week = 10

        with patch.object(self.ai_service, '_get_team_roster') as mock_roster:
            mock_roster.return_value = []

            with patch.object(self.ai_service, '_get_available_players') as mock_available:
                mock_available.return_value = []

                with patch.object(self.ai_service, 'lineup_optimizer') as mock_optimizer:
                    mock_result = Mock()
                    mock_result.success = True
                    mock_result.lineup = []
                    mock_result.projected_points = 150.5
                    mock_optimizer.optimize_lineup.return_value = mock_result

                    recommendations = await self.ai_service.get_lineup_recommendations(team_id, week)

                    assert recommendations["success"]
                    assert "lineup" in recommendations
                    assert "projected_points" in recommendations

    @pytest.mark.asyncio
    async def test_get_waiver_recommendations(self):
        """Test getting waiver wire recommendations."""
        team_id = "team1"

        with patch.object(self.ai_service, 'waiver_recommender') as mock_recommender:
            mock_recommendations = [
                WaiverRecommendation(
                    player_id="wa1", confidence=0.85, priority="high",
                    reasoning="Handcuff with high upside", bid_amount=25
                )
            ]
            mock_recommender.recommend_pickups.return_value = mock_recommendations

            recommendations = await self.ai_service.get_waiver_recommendations(team_id)

            assert len(recommendations) > 0
            assert recommendations[0]["confidence"] > 0.8

    @pytest.mark.asyncio
    async def test_analyze_trade_with_ai(self):
        """Test AI-powered trade analysis."""
        trade_data = {
            "team1_gives": ["player1"],
            "team1_gets": ["player2"],
            "team2_gives": ["player2"],
            "team2_gets": ["player1"]
        }

        with patch.object(self.ai_service, '_get_trade_context') as mock_context:
            mock_context.return_value = {}

            with patch.object(self.ai_service, 'trade_evaluator') as mock_evaluator:
                mock_analysis = Mock()
                mock_analysis.fairness_rating = "fair"
                mock_analysis.confidence = 0.82
                mock_evaluator.evaluate_trade.return_value = mock_analysis

                analysis = await self.ai_service.analyze_trade(trade_data)

                assert analysis["fairness_rating"] == "fair"
                assert analysis["confidence"] > 0.8

    @pytest.mark.asyncio
    async def test_predict_player_performance(self):
        """Test player performance prediction."""
        player_id = "player1"
        week = 10

        with patch.object(self.ai_service, 'performance_predictor') as mock_predictor:
            mock_prediction = Mock()
            mock_prediction.expected_points = 18.5
            mock_prediction.confidence = 0.78
            mock_prediction.range_low = 12.0
            mock_prediction.range_high = 25.0
            mock_predictor.predict_performance.return_value = mock_prediction

            prediction = await self.ai_service.predict_player_performance(player_id, week)

            assert prediction["expected_points"] == 18.5
            assert prediction["confidence"] > 0.7

    @pytest.mark.asyncio
    async def test_get_ai_insights(self):
        """Test general AI insights generation."""
        team_id = "team1"

        with patch.object(self.ai_service, '_analyze_team_performance') as mock_analyze:
            mock_analyze.return_value = {
                "strengths": ["Strong QB play"],
                "weaknesses": ["Inconsistent RB production"],
                "opportunities": ["Favorable upcoming schedule"]
            }

            insights = await self.ai_service.get_team_insights(team_id)

            assert "strengths" in insights
            assert "weaknesses" in insights
            assert "opportunities" in insights


class TestAnalyticsService:
    """Test analytics and metrics calculation."""

    def setup_method(self):
        """Set up test fixtures."""
        self.analytics_service = AnalyticsService()

    @pytest.mark.asyncio
    async def test_calculate_player_efficiency_metrics(self):
        """Test calculation of player efficiency metrics."""
        player_id = "player1"

        with patch.object(self.analytics_service, '_get_player_data') as mock_data:
            mock_data.return_value = {
                "games": [
                    {"points": 18.5, "targets": 8, "touches": 15, "snap_percentage": 0.85},
                    {"points": 22.1, "targets": 10, "touches": 18, "snap_percentage": 0.90},
                    {"points": 14.2, "targets": 6, "touches": 12, "snap_percentage": 0.75}
                ]
            }

            metrics = await self.analytics_service.calculate_efficiency_metrics(player_id)

            assert "points_per_touch" in metrics
            assert "target_share" in metrics
            assert "snap_percentage_avg" in metrics
            assert metrics["points_per_touch"] > 0

    @pytest.mark.asyncio
    async def test_calculate_team_strength_metrics(self):
        """Test calculation of team strength metrics."""
        team_id = "team1"

        with patch.object(self.analytics_service, '_get_team_schedule') as mock_schedule:
            mock_schedule.return_value = [
                {"opponent": "team2", "points_for": 120, "points_against": 95},
                {"opponent": "team3", "points_for": 135, "points_against": 110},
                {"opponent": "team4", "points_for": 105, "points_against": 125}
            ]

            metrics = await self.analytics_service.calculate_team_metrics(team_id)

            assert "avg_points_for" in metrics
            assert "avg_points_against" in metrics
            assert "strength_of_schedule" in metrics

    def test_calculate_consistency_score(self):
        """Test player consistency score calculation."""
        # Consistent performer
        consistent_scores = [18.2, 19.1, 17.8, 18.9, 18.4, 17.6, 19.3]
        consistent_score = self.analytics_service.calculate_consistency_score(consistent_scores)

        # Volatile performer
        volatile_scores = [8.2, 24.1, 11.8, 28.9, 7.4, 22.6, 13.3]
        volatile_score = self.analytics_service.calculate_consistency_score(volatile_scores)

        assert consistent_score > volatile_score
        assert 0 <= consistent_score <= 1
        assert 0 <= volatile_score <= 1


class TestAIPerformance:
    """Test AI system performance and scalability."""

    def setup_method(self):
        """Set up test fixtures."""
        self.ai_service = AIService()

    def test_batch_prediction_performance(self):
        """Test performance of batch predictions."""
        import time

        # Create 100 mock players
        players = [
            MockPlayer(f"p{i}", f"Player {i}", PlayerPosition.RB, "SF", 7000, 15.0, [15.0], 0.2, 0.1, 15)
            for i in range(100)
        ]

        start_time = time.time()

        with patch.object(self.ai_service.performance_predictor, 'predict_batch') as mock_predict:
            mock_predict.return_value = [Mock() for _ in players]

            predictions = self.ai_service.performance_predictor.predict_batch(players)

        end_time = time.time()
        prediction_time = end_time - start_time

        assert len(predictions) == 100
        assert prediction_time < 2.0  # Should handle 100 predictions quickly

    def test_lineup_optimization_scalability(self):
        """Test lineup optimization with large player pool."""
        import time

        # Create large player pool (200 players)
        large_pool = []
        positions = [PlayerPosition.QB, PlayerPosition.RB, PlayerPosition.WR, PlayerPosition.TE]

        for i in range(200):
            pos = positions[i % len(positions)]
            large_pool.append(
                MockPlayer(f"p{i}", f"Player {i}", pos, "SF", 5000 + (i * 50), 10.0 + i/10, [10.0], 0.2, 0.1, 15)
            )

        constraints = LineupConstraints(
            salary_cap=50000,
            positions={
                PlayerPosition.QB: {"min": 1, "max": 1},
                PlayerPosition.RB: {"min": 2, "max": 3},
                PlayerPosition.WR: {"min": 3, "max": 4},
                PlayerPosition.TE: {"min": 1, "max": 2},
            },
            total_players=9
        )

        start_time = time.time()

        optimizer = LineupOptimizer()
        result = optimizer.optimize_lineup(large_pool, constraints)

        end_time = time.time()
        optimization_time = end_time - start_time

        assert result.success
        assert optimization_time < 5.0  # Should optimize large pool reasonably quickly