"""
Trade evaluation algorithm for fantasy sports trades.

Provides comprehensive trade analysis and fairness evaluation including:
- Multi-factor trade scoring and analysis
- Player value assessment based on performance metrics
- Position scarcity and roster impact analysis
- Trade fairness scoring and imbalance detection
- League-specific scoring rule integration
- Historical performance and projection weighting
- Risk assessment for injured or underperforming players
"""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any

try:
    from infrastructure.logging.domain_logger import get_logger
except ImportError:
    import logging

    get_logger = logging.getLogger

logger = get_logger(__name__)


class TradeEvaluationError(Exception):
    """Trade evaluation algorithm errors."""


class FairnessLevel(Enum):
    """Trade fairness assessment levels."""

    VERY_FAIR = "very_fair"
    FAIR = "fair"
    SLIGHTLY_UNFAIR = "slightly_unfair"
    UNFAIR = "unfair"
    VERY_UNFAIR = "very_unfair"


@dataclass
class PlayerValue:
    """Player value assessment."""

    player_id: str
    base_value: float
    position_scarcity_multiplier: float
    injury_risk_penalty: float
    recent_performance_modifier: float
    projection_confidence: float
    final_value: float
    value_tier: str  # elite, high, medium, low, waiver


@dataclass
class TradeAnalysis:
    """Complete trade analysis results."""

    trade_id: str
    team_a_id: str
    team_b_id: str
    team_a_players: list[str]
    team_b_players: list[str]

    # Value assessments
    team_a_total_value: float
    team_b_total_value: float
    value_difference: float
    value_difference_percentage: float

    # Player details
    team_a_player_values: list[PlayerValue]
    team_b_player_values: list[PlayerValue]

    # Trade scoring
    fairness_score: float
    fairness_level: FairnessLevel
    trade_grade_team_a: str
    trade_grade_team_b: str

    # Analysis details
    position_impact: dict[str, dict[str, float]]
    roster_improvement_team_a: float
    roster_improvement_team_b: float
    risk_assessment: dict[str, Any]

    # Recommendations
    recommendation: str
    reasoning: list[str]
    concerns: list[str]

    # Metadata
    evaluated_at: datetime
    confidence_level: float


class TradeEvaluator:
    """Advanced trade evaluation algorithm."""

    def __init__(self) -> None:
        # Position scarcity weights (higher = more scarce)
        self.position_scarcity = {
            "QB": 1.2,
            "RB": 1.5,
            "WR": 1.1,
            "TE": 1.4,
            "K": 0.8,
            "DEF": 0.9,
            # MLB positions
            "C": 1.3,
            "1B": 1.1,
            "2B": 1.2,
            "3B": 1.2,
            "SS": 1.3,
            "OF": 1.0,
            "DH": 1.0,
            "P": 1.1,
            # WNBA positions
            "PG": 1.2,
            "SG": 1.1,
            "SF": 1.1,
            "PF": 1.2,
        }

        # Value tier thresholds (percentiles)
        self.value_tiers = {
            "elite": 95,
            "high": 80,
            "medium": 60,
            "low": 30,
            "waiver": 0,
        }

        # Fairness thresholds (value difference percentages)
        self.fairness_thresholds = {
            FairnessLevel.VERY_FAIR: 5.0,
            FairnessLevel.FAIR: 15.0,
            FairnessLevel.SLIGHTLY_UNFAIR: 25.0,
            FairnessLevel.UNFAIR: 40.0,
            FairnessLevel.VERY_UNFAIR: 100.0,
        }

    async def evaluate_trade(
        self,
        trade_id: str,
        team_a_id: str,
        team_b_id: str,
        team_a_players: list[str],
        team_b_players: list[str],
        league_scoring_rules: dict[str, Any],
        current_rosters: dict[str, list[dict[str, Any]]],
        player_stats: dict[str, dict[str, Any]],
        league_context: dict[str, Any] | None = None,
    ) -> TradeAnalysis:
        """
        Evaluate a proposed trade between two teams.

        Args:
            trade_id: Unique identifier for the trade
            team_a_id: First team ID
            team_b_id: Second team ID
            team_a_players: Player IDs being traded by team A
            team_b_players: Player IDs being traded by team B
            league_scoring_rules: League-specific scoring configuration
            current_rosters: Current roster compositions for both teams
            player_stats: Historical and projected player statistics
            league_context: Additional league information (position limits, etc.)

        Returns:
            Complete trade analysis with recommendations
        """
        try:
            logger.info(
                "Evaluating trade",
                extra={
                    "trade_id": trade_id,
                    "team_a": team_a_id,
                    "team_b": team_b_id,
                    "team_a_players": len(team_a_players),
                    "team_b_players": len(team_b_players),
                },
            )

            # Validate inputs
            if not team_a_players or not team_b_players:
                raise TradeEvaluationError("Both teams must trade at least one player")

            # Calculate player values
            team_a_values = await self._calculate_player_values(
                team_a_players, league_scoring_rules, player_stats
            )
            team_b_values = await self._calculate_player_values(
                team_b_players, league_scoring_rules, player_stats
            )

            # Calculate total values
            team_a_total = sum(pv.final_value for pv in team_a_values)
            team_b_total = sum(pv.final_value for pv in team_b_values)

            # Calculate value difference
            value_difference = abs(team_a_total - team_b_total)
            avg_value = (team_a_total + team_b_total) / 2
            value_diff_percentage = (
                (value_difference / avg_value * 100) if avg_value > 0 else 0
            )

            # Determine fairness level
            fairness_level = self._determine_fairness_level(value_diff_percentage)
            fairness_score = max(0, 100 - value_diff_percentage)

            # Calculate roster impact
            roster_impact_a = await self._calculate_roster_impact(
                team_a_id, team_a_players, team_b_players, current_rosters, player_stats
            )
            roster_impact_b = await self._calculate_roster_impact(
                team_b_id, team_b_players, team_a_players, current_rosters, player_stats
            )

            # Analyze position impacts
            position_impact = self._analyze_position_impact(
                team_a_values + team_b_values, team_a_players, team_b_players
            )

            # Generate trade grades
            grade_a = self._calculate_trade_grade(roster_impact_a, fairness_score, True)
            grade_b = self._calculate_trade_grade(
                roster_impact_b, fairness_score, False
            )

            # Risk assessment
            risk_assessment = self._assess_trade_risks(
                team_a_values + team_b_values, player_stats
            )

            # Generate recommendations
            recommendation, reasoning, concerns = self._generate_recommendations(
                fairness_level, roster_impact_a, roster_impact_b, risk_assessment
            )

            # Calculate confidence level
            confidence = self._calculate_confidence_level(
                team_a_values + team_b_values, player_stats
            )

            # Create analysis result
            analysis = TradeAnalysis(
                trade_id=trade_id,
                team_a_id=team_a_id,
                team_b_id=team_b_id,
                team_a_players=team_a_players,
                team_b_players=team_b_players,
                team_a_total_value=team_a_total,
                team_b_total_value=team_b_total,
                value_difference=value_difference,
                value_difference_percentage=value_diff_percentage,
                team_a_player_values=team_a_values,
                team_b_player_values=team_b_values,
                fairness_score=fairness_score,
                fairness_level=fairness_level,
                trade_grade_team_a=grade_a,
                trade_grade_team_b=grade_b,
                position_impact=position_impact,
                roster_improvement_team_a=roster_impact_a,
                roster_improvement_team_b=roster_impact_b,
                risk_assessment=risk_assessment,
                recommendation=recommendation,
                reasoning=reasoning,
                concerns=concerns,
                evaluated_at=datetime.utcnow(),
                confidence_level=confidence,
            )

            logger.info(
                "Trade evaluation completed",
                extra={
                    "trade_id": trade_id,
                    "fairness_level": fairness_level.value,
                    "fairness_score": fairness_score,
                    "confidence": confidence,
                },
            )

            return analysis

        except Exception as e:
            logger.error(f"Trade evaluation failed: {e}")
            raise TradeEvaluationError(f"Failed to evaluate trade: {e}")

    async def _calculate_player_values(
        self,
        player_ids: list[str],
        scoring_rules: dict[str, Any],
        player_stats: dict[str, dict[str, Any]],
    ) -> list[PlayerValue]:
        """Calculate comprehensive value for each player."""
        player_values = []

        for player_id in player_ids:
            try:
                stats = player_stats.get(player_id, {})
                if not stats:
                    logger.warning(f"No stats found for player {player_id}")
                    continue

                # Base value from projected fantasy points
                base_value = self._calculate_base_value(stats, scoring_rules)

                # Position scarcity multiplier
                position = stats.get("position", "")
                scarcity_multiplier = self.position_scarcity.get(position, 1.0)

                # Injury risk penalty
                injury_penalty = self._calculate_injury_penalty(stats)

                # Recent performance modifier
                performance_modifier = self._calculate_performance_modifier(stats)

                # Projection confidence
                confidence = self._calculate_projection_confidence(stats)

                # Calculate final value
                final_value = (
                    base_value
                    * scarcity_multiplier
                    * (1 - injury_penalty)
                    * (1 + performance_modifier)
                )

                # Determine value tier
                value_tier = self._determine_value_tier(final_value, player_stats)

                player_value = PlayerValue(
                    player_id=player_id,
                    base_value=base_value,
                    position_scarcity_multiplier=scarcity_multiplier,
                    injury_risk_penalty=injury_penalty,
                    recent_performance_modifier=performance_modifier,
                    projection_confidence=confidence,
                    final_value=final_value,
                    value_tier=value_tier,
                )

                player_values.append(player_value)

            except Exception as e:
                logger.warning(f"Failed to calculate value for player {player_id}: {e}")
                continue

        return player_values

    def _calculate_base_value(
        self,
        stats: dict[str, Any],
        scoring_rules: dict[str, Any],
    ) -> float:
        """Calculate base fantasy value for a player."""
        try:
            # Get projected stats
            projections = stats.get("projections", {})
            if not projections:
                # Fall back to season stats with projection factor
                season_stats = stats.get("season_stats", {})
                projections = {
                    k: v * 0.85
                    for k, v in season_stats.items()
                    if isinstance(v, (int, float))
                }

            # Calculate fantasy points based on scoring rules
            fantasy_points = 0.0

            for stat_name, points_per in scoring_rules.items():
                if stat_name in projections:
                    fantasy_points += projections[stat_name] * points_per

            # Weekly value (assuming 17-week season)
            weekly_value = fantasy_points / 17.0

            return max(0.0, weekly_value)

        except Exception as e:
            logger.warning(f"Failed to calculate base value: {e}")
            return 0.0

    def _calculate_injury_penalty(self, stats: dict[str, Any]) -> float:
        """Calculate injury risk penalty (0-1 scale)."""
        injury_status = stats.get("injury_status", "healthy").lower()

        injury_penalties = {
            "healthy": 0.0,
            "questionable": 0.1,
            "doubtful": 0.25,
            "out": 0.5,
            "ir": 0.8,
            "suspended": 0.3,
        }

        return injury_penalties.get(injury_status, 0.0)

    def _calculate_performance_modifier(self, stats: dict[str, Any]) -> float:
        """Calculate recent performance modifier (-0.3 to +0.3)."""
        try:
            recent_games = stats.get("recent_games", [])
            if len(recent_games) < 3:
                return 0.0

            # Compare recent average to season average
            recent_avg = sum(
                g.get("fantasy_points", 0) for g in recent_games[-5:]
            ) / min(5, len(recent_games))
            season_avg = stats.get("season_stats", {}).get(
                "avg_fantasy_points", recent_avg
            )

            if season_avg == 0:
                return 0.0

            improvement = (recent_avg - season_avg) / season_avg
            return max(-0.3, min(0.3, improvement))

        except Exception as e:
            logger.warning(f"Failed to calculate performance modifier: {e}")
            return 0.0

    def _calculate_projection_confidence(self, stats: dict[str, Any]) -> float:
        """Calculate confidence in projections (0-1 scale)."""
        factors = []

        # Games played factor
        games_played = stats.get("season_stats", {}).get("games_played", 0)
        games_factor = min(1.0, games_played / 10.0)  # Full confidence at 10+ games
        factors.append(games_factor)

        # Consistency factor (based on game log variance)
        recent_games = stats.get("recent_games", [])
        if len(recent_games) >= 3:
            points = [g.get("fantasy_points", 0) for g in recent_games]
            if points and max(points) > 0:
                consistency = 1.0 - (max(points) - min(points)) / max(points)
                factors.append(max(0.3, consistency))

        # Age factor (prime years have higher confidence)
        age = stats.get("age", 28)
        age_factor = 1.0 - abs(age - 28) * 0.02  # Peak at 28, decline 2% per year off
        factors.append(max(0.5, age_factor))

        return sum(factors) / len(factors) if factors else 0.7

    def _determine_value_tier(
        self, value: float, all_player_stats: dict[str, dict[str, Any]]
    ) -> str:
        """Determine player value tier based on league context."""
        # This would ideally use league-wide value distribution
        # For now, use simple thresholds
        if value >= 20:
            return "elite"
        elif value >= 15:
            return "high"
        elif value >= 10:
            return "medium"
        elif value >= 5:
            return "low"
        else:
            return "waiver"

    def _determine_fairness_level(self, value_diff_percentage: float) -> FairnessLevel:
        """Determine trade fairness level based on value difference."""
        for level, threshold in self.fairness_thresholds.items():
            if value_diff_percentage <= threshold:
                return level
        return FairnessLevel.VERY_UNFAIR

    async def _calculate_roster_impact(
        self,
        team_id: str,
        players_out: list[str],
        players_in: list[str],
        current_rosters: dict[str, list[dict[str, Any]]],
        player_stats: dict[str, dict[str, Any]],
    ) -> float:
        """Calculate roster improvement percentage for a team."""
        try:
            current_roster = current_rosters.get(team_id, [])
            if not current_roster:
                return 0.0

            # Calculate current roster value
            current_value = 0.0
            for player in current_roster:
                player_id = player.get("player_id")
                if player_id in player_stats:
                    stats = player_stats[player_id]
                    value = self._calculate_base_value(
                        stats, {}
                    )  # Simplified for roster calc
                    current_value += value

            # Calculate post-trade roster value
            post_trade_value = current_value

            # Subtract outgoing players
            for player_id in players_out:
                if player_id in player_stats:
                    stats = player_stats[player_id]
                    value = self._calculate_base_value(stats, {})
                    post_trade_value -= value

            # Add incoming players
            for player_id in players_in:
                if player_id in player_stats:
                    stats = player_stats[player_id]
                    value = self._calculate_base_value(stats, {})
                    post_trade_value += value

            # Calculate improvement percentage
            if current_value > 0:
                improvement = ((post_trade_value - current_value) / current_value) * 100
                return improvement
            else:
                return 0.0

        except Exception as e:
            logger.warning(f"Failed to calculate roster impact: {e}")
            return 0.0

    def _analyze_position_impact(
        self,
        all_player_values: list[PlayerValue],
        team_a_players: list[str],
        team_b_players: list[str],
    ) -> dict[str, dict[str, float]]:
        """Analyze the positional impact of the trade."""
        position_impact: dict[str, dict[str, float]] = {
            "team_a": {},
            "team_b": {},
        }

        # Group players by position for each team
        for player_value in all_player_values:
            player_id = player_value.player_id
            position = "UNKNOWN"  # Would get from player stats
            value = player_value.final_value

            if player_id in team_a_players:
                # Team A is losing this player
                if position not in position_impact["team_a"]:
                    position_impact["team_a"][position] = 0.0
                position_impact["team_a"][position] -= value
            elif player_id in team_b_players:
                # Team A is gaining this player (team B is losing)
                if position not in position_impact["team_a"]:
                    position_impact["team_a"][position] = 0.0
                position_impact["team_a"][position] += value

                # Team B is losing this player
                if position not in position_impact["team_b"]:
                    position_impact["team_b"][position] = 0.0
                position_impact["team_b"][position] -= value

        # Add what team B gains (team A players)
        for player_value in all_player_values:
            player_id = player_value.player_id
            if player_id in team_a_players:
                position = "UNKNOWN"  # Would get from player stats
                value = player_value.final_value
                if position not in position_impact["team_b"]:
                    position_impact["team_b"][position] = 0.0
                position_impact["team_b"][position] += value

        return position_impact

    def _assess_trade_risks(
        self,
        all_player_values: list[PlayerValue],
        player_stats: dict[str, dict[str, Any]],
    ) -> dict[str, Any]:
        """Assess various risks associated with the trade."""
        risks = {
            "injury_risk": 0.0,
            "age_risk": 0.0,
            "consistency_risk": 0.0,
            "high_risk_players": [],
            "low_confidence_players": [],
        }

        for player_value in all_player_values:
            player_id = player_value.player_id
            stats = player_stats.get(player_id, {})

            # Injury risk
            if player_value.injury_risk_penalty > 0.2:
                risks["injury_risk"] += player_value.injury_risk_penalty
                risks["high_risk_players"].append(
                    {
                        "player_id": player_id,
                        "risk_type": "injury",
                        "risk_level": player_value.injury_risk_penalty,
                    }
                )

            # Age risk
            age = stats.get("age", 28)
            if age > 32 or age < 23:
                age_risk = abs(age - 28) * 0.1
                risks["age_risk"] += age_risk
                risks["high_risk_players"].append(
                    {
                        "player_id": player_id,
                        "risk_type": "age",
                        "risk_level": age_risk,
                    }
                )

            # Low confidence projections
            if player_value.projection_confidence < 0.6:
                risks["low_confidence_players"].append(
                    {
                        "player_id": player_id,
                        "confidence": player_value.projection_confidence,
                    }
                )

        return risks

    def _calculate_trade_grade(
        self,
        roster_improvement: float,
        fairness_score: float,
        is_team_a: bool,
    ) -> str:
        """Calculate letter grade for the trade."""
        # Combine roster improvement and fairness
        combined_score = (roster_improvement + fairness_score) / 2

        if combined_score >= 80:
            return "A"
        elif combined_score >= 70:
            return "B"
        elif combined_score >= 60:
            return "C"
        elif combined_score >= 50:
            return "D"
        else:
            return "F"

    def _generate_recommendations(
        self,
        fairness_level: FairnessLevel,
        roster_impact_a: float,
        roster_impact_b: float,
        risk_assessment: dict[str, Any],
    ) -> tuple[str, list[str], list[str]]:
        """Generate trade recommendations and analysis."""
        reasoning = []
        concerns = []

        # Fairness assessment
        if fairness_level in [FairnessLevel.VERY_FAIR, FairnessLevel.FAIR]:
            recommendation = "APPROVE"
            reasoning.append(
                f"Trade is {fairness_level.value.replace('_', ' ')} in terms of player value exchange"
            )
        elif fairness_level == FairnessLevel.SLIGHTLY_UNFAIR:
            recommendation = "REVIEW"
            reasoning.append("Trade has minor value imbalance but may be acceptable")
        else:
            recommendation = "REJECT"
            concerns.append(
                f"Trade is {fairness_level.value.replace('_', ' ')} - significant value imbalance"
            )

        # Roster impact analysis
        if abs(roster_impact_a) > 20 or abs(roster_impact_b) > 20:
            if roster_impact_a > 20:
                reasoning.append("Team A significantly improves their roster")
            if roster_impact_b > 20:
                reasoning.append("Team B significantly improves their roster")
            if min(roster_impact_a, roster_impact_b) < -15:
                concerns.append("One team may be significantly weakened by this trade")

        # Risk factors
        if risk_assessment["injury_risk"] > 0.5:
            concerns.append("High injury risk among traded players")

        if len(risk_assessment["high_risk_players"]) > 2:
            concerns.append("Multiple high-risk players involved in trade")

        if len(risk_assessment["low_confidence_players"]) > 1:
            concerns.append("Low confidence in projections for multiple players")

        # Default reasoning if none provided
        if not reasoning:
            reasoning.append("Standard trade evaluation completed")

        return recommendation, reasoning, concerns

    def _calculate_confidence_level(
        self,
        all_player_values: list[PlayerValue],
        player_stats: dict[str, dict[str, Any]],
    ) -> float:
        """Calculate overall confidence in the trade evaluation."""
        if not all_player_values:
            return 0.0

        confidence_scores = [pv.projection_confidence for pv in all_player_values]
        avg_confidence = sum(confidence_scores) / len(confidence_scores)

        # Adjust for data completeness
        complete_data_players = 0
        for pv in all_player_values:
            stats = player_stats.get(pv.player_id, {})
            if stats.get("season_stats") and stats.get("projections"):
                complete_data_players += 1

        data_completeness = complete_data_players / len(all_player_values)

        return (avg_confidence + data_completeness) / 2


# Export aliases for backward compatibility
FairnessRating = FairnessLevel
TradeRecommendation = TradeAnalysis

# Global evaluator instance
_trade_evaluator: TradeEvaluator | None = None


def get_trade_evaluator() -> TradeEvaluator:
    """Get the global trade evaluator instance."""
    global _trade_evaluator
    if _trade_evaluator is None:
        _trade_evaluator = TradeEvaluator()
    return _trade_evaluator


def reset_trade_evaluator() -> None:
    """Reset the global evaluator (useful for testing)."""
    global _trade_evaluator
    _trade_evaluator = None
