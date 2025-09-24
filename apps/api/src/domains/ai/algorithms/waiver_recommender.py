"""
Advanced waiver recommendation engine for fantasy sports.

Provides intelligent waiver wire analysis including:
- Player value identification and trend analysis
- Roster need assessment and gap analysis
- FAAB bidding strategy optimization
- Breakout player prediction and identification
- Injury replacement recommendations
- Schedule-based streaming suggestions
- League context and competition analysis
- Multi-week planning and strategy
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any, Set
from dataclasses import dataclass
from enum import Enum
from collections import defaultdict

try:
    from infrastructure.logging.domain_logger import get_logger
except ImportError:
    import logging
    get_logger = logging.getLogger  # type: ignore[assignment]

from domains.ai.models.performance_predictor import get_performance_predictor, Sport, PredictionResult
from domains.sports.services.sports_data_service import get_sports_data_service

logger = get_logger(__name__)


class RecommendationType(Enum):
    """Types of waiver recommendations."""
    IMMEDIATE_NEED = "immediate_need"      # Fill roster holes
    UPSIDE_PLAY = "upside_play"           # High ceiling players
    INJURY_REPLACEMENT = "injury_replacement"  # Replace injured players
    SCHEDULE_STREAM = "schedule_stream"    # Favorable matchups
    HANDCUFF = "handcuff"                 # Backup to owned players
    BREAKOUT_CANDIDATE = "breakout_candidate"  # Emerging players
    TRADE_ASSET = "trade_asset"           # Players with trade value


class WaiverPriority(Enum):
    """Waiver claim priority levels."""
    MUST_ADD = "must_add"           # Top priority
    HIGH = "high"                   # Strong consideration
    MEDIUM = "medium"               # Decent option
    LOW = "low"                     # Deep league only
    WATCH = "watch"                 # Monitor for next week


@dataclass
class WaiverTarget:
    """Waiver wire target player."""

    player_id: str
    name: str
    position: str
    team: str
    ownership_percentage: float

    # Projections and analysis
    projected_points_next_week: float
    projected_points_ros: float  # Rest of season
    breakout_probability: float

    # Roster fit
    recommendation_type: RecommendationType
    priority_level: WaiverPriority
    roster_need_score: float

    # FAAB strategy
    suggested_bid_percentage: float
    max_bid_percentage: float

    # Analysis
    value_score: float
    upside_score: float
    safety_score: float
    schedule_grade: str

    # Context
    reasoning: List[str]
    risk_factors: List[str]
    comparable_players: List[str]

    # Metadata
    generated_at: datetime
    confidence_score: float


@dataclass
class RosterAnalysis:
    """Analysis of current roster strengths and weaknesses."""

    team_id: str
    total_projected_points: float

    # Position analysis
    position_strengths: Dict[str, float]  # position -> strength score (0-1)
    position_weaknesses: Dict[str, float]  # position -> weakness score (0-1)

    # Weekly analysis
    bye_week_gaps: Dict[int, List[str]]  # week -> positions affected
    injury_risks: Dict[str, float]  # player_id -> risk score

    # Bench analysis
    bench_depth: Dict[str, int]  # position -> depth count
    streaming_needs: List[str]  # positions that need streaming

    # Advanced metrics
    ceiling_potential: float
    floor_stability: float
    consistency_score: float


@dataclass
class WaiverStrategy:
    """Comprehensive waiver strategy recommendation."""

    team_id: str
    league_id: str
    week: int

    # Targets by priority
    must_add_targets: List[WaiverTarget]
    high_priority_targets: List[WaiverTarget]
    medium_priority_targets: List[WaiverTarget]
    watch_list: List[WaiverTarget]

    # Strategy summary
    total_faab_recommended: float
    focus_positions: List[str]
    strategy_type: str  # aggressive, conservative, balanced

    # Roster analysis
    roster_analysis: RosterAnalysis

    # Meta analysis
    league_competition_level: float
    waiver_wire_strength: float

    generated_at: datetime


class WaiverRecommenderError(Exception):
    """Waiver recommender errors."""
    pass


class WaiverRecommendationEngine:
    """Advanced waiver wire recommendation system."""

    def __init__(self, sport: Sport):
        self.sport = sport
        self.performance_predictor = get_performance_predictor(sport)

        # Recommendation parameters
        self.ownership_threshold = 50.0  # Players above this are not waiver targets
        self.min_projection_improvement = 2.0  # Minimum point improvement to recommend

        # FAAB parameters
        self.faab_budget_allocation = {
            WaiverPriority.MUST_ADD: 0.15,    # 15% of budget
            WaiverPriority.HIGH: 0.08,        # 8% of budget
            WaiverPriority.MEDIUM: 0.05,      # 5% of budget
            WaiverPriority.LOW: 0.02,         # 2% of budget
        }

        # Sport-specific configurations
        self.position_configs = self._get_position_configs(sport)

        logger.info(f"Initialized waiver recommender for {sport.value}")

    def _get_position_configs(self, sport: Sport) -> Dict[str, Any]:
        """Get sport-specific position configurations."""
        configs = {
            Sport.NFL: {
                "positions": ["QB", "RB", "WR", "TE", "K", "DEF"],
                "skill_positions": ["QB", "RB", "WR", "TE"],
                "streaming_positions": ["K", "DEF", "QB"],  # Commonly streamed
                "handcuff_positions": ["RB"],
                "breakout_positions": ["WR", "RB", "TE"],
            },
            Sport.MLB: {
                "positions": ["C", "1B", "2B", "3B", "SS", "OF", "P"],
                "skill_positions": ["C", "1B", "2B", "3B", "SS", "OF"],
                "streaming_positions": ["P", "C"],
                "handcuff_positions": [],
                "breakout_positions": ["OF", "1B", "3B"],
            },
            Sport.WNBA: {
                "positions": ["PG", "SG", "SF", "PF", "C"],
                "skill_positions": ["PG", "SG", "SF", "PF", "C"],
                "streaming_positions": ["C", "PF"],
                "handcuff_positions": [],
                "breakout_positions": ["SG", "SF"],
            }
        }
        return configs.get(sport, configs[Sport.NFL])

    async def generate_waiver_strategy(self,
                                     team_id: str,
                                     league_id: str,
                                     current_roster: List[Dict[str, Any]],
                                     available_players: List[Dict[str, Any]],
                                     league_settings: Dict[str, Any],
                                     week: Optional[int] = None) -> WaiverStrategy:
        """
        Generate comprehensive waiver wire strategy.

        Args:
            team_id: Team requesting recommendations
            league_id: League context
            current_roster: Current team roster
            available_players: Available waiver wire players
            league_settings: League configuration
            week: Target week (current if None)

        Returns:
            WaiverStrategy: Complete waiver strategy
        """
        try:
            if week is None:
                week = self._get_current_week()

            logger.info(
                f"Generating waiver strategy",
                extra={
                    "team_id": team_id,
                    "league_id": league_id,
                    "sport": self.sport.value,
                    "week": week,
                    "available_players": len(available_players),
                }
            )

            # Analyze current roster
            roster_analysis = await self._analyze_roster(current_roster, week)

            # Filter and analyze available players
            waiver_candidates = await self._identify_waiver_candidates(
                available_players, roster_analysis, week
            )

            # Generate recommendations by priority
            recommendations = await self._generate_recommendations(
                waiver_candidates, roster_analysis, league_settings, week
            )

            # Calculate FAAB strategy
            faab_strategy = self._calculate_faab_strategy(
                recommendations, league_settings
            )

            # Analyze league context
            competition_level = await self._analyze_league_competition(
                league_id, available_players
            )

            waiver_wire_strength = self._assess_waiver_wire_strength(available_players)

            # Create strategy
            strategy = WaiverStrategy(
                team_id=team_id,
                league_id=league_id,
                week=week,
                must_add_targets=[r for r in recommendations if r.priority_level == WaiverPriority.MUST_ADD],
                high_priority_targets=[r for r in recommendations if r.priority_level == WaiverPriority.HIGH],
                medium_priority_targets=[r for r in recommendations if r.priority_level == WaiverPriority.MEDIUM],
                watch_list=[r for r in recommendations if r.priority_level == WaiverPriority.WATCH],
                total_faab_recommended=sum(r.suggested_bid_percentage for r in recommendations),
                focus_positions=self._identify_focus_positions(roster_analysis),
                strategy_type=self._determine_strategy_type(roster_analysis, recommendations),
                roster_analysis=roster_analysis,
                league_competition_level=competition_level,
                waiver_wire_strength=waiver_wire_strength,
                generated_at=datetime.utcnow(),
            )

            logger.info(
                f"Generated waiver strategy",
                extra={
                    "team_id": team_id,
                    "must_add": len(strategy.must_add_targets),
                    "high_priority": len(strategy.high_priority_targets),
                    "total_faab": strategy.total_faab_recommended,
                }
            )

            return strategy

        except Exception as e:
            logger.error(f"Waiver strategy generation failed: {e}")
            raise WaiverRecommenderError(f"Strategy generation failed: {e}")

    async def _analyze_roster(self, roster: List[Dict[str, Any]], week: int) -> RosterAnalysis:
        """Analyze current roster strengths and weaknesses."""
        try:
            # Calculate position strengths
            position_strengths = {}
            position_weaknesses = {}

            # Group players by position
            position_players = defaultdict(list)
            for player in roster:
                position = player.get("position", "")
                position_players[position].append(player)

            # Analyze each position
            for position in self.position_configs["positions"]:
                players = position_players[position]

                if not players:
                    position_strengths[position] = 0.0
                    position_weaknesses[position] = 1.0
                    continue

                # Calculate average projected points for position
                total_projection = 0.0
                player_count = 0

                for player in players:
                    try:
                        prediction = await self.performance_predictor.predict_performance(player)
                        total_projection += prediction.predicted_points
                        player_count += 1
                    except:
                        # Fallback to manual projection
                        total_projection += player.get("projected_points", 0)
                        player_count += 1

                avg_projection = total_projection / max(player_count, 1)

                # Score relative to position baseline (simplified)
                position_baseline = self._get_position_baseline(position)
                strength_score = min(1.0, avg_projection / max(position_baseline, 1))

                position_strengths[position] = strength_score
                position_weaknesses[position] = 1.0 - strength_score

            # Analyze bye weeks
            bye_week_gaps = self._analyze_bye_weeks(roster)

            # Assess injury risks
            injury_risks = {}
            for player in roster:
                player_id = player.get("player_id", "")
                injury_status = player.get("injury_status", "healthy").lower()

                risk_scores = {
                    "healthy": 0.0,
                    "questionable": 0.3,
                    "doubtful": 0.7,
                    "out": 1.0,
                    "ir": 1.0,
                }

                injury_risks[player_id] = risk_scores.get(injury_status, 0.1)

            # Calculate bench depth
            bench_depth = defaultdict(int)
            starter_positions = self._get_starting_positions()

            for position in self.position_configs["positions"]:
                total_players = len(position_players[position])
                starters_needed = starter_positions.get(position, 1)
                bench_depth[position] = max(0, total_players - starters_needed)

            # Identify streaming needs
            streaming_needs = []
            for position in self.position_configs["streaming_positions"]:
                if bench_depth[position] < 1:
                    streaming_needs.append(position)

            # Calculate team metrics
            all_projections = []
            for player in roster:
                try:
                    prediction = await self.performance_predictor.predict_performance(player)
                    all_projections.append(prediction.predicted_points)
                except:
                    all_projections.append(player.get("projected_points", 0))

            total_projected = sum(all_projections)
            ceiling_potential = sum(p * 1.3 for p in all_projections)  # 30% upside
            floor_stability = sum(p * 0.7 for p in all_projections)    # 30% downside
            consistency_score = 1.0 - (np.std(all_projections) / max(np.mean(all_projections), 1))

            return RosterAnalysis(
                team_id="",  # Will be set by caller
                total_projected_points=total_projected,
                position_strengths=position_strengths,
                position_weaknesses=position_weaknesses,
                bye_week_gaps=bye_week_gaps,
                injury_risks=injury_risks,
                bench_depth=dict(bench_depth),
                streaming_needs=streaming_needs,
                ceiling_potential=ceiling_potential,
                floor_stability=floor_stability,
                consistency_score=consistency_score,
            )

        except Exception as e:
            logger.error(f"Roster analysis failed: {e}")
            raise WaiverRecommenderError(f"Roster analysis failed: {e}")

    async def _identify_waiver_candidates(self,
                                        available_players: List[Dict[str, Any]],
                                        roster_analysis: RosterAnalysis,
                                        week: int) -> List[Dict[str, Any]]:
        """Identify potential waiver wire candidates."""
        try:
            candidates = []

            for player in available_players:
                # Filter by ownership
                ownership = player.get("ownership_percentage", 0)
                if ownership > self.ownership_threshold:
                    continue

                # Basic eligibility checks
                position = player.get("position", "")
                if position not in self.position_configs["positions"]:
                    continue

                # Skip players that are out long-term
                injury_status = player.get("injury_status", "healthy").lower()
                if injury_status in ["ir", "out"] and player.get("return_timeline", 99) > 4:
                    continue

                candidates.append(player)

            logger.info(f"Identified {len(candidates)} waiver candidates")
            return candidates

        except Exception as e:
            logger.error(f"Candidate identification failed: {e}")
            return []

    async def _generate_recommendations(self,
                                      candidates: List[Dict[str, Any]],
                                      roster_analysis: RosterAnalysis,
                                      league_settings: Dict[str, Any],
                                      week: int) -> List[WaiverTarget]:
        """Generate waiver recommendations with analysis."""
        try:
            recommendations = []

            for player in candidates:
                # Generate prediction
                try:
                    prediction = await self.performance_predictor.predict_performance(player)
                    projected_points = prediction.predicted_points
                    confidence = prediction.confidence_score
                except:
                    projected_points = player.get("projected_points", 0)
                    confidence = 0.5

                # Calculate rest of season projection
                ros_projection = self._calculate_ros_projection(player)

                # Assess recommendation type and priority
                rec_type, priority = self._assess_recommendation_type_and_priority(
                    player, roster_analysis, projected_points
                )

                # Skip if no clear recommendation
                if priority == WaiverPriority.WATCH and rec_type == RecommendationType.IMMEDIATE_NEED:
                    continue

                # Calculate scores
                value_score = self._calculate_value_score(player, projected_points)
                upside_score = self._calculate_upside_score(player, prediction if 'prediction' in locals() else None)
                safety_score = self._calculate_safety_score(player, confidence)
                roster_need_score = self._calculate_roster_need_score(
                    player, roster_analysis
                )

                # Calculate FAAB recommendations
                suggested_bid, max_bid = self._calculate_faab_recommendations(
                    priority, value_score, league_settings
                )

                # Generate reasoning
                reasoning = self._generate_reasoning(
                    player, rec_type, projected_points, roster_analysis
                )

                # Identify risk factors
                risk_factors = self._identify_risk_factors(player)

                # Find comparable players
                comparable_players = self._find_comparable_players(player, candidates)

                # Calculate breakout probability
                breakout_prob = self._calculate_breakout_probability(player)

                # Grade schedule
                schedule_grade = self._grade_upcoming_schedule(player, week)

                recommendation = WaiverTarget(
                    player_id=player.get("player_id", ""),
                    name=player.get("name", ""),
                    position=player.get("position", ""),
                    team=player.get("team", ""),
                    ownership_percentage=player.get("ownership_percentage", 0),
                    projected_points_next_week=projected_points,
                    projected_points_ros=ros_projection,
                    breakout_probability=breakout_prob,
                    recommendation_type=rec_type,
                    priority_level=priority,
                    roster_need_score=roster_need_score,
                    suggested_bid_percentage=suggested_bid,
                    max_bid_percentage=max_bid,
                    value_score=value_score,
                    upside_score=upside_score,
                    safety_score=safety_score,
                    schedule_grade=schedule_grade,
                    reasoning=reasoning,
                    risk_factors=risk_factors,
                    comparable_players=comparable_players,
                    generated_at=datetime.utcnow(),
                    confidence_score=confidence,
                )

                recommendations.append(recommendation)

            # Sort by priority and value
            recommendations.sort(
                key=lambda r: (
                    list(WaiverPriority).index(r.priority_level),
                    -r.value_score
                )
            )

            return recommendations

        except Exception as e:
            logger.error(f"Recommendation generation failed: {e}")
            return []

    def _get_current_week(self) -> int:
        """Get current NFL/fantasy week."""
        # Simplified - would integrate with actual week calculation
        now = datetime.now()

        # NFL season typically starts in early September
        season_start = datetime(now.year, 9, 1)
        if now < season_start:
            season_start = datetime(now.year - 1, 9, 1)

        weeks_elapsed = (now - season_start).days // 7
        return min(max(1, weeks_elapsed + 1), 18)

    def _get_position_baseline(self, position: str) -> float:
        """Get baseline projection for position."""
        # Sport and position specific baselines
        baselines = {
            Sport.NFL: {
                "QB": 18.0, "RB": 12.0, "WR": 10.0, "TE": 8.0,
                "K": 8.0, "DEF": 8.0
            },
            Sport.MLB: {
                "C": 8.0, "1B": 10.0, "2B": 9.0, "3B": 9.0,
                "SS": 9.0, "OF": 9.0, "P": 12.0
            },
            Sport.WNBA: {
                "PG": 25.0, "SG": 22.0, "SF": 20.0, "PF": 18.0, "C": 16.0
            }
        }

        sport_baselines = baselines.get(self.sport, baselines[Sport.NFL])
        return sport_baselines.get(position, 10.0)

    def _analyze_bye_weeks(self, roster: List[Dict[str, Any]]) -> Dict[int, List[str]]:
        """Analyze bye week gaps in roster."""
        bye_week_gaps = defaultdict(list)

        for player in roster:
            bye_week = player.get("bye_week")
            position = player.get("position", "")

            if bye_week and position:
                bye_week_gaps[bye_week].append(position)

        return dict(bye_week_gaps)

    def _get_starting_positions(self) -> Dict[str, int]:
        """Get starting lineup requirements by position."""
        # Simplified starting lineup requirements
        lineups = {
            Sport.NFL: {"QB": 1, "RB": 2, "WR": 3, "TE": 1, "K": 1, "DEF": 1},
            Sport.MLB: {"C": 1, "1B": 1, "2B": 1, "3B": 1, "SS": 1, "OF": 3, "P": 2},
            Sport.WNBA: {"PG": 1, "SG": 1, "SF": 1, "PF": 1, "C": 1},
        }

        return lineups.get(self.sport, lineups[Sport.NFL])

    def _calculate_ros_projection(self, player: Dict[str, Any]) -> float:
        """Calculate rest of season projection."""
        weekly_projection = player.get("projected_points", 0)
        weeks_remaining = max(1, 18 - self._get_current_week())  # Simplified

        # Account for growth/decline trends
        age = player.get("age", 27)
        experience = player.get("years_experience", 3)

        trend_factor = 1.0
        if age < 25 and experience < 3:  # Young player
            trend_factor = 1.1  # Potential for growth
        elif age > 30:  # Veteran
            trend_factor = 0.95  # Potential decline

        return weekly_projection * weeks_remaining * trend_factor

    def _assess_recommendation_type_and_priority(self,
                                               player: Dict[str, Any],
                                               roster_analysis: RosterAnalysis,
                                               projected_points: float) -> Tuple[RecommendationType, WaiverPriority]:
        """Assess recommendation type and priority level."""
        position = player.get("position", "")

        # Check for immediate needs
        position_weakness = roster_analysis.position_weaknesses.get(position, 0)
        if position_weakness > 0.7:
            if projected_points > self._get_position_baseline(position) * 1.2:
                return RecommendationType.IMMEDIATE_NEED, WaiverPriority.MUST_ADD
            elif projected_points > self._get_position_baseline(position):
                return RecommendationType.IMMEDIATE_NEED, WaiverPriority.HIGH

        # Check for breakout candidates
        breakout_prob = self._calculate_breakout_probability(player)
        if breakout_prob > 0.3:
            if breakout_prob > 0.6:
                return RecommendationType.BREAKOUT_CANDIDATE, WaiverPriority.HIGH
            else:
                return RecommendationType.BREAKOUT_CANDIDATE, WaiverPriority.MEDIUM

        # Check for injury replacements
        if player.get("opportunity_score", 0) > 0.7:  # High opportunity due to injury
            return RecommendationType.INJURY_REPLACEMENT, WaiverPriority.HIGH

        # Check for streaming candidates
        if position in self.position_configs["streaming_positions"]:
            schedule_grade = self._grade_upcoming_schedule(player, self._get_current_week())
            if schedule_grade in ["A", "B"]:
                return RecommendationType.SCHEDULE_STREAM, WaiverPriority.MEDIUM

        # Check for handcuffs
        if position in self.position_configs["handcuff_positions"]:
            return RecommendationType.HANDCUFF, WaiverPriority.LOW

        # Default to upside play
        if projected_points > self._get_position_baseline(position):
            return RecommendationType.UPSIDE_PLAY, WaiverPriority.MEDIUM
        else:
            return RecommendationType.UPSIDE_PLAY, WaiverPriority.WATCH

    def _calculate_value_score(self, player: Dict[str, Any], projected_points: float) -> float:
        """Calculate value score for player."""
        ownership = max(player.get("ownership_percentage", 0), 1)
        baseline = self._get_position_baseline(player.get("position", ""))

        # Value = projected points above baseline / ownership percentage
        value = max(0, projected_points - baseline) / ownership * 100

        return min(1.0, value / 10.0)  # Normalize to 0-1

    def _calculate_upside_score(self, player: Dict[str, Any], prediction: Optional[PredictionResult]) -> float:
        """Calculate upside score for player."""
        if prediction:
            ceiling = prediction.prediction_range[1]
            projected = prediction.predicted_points
        else:
            projected = player.get("projected_points", 0)
            ceiling = projected * 1.4  # Estimate ceiling

        if projected <= 0:
            return 0.0

        upside_ratio = ceiling / projected
        return min(1.0, (upside_ratio - 1.0) / 0.5)  # Normalize upside

    def _calculate_safety_score(self, player: Dict[str, Any], confidence: float) -> float:
        """Calculate safety/floor score for player."""
        # Base safety on confidence and injury status
        injury_risk = 0.0
        injury_status = player.get("injury_status", "healthy").lower()

        if injury_status in ["questionable", "doubtful"]:
            injury_risk = 0.3
        elif injury_status in ["out", "ir"]:
            injury_risk = 0.8

        safety = confidence * (1.0 - injury_risk)
        return max(0.0, min(1.0, safety))

    def _calculate_roster_need_score(self, player: Dict[str, Any], roster_analysis: RosterAnalysis) -> float:
        """Calculate how much the roster needs this player."""
        position = player.get("position", "")

        # Position weakness score
        weakness_score = roster_analysis.position_weaknesses.get(position, 0)

        # Bench depth consideration
        depth_score = 1.0 - (roster_analysis.bench_depth.get(position, 0) / 3.0)
        depth_score = max(0.0, min(1.0, depth_score))

        # Streaming need bonus
        streaming_bonus = 0.2 if position in roster_analysis.streaming_needs else 0.0

        need_score = (weakness_score * 0.6) + (depth_score * 0.3) + streaming_bonus
        return min(1.0, need_score)

    def _calculate_faab_recommendations(self,
                                      priority: WaiverPriority,
                                      value_score: float,
                                      league_settings: Dict[str, Any]) -> Tuple[float, float]:
        """Calculate FAAB bid recommendations."""
        base_percentage = self.faab_budget_allocation.get(priority, 0.02)

        # Adjust based on value score
        value_multiplier = 0.5 + (value_score * 1.5)  # 0.5 to 2.0 range

        suggested_bid = base_percentage * value_multiplier
        max_bid = suggested_bid * 1.5  # Maximum willing to bid

        # Ensure reasonable bounds
        suggested_bid = max(0.01, min(0.25, suggested_bid))
        max_bid = max(suggested_bid, min(0.35, max_bid))

        return round(suggested_bid, 3), round(max_bid, 3)

    def _calculate_breakout_probability(self, player: Dict[str, Any]) -> float:
        """Calculate probability of player having breakout performance."""
        factors = []

        # Opportunity factors
        snap_share = player.get("snap_share", 0.5)
        target_share = player.get("target_share", 0.1)
        red_zone_touches = player.get("red_zone_touches", 0)

        # Age and experience factors
        age = player.get("age", 27)
        experience = player.get("years_experience", 3)

        # Young player with opportunity
        if age <= 25 and experience <= 3:
            factors.append(0.2)

        # High opportunity metrics
        if snap_share > 0.7:
            factors.append(0.2)
        if target_share > 0.15:
            factors.append(0.2)
        if red_zone_touches > 2:
            factors.append(0.15)

        # Recent performance trends
        recent_games = player.get("recent_games", [])
        if len(recent_games) >= 3:
            recent_avg = np.mean([g.get("fantasy_points", 0) for g in recent_games[-3:]])
            season_avg = player.get("season_average", recent_avg)

            if recent_avg > season_avg * 1.3:
                factors.append(0.25)

        # Team context
        if player.get("team_pace", 0) > 65:  # High-pace offense
            factors.append(0.1)

        return min(1.0, sum(factors))

    def _grade_upcoming_schedule(self, player: Dict[str, Any], week: int) -> str:
        """Grade player's upcoming schedule strength."""
        # This would integrate with opponent strength data
        # Simplified implementation

        opponent_ranks = player.get("next_3_opponents_defensive_rank", [16, 16, 16])
        avg_rank = np.mean(opponent_ranks)

        if avg_rank <= 8:
            return "D"  # Tough matchups
        elif avg_rank <= 16:
            return "C"  # Average matchups
        elif avg_rank <= 24:
            return "B"  # Good matchups
        else:
            return "A"  # Great matchups

    def _generate_reasoning(self,
                          player: Dict[str, Any],
                          rec_type: RecommendationType,
                          projected_points: float,
                          roster_analysis: RosterAnalysis) -> List[str]:
        """Generate human-readable reasoning for recommendation."""
        reasoning = []

        position = player.get("position", "")
        name = player.get("name", "Unknown")

        # Type-specific reasoning
        if rec_type == RecommendationType.IMMEDIATE_NEED:
            weakness = roster_analysis.position_weaknesses.get(position, 0)
            reasoning.append(f"Addresses significant {position} weakness (weakness score: {weakness:.1f})")

        elif rec_type == RecommendationType.BREAKOUT_CANDIDATE:
            breakout_prob = self._calculate_breakout_probability(player)
            reasoning.append(f"High breakout potential ({breakout_prob:.1%} probability)")

        elif rec_type == RecommendationType.INJURY_REPLACEMENT:
            reasoning.append("Clear opportunity due to injury ahead of them")

        elif rec_type == RecommendationType.SCHEDULE_STREAM:
            schedule_grade = self._grade_upcoming_schedule(player, self._get_current_week())
            reasoning.append(f"Excellent upcoming schedule (Grade: {schedule_grade})")

        # Performance reasoning
        baseline = self._get_position_baseline(position)
        if projected_points > baseline * 1.3:
            reasoning.append(f"Projects well above {position} baseline ({projected_points:.1f} vs {baseline:.1f})")

        # Opportunity reasoning
        snap_share = player.get("snap_share", 0)
        if snap_share > 0.7:
            reasoning.append(f"High snap share ({snap_share:.1%})")

        target_share = player.get("target_share", 0)
        if target_share > 0.15:
            reasoning.append(f"Strong target share ({target_share:.1%})")

        # Recent form
        recent_games = player.get("recent_games", [])
        if len(recent_games) >= 2:
            recent_avg = np.mean([g.get("fantasy_points", 0) for g in recent_games[-2:]])
            if recent_avg > baseline:
                reasoning.append(f"Strong recent form ({recent_avg:.1f} points/game)")

        return reasoning

    def _identify_risk_factors(self, player: Dict[str, Any]) -> List[str]:
        """Identify risk factors for the player."""
        risk_factors = []

        # Injury risks
        injury_status = player.get("injury_status", "healthy").lower()
        if injury_status in ["questionable", "doubtful"]:
            risk_factors.append(f"Injury concern ({injury_status})")

        # Age risks
        age = player.get("age", 27)
        if age > 32:
            risk_factors.append("Age-related decline risk")

        # Opportunity risks
        snap_share = player.get("snap_share", 0.5)
        if snap_share < 0.5:
            risk_factors.append(f"Limited opportunity ({snap_share:.1%} snap share)")

        # Competition risks
        depth_chart_position = player.get("depth_chart_position", 1)
        if depth_chart_position > 2:
            risk_factors.append("Low on depth chart")

        # Team context risks
        team_pace = player.get("team_pace", 65)
        if team_pace < 60:
            risk_factors.append("Slow-paced offense limits upside")

        return risk_factors

    def _find_comparable_players(self, player: Dict[str, Any], candidates: List[Dict[str, Any]]) -> List[str]:
        """Find comparable players for context."""
        position = player.get("position", "")
        team = player.get("team", "")
        projected_points = player.get("projected_points", 0)

        comparables = []

        for candidate in candidates:
            if (candidate.get("position") == position and
                candidate.get("player_id") != player.get("player_id")):

                candidate_points = candidate.get("projected_points", 0)

                # Similar projection range
                if abs(candidate_points - projected_points) < 3.0:
                    comparables.append(candidate.get("name", "Unknown"))

        return comparables[:3]  # Return top 3 comparables

    def _calculate_faab_strategy(self, recommendations: List[WaiverTarget], league_settings: Dict[str, Any]) -> Dict[str, float]:
        """Calculate overall FAAB strategy."""
        total_recommended = sum(r.suggested_bid_percentage for r in recommendations)

        strategy = {
            "total_recommended": total_recommended,
            "aggressive_threshold": 0.25,
            "conservative_threshold": 0.10,
        }

        return strategy

    async def _analyze_league_competition(self, league_id: str, available_players: List[Dict[str, Any]]) -> float:
        """Analyze level of competition in league."""
        # This would analyze other teams' waiver activity, FAAB spending patterns, etc.
        # Simplified implementation
        return 0.7  # Moderate competition

    def _assess_waiver_wire_strength(self, available_players: List[Dict[str, Any]]) -> float:
        """Assess overall strength of waiver wire."""
        if not available_players:
            return 0.0

        # Count players with meaningful projections
        meaningful_players = 0
        for player in available_players:
            projected = player.get("projected_points", 0)
            position = player.get("position", "")
            baseline = self._get_position_baseline(position)

            if projected > baseline * 0.8:  # Within 80% of baseline
                meaningful_players += 1

        strength = meaningful_players / len(available_players)
        return min(1.0, strength)

    def _identify_focus_positions(self, roster_analysis: RosterAnalysis) -> List[str]:
        """Identify positions that should be the focus of waiver activity."""
        focus_positions = []

        # Positions with high weakness scores
        for position, weakness in roster_analysis.position_weaknesses.items():
            if weakness > 0.6:
                focus_positions.append(position)

        # Streaming needs
        focus_positions.extend(roster_analysis.streaming_needs)

        # Remove duplicates while preserving order
        return list(dict.fromkeys(focus_positions))

    def _determine_strategy_type(self, roster_analysis: RosterAnalysis, recommendations: List[WaiverTarget]) -> str:
        """Determine overall strategy type."""
        must_adds = len([r for r in recommendations if r.priority_level == WaiverPriority.MUST_ADD])
        high_priority = len([r for r in recommendations if r.priority_level == WaiverPriority.HIGH])

        total_faab = sum(r.suggested_bid_percentage for r in recommendations)

        if must_adds > 0 or total_faab > 0.2:
            return "aggressive"
        elif high_priority > 2 or total_faab > 0.1:
            return "balanced"
        else:
            return "conservative"


# Global recommender instances
_recommenders: Dict[Sport, WaiverRecommendationEngine] = {}


def get_waiver_recommender(sport: Sport) -> WaiverRecommendationEngine:
    """Get or create waiver recommender for a sport."""
    global _recommenders

    if sport not in _recommenders:
        _recommenders[sport] = WaiverRecommendationEngine(sport)

    return _recommenders[sport]


def reset_recommenders():
    """Reset all recommenders (useful for testing)."""
    global _recommenders
    _recommenders = {}