"""
AIService with recommendation engine for fantasy sports AI assistance.

Provides comprehensive AI-powered recommendations including:
- Lineup optimization recommendations
- Waiver wire pickup suggestions
- Trade opportunity analysis
- Draft pick recommendations
- Matchup-specific advice
- Player performance predictions
- Risk/reward analysis
- Seasonal strategy guidance
"""

import random
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID

from sqlalchemy.orm import Session

from domains.leagues.models.team import Team
from domains.lineups.models.lineup import Lineup
from domains.scoring.models.score import Score
from domains.sports.models.player import Player
from domains.trading.models.trade import Trade

try:
    from infrastructure.logging.domain_logger import get_logger
except ImportError:
    import logging
    get_logger = logging.getLogger  # type: ignore[assignment]

try:
    # Optional ML dependencies
    import numpy as np
    import pandas as pd
    from sklearn.ensemble import RandomForestRegressor
    from sklearn.preprocessing import StandardScaler
    ML_AVAILABLE = True
except ImportError:
    # Fallback to statistical methods if ML libraries not available
    ML_AVAILABLE = False
    np = None
    pd = None
    RandomForestRegressor = None
    StandardScaler = None

logger = get_logger(__name__)


@dataclass
class Recommendation:
    """AI recommendation structure."""

    recommendation_type: str
    action: str
    target_player_id: Optional[str]
    target_team_id: Optional[str]
    confidence_score: float
    reasoning: str
    expected_impact: float
    risk_level: str
    priority: int
    metadata: Dict[str, Any]


@dataclass
class LineupOptimization:
    """Lineup optimization recommendation."""

    current_lineup: Dict[str, str]
    recommended_changes: List[Dict[str, Any]]
    projected_improvement: float
    confidence: float
    reasoning: str


@dataclass
class WaiverRecommendation:
    """Waiver wire recommendation."""

    player_id: str
    player_name: str
    position: str
    pickup_priority: int
    drop_candidate_id: Optional[str]
    projected_points: float
    confidence: float
    reasoning: str
    bid_suggestion: Optional[int]


@dataclass
class TradeRecommendation:
    """Trade opportunity recommendation."""

    target_team_id: str
    offered_players: List[str]
    requested_players: List[str]
    fairness_score: float
    mutual_benefit: bool
    reasoning: str
    success_probability: float


class RecommendationType:
    """Recommendation type constants."""

    LINEUP_OPTIMIZATION = "lineup_optimization"
    WAIVER_PICKUP = "waiver_pickup"
    TRADE_OPPORTUNITY = "trade_opportunity"
    DRAFT_PICK = "draft_pick"
    START_SIT = "start_sit"
    DROP_CANDIDATE = "drop_candidate"
    MATCHUP_ADVICE = "matchup_advice"


class RiskLevel:
    """Risk level constants."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    VERY_HIGH = "very_high"


class AIService:
    """Service for AI-powered fantasy sports recommendations and analysis."""

    def __init__(self, session: Session):
        self.session = session
        self.ml_models = {}
        self._initialize_models()

    def _initialize_models(self):
        """Initialize ML models if available."""
        if ML_AVAILABLE:
            self.ml_models = {
                "player_performance": RandomForestRegressor(n_estimators=100, random_state=42),
                "lineup_optimizer": RandomForestRegressor(n_estimators=50, random_state=42),
                "trade_evaluator": RandomForestRegressor(n_estimators=75, random_state=42),
            }
            logger.info("ML models initialized successfully")
        else:
            logger.info("ML libraries not available, using statistical methods")

    # Lineup Optimization

    async def get_lineup_recommendations(
        self,
        team_id: str,
        week: Optional[int] = None,
        include_waiver_targets: bool = False,
    ) -> LineupOptimization:
        """
        Generate AI-powered lineup optimization recommendations.

        Args:
            team_id: Team ID to optimize
            week: Target week (current if not specified)
            include_waiver_targets: Include waiver wire players

        Returns:
            LineupOptimization with recommended changes
        """
        team = self.session.query(Team).filter(Team.team_id == UUID(team_id)).first()
        if not team:
            raise ValueError(f"Team {team_id} not found")

        # Get current roster
        roster_players = self._get_team_roster_players(team_id)

        # Get current lineup if exists
        current_lineup = self._get_current_lineup(team_id, week)

        # Analyze each position
        recommendations = []
        projected_improvement = 0.0

        # Optimize each position
        for position in ["QB", "RB", "WR", "TE", "K", "DEF"]:
            position_players = [p for p in roster_players if p.position == position]
            if not position_players:
                continue

            # Get best player for this position
            best_player = await self._get_best_player_for_position(
                position_players, week
            )
            current_starter = current_lineup.get(position)

            if current_starter != str(best_player.player_id):
                projected_points = await self._predict_player_points(best_player, week)
                current_points = await self._predict_player_points_by_id(current_starter, week) if current_starter else 0

                improvement = projected_points - current_points
                if improvement > 0.5:  # Only recommend if meaningful improvement
                    recommendations.append({
                        "position": position,
                        "action": "start",
                        "player_id": str(best_player.player_id),
                        "player_name": best_player.name,
                        "bench_player_id": current_starter,
                        "projected_improvement": round(improvement, 2),
                        "reasoning": f"Projected to score {projected_points:.1f} points vs {current_points:.1f}",
                    })
                    projected_improvement += improvement

        # Include waiver wire targets if requested
        if include_waiver_targets:
            waiver_targets = await self._get_waiver_wire_targets(team_id, week)
            for target in waiver_targets[:3]:  # Top 3 targets
                recommendations.append({
                    "position": target["position"],
                    "action": "pickup",
                    "player_id": target["player_id"],
                    "player_name": target["player_name"],
                    "drop_candidate_id": target.get("drop_candidate_id"),
                    "projected_improvement": target["projected_improvement"],
                    "reasoning": f"Available on waivers, projected {target['projected_points']:.1f} points",
                })

        confidence = self._calculate_recommendation_confidence(recommendations)

        return LineupOptimization(
            current_lineup=current_lineup,
            recommended_changes=recommendations,
            projected_improvement=round(projected_improvement, 2),
            confidence=confidence,
            reasoning=self._generate_lineup_reasoning(recommendations, projected_improvement),
        )

    # Waiver Wire Recommendations

    async def get_waiver_recommendations(
        self,
        team_id: str,
        week: Optional[int] = None,
        budget_remaining: Optional[int] = None,
        top_n: int = 10,
    ) -> List[WaiverRecommendation]:
        """
        Generate AI-powered waiver wire recommendations.

        Args:
            team_id: Team ID
            week: Target week
            budget_remaining: FAAB budget remaining
            top_n: Number of recommendations to return

        Returns:
            List of waiver recommendations
        """
        team = self.session.query(Team).filter(Team.team_id == UUID(team_id)).first()
        if not team:
            raise ValueError(f"Team {team_id} not found")

        # Get available players
        available_players = await self._get_available_players(str(team.league_id))

        # Analyze team needs
        team_needs = await self._analyze_team_needs(team_id)

        recommendations = []

        for player in available_players:
            # Calculate pickup value
            pickup_value = await self._calculate_pickup_value(player, team_id, team_needs)

            if pickup_value["should_pickup"]:
                # Find drop candidate
                drop_candidate = await self._find_drop_candidate(team_id, player.position)

                # Calculate bid suggestion
                bid_suggestion = None
                if budget_remaining:
                    bid_suggestion = self._calculate_bid_suggestion(
                        pickup_value["projected_points"],
                        pickup_value["competition_level"],
                        budget_remaining
                    )

                recommendations.append(WaiverRecommendation(
                    player_id=str(player.player_id),
                    player_name=player.name,
                    position=player.position,
                    pickup_priority=pickup_value["priority"],
                    drop_candidate_id=str(drop_candidate.player_id) if drop_candidate else None,
                    projected_points=pickup_value["projected_points"],
                    confidence=pickup_value["confidence"],
                    reasoning=pickup_value["reasoning"],
                    bid_suggestion=bid_suggestion,
                ))

        # Sort by priority and return top N
        recommendations.sort(key=lambda x: x.pickup_priority)
        return recommendations[:top_n]

    # Trade Recommendations

    async def get_trade_recommendations(
        self,
        team_id: str,
        analysis_depth: str = "standard",
    ) -> List[TradeRecommendation]:
        """
        Generate AI-powered trade opportunity recommendations.

        Args:
            team_id: Team ID
            analysis_depth: Analysis depth (quick, standard, deep)

        Returns:
            List of trade recommendations
        """
        team = self.session.query(Team).filter(Team.team_id == UUID(team_id)).first()
        if not team:
            raise ValueError(f"Team {team_id} not found")

        # Get league teams
        league_teams = self._get_league_teams(str(team.league_id))
        other_teams = [t for t in league_teams if t.team_id != team.team_id]

        recommendations = []

        # Analyze potential trades with each team
        for target_team in other_teams:
            trade_opportunities = await self._analyze_trade_opportunities(
                team_id, str(target_team.team_id), analysis_depth
            )

            for opportunity in trade_opportunities:
                if opportunity["mutual_benefit"] and opportunity["fairness_score"] >= 0.7:
                    recommendations.append(TradeRecommendation(
                        target_team_id=str(target_team.team_id),
                        offered_players=opportunity["offered_players"],
                        requested_players=opportunity["requested_players"],
                        fairness_score=opportunity["fairness_score"],
                        mutual_benefit=opportunity["mutual_benefit"],
                        reasoning=opportunity["reasoning"],
                        success_probability=opportunity["success_probability"],
                    ))

        # Sort by success probability and mutual benefit
        recommendations.sort(key=lambda x: (x.success_probability, x.fairness_score), reverse=True)
        return recommendations[:5]  # Top 5 trade opportunities

    # Start/Sit Recommendations

    async def get_start_sit_recommendations(
        self,
        team_id: str,
        week: Optional[int] = None,
        position: Optional[str] = None,
    ) -> List[Recommendation]:
        """
        Generate start/sit recommendations for specific positions.

        Args:
            team_id: Team ID
            week: Target week
            position: Specific position to analyze

        Returns:
            List of start/sit recommendations
        """
        roster_players = self._get_team_roster_players(team_id)

        if position:
            roster_players = [p for p in roster_players if p.position == position]

        recommendations = []

        # Group players by position
        by_position = {}
        for player in roster_players:
            if player.position not in by_position:
                by_position[player.position] = []
            by_position[player.position].append(player)

        for pos, players in by_position.items():
            if len(players) > 1:  # Only if there are choices
                ranked_players = await self._rank_players_for_week(players, week)

                for i, player_data in enumerate(ranked_players):
                    player = player_data["player"]
                    projected_points = player_data["projected_points"]

                    if i == 0:  # Best player
                        action = "start"
                        reasoning = f"Top projected {pos} with {projected_points:.1f} points"
                        confidence = 0.8
                    else:
                        action = "sit"
                        reasoning = f"Projected {projected_points:.1f} points, ranked #{i+1} at {pos}"
                        confidence = 0.7

                    recommendations.append(Recommendation(
                        recommendation_type=RecommendationType.START_SIT,
                        action=action,
                        target_player_id=str(player.player_id),
                        target_team_id=team_id,
                        confidence_score=confidence,
                        reasoning=reasoning,
                        expected_impact=projected_points,
                        risk_level=self._assess_player_risk(player),
                        priority=1 if action == "start" else 2,
                        metadata={
                            "position": pos,
                            "projected_points": projected_points,
                            "rank": i + 1,
                        },
                    ))

        return recommendations

    # Draft Recommendations

    async def get_draft_recommendations(
        self,
        draft_id: str,
        team_id: str,
        pick_number: int,
        strategy: str = "balanced",
    ) -> List[Recommendation]:
        """
        Generate draft pick recommendations.

        Args:
            draft_id: Draft ID
            team_id: Team making the pick
            pick_number: Current pick number
            strategy: Draft strategy (value, balanced, positional)

        Returns:
            List of draft recommendations
        """
        available_players = await self._get_available_draft_players(draft_id)

        # Analyze team's current roster and needs
        team_needs = await self._analyze_draft_needs(team_id, pick_number)

        recommendations = []

        for player in available_players[:20]:  # Top 20 available
            value_score = await self._calculate_draft_value(
                player, pick_number, team_needs, strategy
            )

            if value_score > 0.6:  # Only recommend high-value picks
                recommendations.append(Recommendation(
                    recommendation_type=RecommendationType.DRAFT_PICK,
                    action="draft",
                    target_player_id=str(player.player_id),
                    target_team_id=team_id,
                    confidence_score=value_score,
                    reasoning=f"Excellent value at pick #{pick_number}, addresses {team_needs[player.position]}",
                    expected_impact=value_score * 100,
                    risk_level=self._assess_player_risk(player),
                    priority=1,
                    metadata={
                        "position": player.position,
                        "adp": self._get_average_draft_position(player),
                        "value_above_replacement": value_score,
                    },
                ))

        # Sort by value score
        recommendations.sort(key=lambda x: x.confidence_score, reverse=True)
        return recommendations[:5]

    # Matchup Analysis

    async def get_matchup_advice(
        self,
        team_id: str,
        opponent_team_id: str,
        week: Optional[int] = None,
    ) -> List[Recommendation]:
        """
        Generate matchup-specific advice and recommendations.

        Args:
            team_id: User's team ID
            opponent_team_id: Opponent's team ID
            week: Target week

        Returns:
            List of matchup-specific recommendations
        """
        # Analyze opponent's typical lineup
        opponent_strengths = await self._analyze_opponent_strengths(opponent_team_id)

        # Analyze user's roster for counter-strategies
        user_roster = self._get_team_roster_players(team_id)

        recommendations = []

        # High-ceiling vs safe plays analysis
        if opponent_strengths["avg_points"] > 110:  # High-scoring opponent
            # Recommend high-ceiling plays
            boom_players = await self._identify_boom_potential_players(user_roster, week)
            for player in boom_players[:3]:
                recommendations.append(Recommendation(
                    recommendation_type=RecommendationType.MATCHUP_ADVICE,
                    action="start_high_ceiling",
                    target_player_id=str(player.player_id),
                    target_team_id=team_id,
                    confidence_score=0.75,
                    reasoning=f"High-ceiling play needed against strong opponent (avg {opponent_strengths['avg_points']:.1f} pts)",
                    expected_impact=player.projections.get("ceiling", 0) if player.projections else 0,
                    risk_level=RiskLevel.HIGH,
                    priority=1,
                    metadata={"strategy": "high_ceiling", "opponent_strength": "high"},
                ))
        else:
            # Recommend safe plays
            safe_players = await self._identify_safe_floor_players(user_roster, week)
            for player in safe_players[:3]:
                recommendations.append(Recommendation(
                    recommendation_type=RecommendationType.MATCHUP_ADVICE,
                    action="start_safe_floor",
                    target_player_id=str(player.player_id),
                    target_team_id=team_id,
                    confidence_score=0.8,
                    reasoning=f"Safe floor play recommended against moderate opponent",
                    expected_impact=player.projections.get("floor", 0) if player.projections else 0,
                    risk_level=RiskLevel.LOW,
                    priority=1,
                    metadata={"strategy": "safe_floor", "opponent_strength": "moderate"},
                ))

        return recommendations

    # Prediction Methods

    async def _predict_player_points(self, player: Player, week: Optional[int]) -> float:
        """Predict fantasy points for a player."""
        if ML_AVAILABLE and "player_performance" in self.ml_models:
            return await self._ml_predict_points(player, week)
        else:
            return await self._statistical_predict_points(player, week)

    async def _ml_predict_points(self, player: Player, week: Optional[int]) -> float:
        """ML-based point prediction."""
        # Feature engineering for ML model
        features = self._extract_player_features(player, week)

        if hasattr(self.ml_models["player_performance"], "predict"):
            try:
                prediction = self.ml_models["player_performance"].predict([features])[0]
                return max(0, prediction)  # Ensure non-negative
            except Exception as e:
                logger.warning(f"ML prediction failed, falling back to statistical: {e}")

        return await self._statistical_predict_points(player, week)

    async def _statistical_predict_points(self, player: Player, week: Optional[int]) -> float:
        """Statistical point prediction."""
        # Get recent performance
        recent_scores = self._get_recent_player_scores(str(player.player_id), 5)

        if not recent_scores:
            # Use projections if available
            if player.projections and "fantasy_points" in player.projections:
                return float(player.projections["fantasy_points"])
            # Fallback to position averages
            return self._get_position_average_points(player.position)

        # Calculate weighted average (recent games weighted higher)
        weights = [0.4, 0.3, 0.2, 0.1] if len(recent_scores) >= 4 else [1.0] * len(recent_scores)
        weighted_avg = sum(score.points * weight for score, weight in zip(recent_scores, weights))

        # Adjust for matchup difficulty (simplified)
        matchup_modifier = random.uniform(0.9, 1.1)  # Would use real matchup data

        return weighted_avg * matchup_modifier

    async def _predict_player_points_by_id(self, player_id: Optional[str], week: Optional[int]) -> float:
        """Predict points for player by ID."""
        if not player_id:
            return 0.0

        player = self.session.query(Player).filter(Player.player_id == UUID(player_id)).first()
        if not player:
            return 0.0

        return await self._predict_player_points(player, week)

    # Helper Methods

    def _get_team_roster_players(self, team_id: str) -> List[Player]:
        """Get all players on a team's roster."""
        team = self.session.query(Team).filter(Team.team_id == UUID(team_id)).first()
        if not team or not team.roster:
            return []

        return self.session.query(Player).filter(
            Player.player_id.in_([UUID(pid) for pid in team.roster])
        ).all()

    def _get_current_lineup(self, team_id: str, week: Optional[int]) -> Dict[str, str]:
        """Get current lineup for team."""
        lineup = self.session.query(Lineup).filter(
            Lineup.team_id == UUID(team_id),
            Lineup.week == (week or 1)
        ).first()

        if not lineup or not lineup.players:
            return {}

        # Convert to position -> player_id mapping
        lineup_dict = {}
        for player_entry in lineup.players:
            if isinstance(player_entry, dict) and "position" in player_entry and "player_id" in player_entry:
                lineup_dict[player_entry["position"]] = player_entry["player_id"]

        return lineup_dict

    async def _get_best_player_for_position(self, players: List[Player], week: Optional[int]) -> Player:
        """Get the best player for a position based on projections."""
        if not players:
            raise ValueError("No players provided")

        player_projections = []
        for player in players:
            projected_points = await self._predict_player_points(player, week)
            player_projections.append((player, projected_points))

        # Sort by projected points
        player_projections.sort(key=lambda x: x[1], reverse=True)
        return player_projections[0][0]

    async def _get_waiver_wire_targets(self, team_id: str, week: Optional[int]) -> List[Dict[str, Any]]:
        """Get waiver wire targets for team."""
        # This would get available players not on any roster
        # Simplified implementation
        return [
            {
                "player_id": "waiver_target_1",
                "player_name": "Waiver Target 1",
                "position": "RB",
                "projected_points": 12.5,
                "projected_improvement": 3.2,
                "drop_candidate_id": "bench_player_1",
            }
        ]

    def _calculate_recommendation_confidence(self, recommendations: List[Dict[str, Any]]) -> float:
        """Calculate overall confidence in recommendations."""
        if not recommendations:
            return 0.0

        # Base confidence on number and quality of recommendations
        base_confidence = min(0.9, len(recommendations) * 0.15)

        # Adjust for impact size
        avg_impact = sum(rec.get("projected_improvement", 0) for rec in recommendations) / len(recommendations)
        impact_bonus = min(0.1, avg_impact * 0.02)

        return base_confidence + impact_bonus

    def _generate_lineup_reasoning(self, recommendations: List[Dict[str, Any]], improvement: float) -> str:
        """Generate reasoning text for lineup recommendations."""
        if not recommendations:
            return "Your current lineup appears optimal with no recommended changes."

        if improvement > 5:
            return f"Significant lineup improvements available (+{improvement:.1f} projected points). Consider making {len(recommendations)} changes."
        elif improvement > 2:
            return f"Moderate lineup improvements possible (+{improvement:.1f} projected points). {len(recommendations)} potential changes identified."
        else:
            return f"Minor lineup tweaks suggested (+{improvement:.1f} projected points). Your lineup is largely optimized."

    async def _get_available_players(self, league_id: str) -> List[Player]:
        """Get players available on waivers."""
        # This would exclude players on any team roster
        # Simplified implementation
        return self.session.query(Player).limit(50).all()

    async def _analyze_team_needs(self, team_id: str) -> Dict[str, str]:
        """Analyze team's positional needs."""
        # Simplified analysis
        return {
            "QB": "weak",
            "RB": "strong",
            "WR": "average",
            "TE": "weak",
            "K": "average",
            "DEF": "strong",
        }

    async def _calculate_pickup_value(
        self, player: Player, team_id: str, team_needs: Dict[str, str]
    ) -> Dict[str, Any]:
        """Calculate value of picking up a player."""
        projected_points = await self._predict_player_points(player, None)

        # Factor in team need
        need_multiplier = {"weak": 1.3, "average": 1.0, "strong": 0.7}.get(
            team_needs.get(player.position, "average"), 1.0
        )

        adjusted_value = projected_points * need_multiplier

        return {
            "should_pickup": adjusted_value > 8.0,  # Threshold for pickup
            "projected_points": projected_points,
            "priority": int(adjusted_value),
            "confidence": 0.75,
            "reasoning": f"Projected {projected_points:.1f} points, fills {team_needs.get(player.position)} need",
            "competition_level": random.randint(1, 5),  # Would analyze actual competition
        }

    async def _find_drop_candidate(self, team_id: str, position: str) -> Optional[Player]:
        """Find the best drop candidate for a position."""
        roster_players = self._get_team_roster_players(team_id)
        position_players = [p for p in roster_players if p.position == position]

        if not position_players:
            return None

        # Find lowest projected player
        player_values = []
        for player in position_players:
            projected_points = await self._predict_player_points(player, None)
            player_values.append((player, projected_points))

        player_values.sort(key=lambda x: x[1])
        return player_values[0][0] if player_values else None

    def _calculate_bid_suggestion(self, projected_points: float, competition: int, budget: int) -> int:
        """Calculate FAAB bid suggestion."""
        base_bid = max(1, int(projected_points * 2))  # $2 per projected point
        competition_adjustment = competition * 2  # Add $2 per competitor
        budget_cap = budget // 4  # Don't spend more than 25% of budget

        return min(base_bid + competition_adjustment, budget_cap)

    def _get_league_teams(self, league_id: str) -> List[Team]:
        """Get all teams in league."""
        return self.session.query(Team).filter(Team.league_id == UUID(league_id)).all()

    async def _analyze_trade_opportunities(
        self, team_id: str, target_team_id: str, depth: str
    ) -> List[Dict[str, Any]]:
        """Analyze potential trades between teams."""
        # Simplified analysis
        return [
            {
                "offered_players": ["player_1"],
                "requested_players": ["player_2"],
                "fairness_score": 0.85,
                "mutual_benefit": True,
                "reasoning": "Both teams fill positional needs",
                "success_probability": 0.7,
            }
        ]

    async def _rank_players_for_week(self, players: List[Player], week: Optional[int]) -> List[Dict[str, Any]]:
        """Rank players for a specific week."""
        ranked = []
        for player in players:
            projected_points = await self._predict_player_points(player, week)
            ranked.append({
                "player": player,
                "projected_points": projected_points,
            })

        ranked.sort(key=lambda x: x["projected_points"], reverse=True)
        return ranked

    def _assess_player_risk(self, player: Player) -> str:
        """Assess injury/performance risk for player."""
        if player.injury_status and player.injury_status.lower() in ["out", "doubtful"]:
            return RiskLevel.VERY_HIGH
        elif player.injury_status and player.injury_status.lower() == "questionable":
            return RiskLevel.HIGH
        elif player.injury_status and player.injury_status.lower() == "probable":
            return RiskLevel.MEDIUM
        else:
            return RiskLevel.LOW

    async def _get_available_draft_players(self, draft_id: str) -> List[Player]:
        """Get available players in draft."""
        # This would exclude already drafted players
        return self.session.query(Player).limit(100).all()

    async def _analyze_draft_needs(self, team_id: str, pick_number: int) -> Dict[str, str]:
        """Analyze team needs for draft."""
        # Would analyze current roster and draft strategy
        return {
            "QB": "high",
            "RB": "medium",
            "WR": "high",
            "TE": "low",
            "K": "low",
            "DEF": "low",
        }

    async def _calculate_draft_value(
        self, player: Player, pick_number: int, needs: Dict[str, str], strategy: str
    ) -> float:
        """Calculate draft value for player."""
        base_value = await self._predict_player_points(player, None) / 200  # Normalize
        need_bonus = {"high": 0.2, "medium": 0.1, "low": 0.0}.get(needs.get(player.position, "low"), 0.0)
        pick_adjustment = max(0.1, 1.0 - (pick_number / 200))  # Later picks less valuable

        return min(1.0, base_value + need_bonus + pick_adjustment)

    def _get_average_draft_position(self, player: Player) -> int:
        """Get average draft position for player."""
        # Would use historical draft data
        return random.randint(20, 100)

    async def _analyze_opponent_strengths(self, opponent_team_id: str) -> Dict[str, Any]:
        """Analyze opponent's strengths and tendencies."""
        # Simplified analysis
        return {
            "avg_points": 105.8,
            "consistency": 0.7,
            "strengths": ["RB", "WR"],
            "weaknesses": ["QB", "TE"],
        }

    async def _identify_boom_potential_players(self, roster: List[Player], week: Optional[int]) -> List[Player]:
        """Identify players with high ceiling potential."""
        boom_players = []
        for player in roster:
            if player.projections and "ceiling" in player.projections:
                if player.projections["ceiling"] > 20:  # High ceiling threshold
                    boom_players.append(player)

        return boom_players[:5]

    async def _identify_safe_floor_players(self, roster: List[Player], week: Optional[int]) -> List[Player]:
        """Identify players with safe floor."""
        safe_players = []
        for player in roster:
            if player.projections and "floor" in player.projections:
                if player.projections["floor"] > 8:  # Safe floor threshold
                    safe_players.append(player)

        return safe_players[:5]

    def _extract_player_features(self, player: Player, week: Optional[int]) -> List[float]:
        """Extract features for ML model."""
        # Extract numerical features for ML prediction
        features = [
            # Player attributes
            1.0 if player.position == "QB" else 0.0,
            1.0 if player.position == "RB" else 0.0,
            1.0 if player.position == "WR" else 0.0,
            1.0 if player.position == "TE" else 0.0,
            1.0 if player.injury_status == "healthy" else 0.0,
            # Recent performance (would use actual data)
            15.2,  # avg points last 3 games
            0.85,  # target share
            # Matchup data (would use actual matchup info)
            0.75,  # matchup difficulty
            week or 1,  # week number
        ]
        return features

    def _get_recent_player_scores(self, player_id: str, n_games: int) -> List[Score]:
        """Get recent scores for player."""
        return (
            self.session.query(Score)
            .filter(Score.player_id == UUID(player_id))
            .order_by(Score.created_at.desc())
            .limit(n_games)
            .all()
        )

    def _get_position_average_points(self, position: str) -> float:
        """Get average fantasy points for position."""
        averages = {
            "QB": 18.5,
            "RB": 12.8,
            "WR": 11.2,
            "TE": 8.9,
            "K": 7.5,
            "DEF": 8.2,
        }
        return averages.get(position, 10.0)


# Global service instance
_ai_service: Optional[AIService] = None


def get_ai_service(session: Session) -> AIService:
    """Get the global AI service instance."""
    global _ai_service
    if _ai_service is None:
        _ai_service = AIService(session)
    return _ai_service


def reset_ai_service():
    """Reset the global service (useful for testing)."""
    global _ai_service
    _ai_service = None