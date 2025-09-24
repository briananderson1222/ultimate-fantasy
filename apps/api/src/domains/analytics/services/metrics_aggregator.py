"""
Performance metrics aggregator service.

Centralized service for collecting, processing, and aggregating performance metrics
across all fantasy sports domains. Provides unified analytics and reporting
capabilities with real-time and historical data aggregation.
"""

import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, field
from enum import Enum
import statistics
from collections import defaultdict

from sqlalchemy.orm import Session
from sqlalchemy import func, desc, asc, and_, or_

try:
    from infrastructure.logging.domain_logger import get_logger
except ImportError:
    import logging
    get_logger = logging.getLogger

from domains.users.models.user_team import UserTeam
from domains.leagues.models.league import League
from domains.lineups.models.lineup import Lineup
from domains.scoring.models.scoring import GameScore
from domains.players.models.player import Player
from domains.trading.models.trade import Trade
from domains.waivers.models.waiver import WaiverClaim

logger = get_logger(__name__)


class MetricType(str, Enum):
    """Types of metrics that can be aggregated."""
    SCORING = "scoring"
    EFFICIENCY = "efficiency"
    CONSISTENCY = "consistency"
    TRADING = "trading"
    WAIVER = "waiver"
    LINEUP = "lineup"
    COMPETITIVE = "competitive"


class AggregationPeriod(str, Enum):
    """Time periods for metric aggregation."""
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    SEASONAL = "seasonal"
    HISTORICAL = "historical"


class MetricScope(str, Enum):
    """Scope of metric calculation."""
    USER = "user"
    TEAM = "team"
    LEAGUE = "league"
    GLOBAL = "global"


@dataclass
class MetricValue:
    """Individual metric value with metadata."""
    metric_name: str
    value: Union[float, int, str]
    timestamp: datetime
    confidence: float = 1.0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AggregatedMetric:
    """Aggregated metric with statistical summary."""
    metric_name: str
    scope: MetricScope
    period: AggregationPeriod

    # Statistical values
    current_value: float
    previous_value: Optional[float] = None
    average_value: float = 0.0
    median_value: float = 0.0
    min_value: float = 0.0
    max_value: float = 0.0
    std_deviation: float = 0.0

    # Trend analysis
    trend_direction: str = "stable"  # "up", "down", "stable"
    trend_strength: float = 0.0
    change_percentage: float = 0.0

    # Benchmarking
    percentile_rank: float = 50.0
    league_average: Optional[float] = None
    league_median: Optional[float] = None

    # Metadata
    sample_size: int = 0
    data_quality: float = 1.0
    last_updated: datetime = field(default_factory=datetime.utcnow)
    tags: List[str] = field(default_factory=list)


@dataclass
class PerformanceMetrics:
    """Comprehensive performance metrics collection."""
    user_team_id: str
    league_id: str
    period: AggregationPeriod
    generated_at: datetime

    # Core performance metrics
    scoring_metrics: Dict[str, AggregatedMetric] = field(default_factory=dict)
    efficiency_metrics: Dict[str, AggregatedMetric] = field(default_factory=dict)
    consistency_metrics: Dict[str, AggregatedMetric] = field(default_factory=dict)
    trading_metrics: Dict[str, AggregatedMetric] = field(default_factory=dict)
    waiver_metrics: Dict[str, AggregatedMetric] = field(default_factory=dict)
    lineup_metrics: Dict[str, AggregatedMetric] = field(default_factory=dict)
    competitive_metrics: Dict[str, AggregatedMetric] = field(default_factory=dict)

    # Summary indicators
    overall_performance_score: float = 0.0
    performance_grade: str = "B"
    strengths: List[str] = field(default_factory=list)
    weaknesses: List[str] = field(default_factory=list)


class PerformanceMetricsAggregator:
    """Service for aggregating and analyzing performance metrics."""

    def __init__(self, db: Session):
        self.db = db
        self.logger = get_logger(self.__class__.__name__)

    async def aggregate_team_metrics(
        self,
        user_team_id: str,
        period: AggregationPeriod = AggregationPeriod.WEEKLY,
        include_benchmarks: bool = True
    ) -> PerformanceMetrics:
        """
        Aggregate comprehensive performance metrics for a team.

        Args:
            user_team_id: ID of the user team to analyze
            period: Time period for aggregation
            include_benchmarks: Whether to include league benchmarking

        Returns:
            PerformanceMetrics object with all aggregated data
        """
        try:
            user_team = self.db.query(UserTeam).filter(
                UserTeam.user_team_id == user_team_id
            ).first()

            if not user_team:
                raise ValueError(f"User team {user_team_id} not found")

            self.logger.info(f"Aggregating metrics for team {user_team_id}, period: {period.value}")

            # Initialize metrics collection
            metrics = PerformanceMetrics(
                user_team_id=user_team_id,
                league_id=user_team.league_id,
                period=period,
                generated_at=datetime.utcnow()
            )

            # Aggregate different metric categories in parallel
            tasks = [
                self._aggregate_scoring_metrics(user_team, period),
                self._aggregate_efficiency_metrics(user_team, period),
                self._aggregate_consistency_metrics(user_team, period),
                self._aggregate_trading_metrics(user_team, period),
                self._aggregate_waiver_metrics(user_team, period),
                self._aggregate_lineup_metrics(user_team, period),
                self._aggregate_competitive_metrics(user_team, period),
            ]

            results = await asyncio.gather(*tasks, return_exceptions=True)

            # Process results
            metrics.scoring_metrics = results[0] if not isinstance(results[0], Exception) else {}
            metrics.efficiency_metrics = results[1] if not isinstance(results[1], Exception) else {}
            metrics.consistency_metrics = results[2] if not isinstance(results[2], Exception) else {}
            metrics.trading_metrics = results[3] if not isinstance(results[3], Exception) else {}
            metrics.waiver_metrics = results[4] if not isinstance(results[4], Exception) else {}
            metrics.lineup_metrics = results[5] if not isinstance(results[5], Exception) else {}
            metrics.competitive_metrics = results[6] if not isinstance(results[6], Exception) else {}

            # Add league benchmarking if requested
            if include_benchmarks:
                await self._add_league_benchmarks(metrics, user_team.league_id)

            # Calculate overall performance score
            metrics.overall_performance_score = self._calculate_overall_score(metrics)
            metrics.performance_grade = self._calculate_performance_grade(metrics.overall_performance_score)

            # Identify strengths and weaknesses
            metrics.strengths, metrics.weaknesses = self._identify_strengths_weaknesses(metrics)

            self.logger.info(
                f"Metrics aggregation completed for team {user_team_id}",
                extra={
                    "user_team_id": user_team_id,
                    "overall_score": metrics.overall_performance_score,
                    "grade": metrics.performance_grade,
                    "metrics_count": sum([
                        len(metrics.scoring_metrics),
                        len(metrics.efficiency_metrics),
                        len(metrics.consistency_metrics),
                        len(metrics.trading_metrics),
                        len(metrics.waiver_metrics),
                        len(metrics.lineup_metrics),
                        len(metrics.competitive_metrics)
                    ])
                }
            )

            return metrics

        except Exception as e:
            self.logger.error(f"Failed to aggregate team metrics: {e}")
            raise

    async def _aggregate_scoring_metrics(
        self,
        user_team: UserTeam,
        period: AggregationPeriod
    ) -> Dict[str, AggregatedMetric]:
        """Aggregate scoring performance metrics."""
        try:
            metrics = {}

            # Get scoring data for the period
            scoring_query = self.db.query(GameScore).filter(
                GameScore.user_team_id == user_team.user_team_id
            )

            # Apply period filter
            period_filter = self._get_period_filter(period)
            if period_filter:
                scoring_query = scoring_query.filter(GameScore.created_at >= period_filter)

            scores = scoring_query.order_by(GameScore.created_at.desc()).all()

            if not scores:
                return metrics

            # Calculate basic scoring metrics
            total_points = [float(score.total_points) for score in scores]

            # Average points per game
            metrics["avg_points_per_game"] = AggregatedMetric(
                metric_name="avg_points_per_game",
                scope=MetricScope.TEAM,
                period=period,
                current_value=statistics.mean(total_points),
                average_value=statistics.mean(total_points),
                median_value=statistics.median(total_points),
                min_value=min(total_points),
                max_value=max(total_points),
                std_deviation=statistics.stdev(total_points) if len(total_points) > 1 else 0.0,
                sample_size=len(total_points),
                tags=["scoring", "performance"]
            )

            # High-score games (above 90th percentile)
            high_score_threshold = statistics.quantiles(total_points, n=10)[8] if len(total_points) >= 10 else max(total_points)
            high_score_count = sum(1 for score in total_points if score >= high_score_threshold)

            metrics["high_score_frequency"] = AggregatedMetric(
                metric_name="high_score_frequency",
                scope=MetricScope.TEAM,
                period=period,
                current_value=high_score_count / len(total_points),
                sample_size=len(total_points),
                tags=["scoring", "ceiling"]
            )

            # Calculate trends if we have enough data
            if len(total_points) >= 5:
                recent_avg = statistics.mean(total_points[:3])
                earlier_avg = statistics.mean(total_points[3:6]) if len(total_points) >= 6 else statistics.mean(total_points[3:])

                for metric in metrics.values():
                    if earlier_avg > 0:
                        metric.change_percentage = ((recent_avg - earlier_avg) / earlier_avg) * 100
                        metric.trend_direction = "up" if metric.change_percentage > 5 else "down" if metric.change_percentage < -5 else "stable"
                        metric.trend_strength = abs(metric.change_percentage) / 100

            return metrics

        except Exception as e:
            self.logger.error(f"Failed to aggregate scoring metrics: {e}")
            return {}

    async def _aggregate_efficiency_metrics(
        self,
        user_team: UserTeam,
        period: AggregationPeriod
    ) -> Dict[str, AggregatedMetric]:
        """Aggregate efficiency metrics."""
        try:
            metrics = {}

            # Roster utilization efficiency
            lineup_query = self.db.query(Lineup).filter(
                Lineup.user_team_id == user_team.user_team_id
            )

            period_filter = self._get_period_filter(period)
            if period_filter:
                lineup_query = lineup_query.filter(Lineup.created_at >= period_filter)

            lineups = lineup_query.all()

            if lineups:
                # Calculate roster utilization metrics
                total_possible_players = len(lineups) * 9  # Assuming 9 starting positions
                total_set_players = sum(
                    len([p for p in [lineup.qb_id, lineup.rb1_id, lineup.rb2_id,
                                   lineup.wr1_id, lineup.wr2_id, lineup.te_id,
                                   lineup.flex_id, lineup.dst_id, lineup.k_id] if p])
                    for lineup in lineups
                )

                roster_utilization = total_set_players / total_possible_players if total_possible_players > 0 else 0

                metrics["roster_utilization"] = AggregatedMetric(
                    metric_name="roster_utilization",
                    scope=MetricScope.TEAM,
                    period=period,
                    current_value=roster_utilization,
                    sample_size=len(lineups),
                    tags=["efficiency", "roster"]
                )

            return metrics

        except Exception as e:
            self.logger.error(f"Failed to aggregate efficiency metrics: {e}")
            return {}

    async def _aggregate_consistency_metrics(
        self,
        user_team: UserTeam,
        period: AggregationPeriod
    ) -> Dict[str, AggregatedMetric]:
        """Aggregate consistency metrics."""
        try:
            metrics = {}

            # Get scoring data for consistency analysis
            scoring_query = self.db.query(GameScore).filter(
                GameScore.user_team_id == user_team.user_team_id
            )

            period_filter = self._get_period_filter(period)
            if period_filter:
                scoring_query = scoring_query.filter(GameScore.created_at >= period_filter)

            scores = scoring_query.order_by(GameScore.created_at.desc()).all()

            if len(scores) >= 3:
                total_points = [float(score.total_points) for score in scores]

                # Coefficient of variation (lower is more consistent)
                mean_score = statistics.mean(total_points)
                std_score = statistics.stdev(total_points)
                coefficient_of_variation = (std_score / mean_score) if mean_score > 0 else 0

                # Consistency score (inverse of coefficient of variation, scaled)
                consistency_score = max(0, 1 - (coefficient_of_variation / 0.5))  # Normalize to 0-1

                metrics["scoring_consistency"] = AggregatedMetric(
                    metric_name="scoring_consistency",
                    scope=MetricScope.TEAM,
                    period=period,
                    current_value=consistency_score,
                    average_value=consistency_score,
                    std_deviation=coefficient_of_variation,
                    sample_size=len(total_points),
                    tags=["consistency", "scoring"]
                )

                # Floor performance (25th percentile)
                floor_score = statistics.quantiles(total_points, n=4)[0] if len(total_points) >= 4 else min(total_points)

                metrics["scoring_floor"] = AggregatedMetric(
                    metric_name="scoring_floor",
                    scope=MetricScope.TEAM,
                    period=period,
                    current_value=floor_score,
                    min_value=min(total_points),
                    sample_size=len(total_points),
                    tags=["consistency", "floor"]
                )

            return metrics

        except Exception as e:
            self.logger.error(f"Failed to aggregate consistency metrics: {e}")
            return {}

    async def _aggregate_trading_metrics(
        self,
        user_team: UserTeam,
        period: AggregationPeriod
    ) -> Dict[str, AggregatedMetric]:
        """Aggregate trading activity metrics."""
        try:
            metrics = {}

            # Get trading data
            trades_query = self.db.query(Trade).filter(
                or_(
                    Trade.proposing_team_id == user_team.user_team_id,
                    Trade.target_team_id == user_team.user_team_id
                )
            )

            period_filter = self._get_period_filter(period)
            if period_filter:
                trades_query = trades_query.filter(Trade.created_at >= period_filter)

            trades = trades_query.all()

            # Trade activity metrics
            total_trades = len(trades)
            completed_trades = len([t for t in trades if t.status == "accepted"])

            metrics["trade_activity"] = AggregatedMetric(
                metric_name="trade_activity",
                scope=MetricScope.TEAM,
                period=period,
                current_value=total_trades,
                sample_size=total_trades,
                tags=["trading", "activity"]
            )

            if total_trades > 0:
                trade_success_rate = completed_trades / total_trades

                metrics["trade_success_rate"] = AggregatedMetric(
                    metric_name="trade_success_rate",
                    scope=MetricScope.TEAM,
                    period=period,
                    current_value=trade_success_rate,
                    sample_size=total_trades,
                    tags=["trading", "success"]
                )

            return metrics

        except Exception as e:
            self.logger.error(f"Failed to aggregate trading metrics: {e}")
            return {}

    async def _aggregate_waiver_metrics(
        self,
        user_team: UserTeam,
        period: AggregationPeriod
    ) -> Dict[str, AggregatedMetric]:
        """Aggregate waiver wire activity metrics."""
        try:
            metrics = {}

            # Get waiver claims data
            waivers_query = self.db.query(WaiverClaim).filter(
                WaiverClaim.user_team_id == user_team.user_team_id
            )

            period_filter = self._get_period_filter(period)
            if period_filter:
                waivers_query = waivers_query.filter(WaiverClaim.created_at >= period_filter)

            waivers = waivers_query.all()

            # Waiver activity metrics
            total_claims = len(waivers)
            successful_claims = len([w for w in waivers if w.status == "awarded"])

            metrics["waiver_activity"] = AggregatedMetric(
                metric_name="waiver_activity",
                scope=MetricScope.TEAM,
                period=period,
                current_value=total_claims,
                sample_size=total_claims,
                tags=["waiver", "activity"]
            )

            if total_claims > 0:
                waiver_success_rate = successful_claims / total_claims

                metrics["waiver_success_rate"] = AggregatedMetric(
                    metric_name="waiver_success_rate",
                    scope=MetricScope.TEAM,
                    period=period,
                    current_value=waiver_success_rate,
                    sample_size=total_claims,
                    tags=["waiver", "success"]
                )

            return metrics

        except Exception as e:
            self.logger.error(f"Failed to aggregate waiver metrics: {e}")
            return {}

    async def _aggregate_lineup_metrics(
        self,
        user_team: UserTeam,
        period: AggregationPeriod
    ) -> Dict[str, AggregatedMetric]:
        """Aggregate lineup management metrics."""
        try:
            metrics = {}

            # Get lineup data
            lineup_query = self.db.query(Lineup).filter(
                Lineup.user_team_id == user_team.user_team_id
            )

            period_filter = self._get_period_filter(period)
            if period_filter:
                lineup_query = lineup_query.filter(Lineup.created_at >= period_filter)

            lineups = lineup_query.all()

            if lineups:
                # Lineup optimization rate (how often lineups were changed)
                unique_weeks = len(set(lineup.week for lineup in lineups if lineup.week))
                lineup_changes = len(lineups)

                optimization_rate = lineup_changes / unique_weeks if unique_weeks > 0 else 0

                metrics["lineup_optimization_rate"] = AggregatedMetric(
                    metric_name="lineup_optimization_rate",
                    scope=MetricScope.TEAM,
                    period=period,
                    current_value=optimization_rate,
                    sample_size=len(lineups),
                    tags=["lineup", "optimization"]
                )

            return metrics

        except Exception as e:
            self.logger.error(f"Failed to aggregate lineup metrics: {e}")
            return {}

    async def _aggregate_competitive_metrics(
        self,
        user_team: UserTeam,
        period: AggregationPeriod
    ) -> Dict[str, AggregatedMetric]:
        """Aggregate competitive positioning metrics."""
        try:
            metrics = {}

            # League standings analysis would go here
            # For now, placeholder metrics

            metrics["league_rank"] = AggregatedMetric(
                metric_name="league_rank",
                scope=MetricScope.LEAGUE,
                period=period,
                current_value=6,  # Would calculate from actual standings
                sample_size=1,
                tags=["competitive", "rank"]
            )

            return metrics

        except Exception as e:
            self.logger.error(f"Failed to aggregate competitive metrics: {e}")
            return {}

    async def _add_league_benchmarks(self, metrics: PerformanceMetrics, league_id: str):
        """Add league benchmarking data to metrics."""
        try:
            # Get all teams in the league for benchmarking
            league_teams = self.db.query(UserTeam).filter(
                UserTeam.league_id == league_id
            ).all()

            # Calculate league averages for key metrics
            # This would involve aggregating metrics for all teams and calculating percentiles
            # For now, add placeholder benchmarking

            for category_metrics in [
                metrics.scoring_metrics,
                metrics.efficiency_metrics,
                metrics.consistency_metrics
            ]:
                for metric in category_metrics.values():
                    # Placeholder league average (would calculate from actual data)
                    metric.league_average = metric.current_value * 0.95
                    metric.percentile_rank = 60.0  # Would calculate actual percentile

        except Exception as e:
            self.logger.error(f"Failed to add league benchmarks: {e}")

    def _calculate_overall_score(self, metrics: PerformanceMetrics) -> float:
        """Calculate overall performance score from all metrics."""
        try:
            scores = []
            weights = {}

            # Weight different categories
            category_weights = {
                "scoring": 0.3,
                "efficiency": 0.2,
                "consistency": 0.2,
                "trading": 0.1,
                "waiver": 0.1,
                "lineup": 0.1
            }

            # Collect weighted scores from each category
            for category, weight in category_weights.items():
                category_metrics = getattr(metrics, f"{category}_metrics", {})
                if category_metrics:
                    category_scores = []
                    for metric in category_metrics.values():
                        # Normalize metrics to 0-100 scale
                        if metric.percentile_rank > 0:
                            category_scores.append(metric.percentile_rank)
                        else:
                            # Use relative performance if percentile not available
                            if metric.league_average and metric.league_average > 0:
                                relative_score = (metric.current_value / metric.league_average) * 50
                                category_scores.append(min(100, max(0, relative_score)))

                    if category_scores:
                        avg_category_score = statistics.mean(category_scores)
                        scores.append(avg_category_score * weight)

            return sum(scores) if scores else 50.0

        except Exception as e:
            self.logger.error(f"Failed to calculate overall score: {e}")
            return 50.0

    def _calculate_performance_grade(self, score: float) -> str:
        """Convert numerical score to letter grade."""
        if score >= 90:
            return "A+"
        elif score >= 85:
            return "A"
        elif score >= 80:
            return "A-"
        elif score >= 75:
            return "B+"
        elif score >= 70:
            return "B"
        elif score >= 65:
            return "B-"
        elif score >= 60:
            return "C+"
        elif score >= 55:
            return "C"
        elif score >= 50:
            return "C-"
        elif score >= 45:
            return "D+"
        elif score >= 40:
            return "D"
        else:
            return "F"

    def _identify_strengths_weaknesses(
        self,
        metrics: PerformanceMetrics
    ) -> tuple[List[str], List[str]]:
        """Identify key strengths and weaknesses from metrics."""
        strengths = []
        weaknesses = []

        try:
            # Analyze all metrics to find standouts
            all_metrics = []
            for category_metrics in [
                metrics.scoring_metrics,
                metrics.efficiency_metrics,
                metrics.consistency_metrics,
                metrics.trading_metrics,
                metrics.waiver_metrics,
                metrics.lineup_metrics,
                metrics.competitive_metrics
            ]:
                all_metrics.extend(category_metrics.values())

            # Identify top performers (strengths)
            for metric in all_metrics:
                if metric.percentile_rank >= 80:
                    strengths.append(metric.metric_name.replace("_", " ").title())
                elif metric.percentile_rank <= 20:
                    weaknesses.append(metric.metric_name.replace("_", " ").title())

            # Limit to top 3 of each
            return strengths[:3], weaknesses[:3]

        except Exception as e:
            self.logger.error(f"Failed to identify strengths/weaknesses: {e}")
            return [], []

    def _get_period_filter(self, period: AggregationPeriod) -> Optional[datetime]:
        """Get datetime filter for the specified period."""
        now = datetime.utcnow()

        if period == AggregationPeriod.DAILY:
            return now - timedelta(days=1)
        elif period == AggregationPeriod.WEEKLY:
            return now - timedelta(weeks=1)
        elif period == AggregationPeriod.MONTHLY:
            return now - timedelta(days=30)
        elif period == AggregationPeriod.SEASONAL:
            return now - timedelta(days=120)  # ~4 months
        else:  # HISTORICAL
            return None

    async def get_league_metrics_summary(
        self,
        league_id: str,
        period: AggregationPeriod = AggregationPeriod.WEEKLY
    ) -> Dict[str, Any]:
        """Get aggregated metrics summary for an entire league."""
        try:
            league_teams = self.db.query(UserTeam).filter(
                UserTeam.league_id == league_id
            ).all()

            summary = {
                "league_id": league_id,
                "period": period.value,
                "team_count": len(league_teams),
                "generated_at": datetime.utcnow().isoformat(),
                "metrics": {}
            }

            # Aggregate metrics for all teams
            team_metrics = []
            for team in league_teams:
                try:
                    metrics = await self.aggregate_team_metrics(
                        str(team.user_team_id),
                        period,
                        include_benchmarks=False
                    )
                    team_metrics.append(metrics)
                except Exception as e:
                    self.logger.warning(f"Failed to aggregate metrics for team {team.user_team_id}: {e}")
                    continue

            # Calculate league-wide statistics
            if team_metrics:
                summary["metrics"]["average_score"] = statistics.mean([m.overall_performance_score for m in team_metrics])
                summary["metrics"]["score_distribution"] = {
                    "min": min([m.overall_performance_score for m in team_metrics]),
                    "max": max([m.overall_performance_score for m in team_metrics]),
                    "std": statistics.stdev([m.overall_performance_score for m in team_metrics]) if len(team_metrics) > 1 else 0
                }
                summary["metrics"]["grade_distribution"] = {}
                for metrics in team_metrics:
                    grade = metrics.performance_grade
                    summary["metrics"]["grade_distribution"][grade] = summary["metrics"]["grade_distribution"].get(grade, 0) + 1

            return summary

        except Exception as e:
            self.logger.error(f"Failed to get league metrics summary: {e}")
            raise

    async def export_metrics_data(
        self,
        user_team_id: str,
        format: str = "json"
    ) -> Dict[str, Any]:
        """Export metrics data in specified format."""
        try:
            metrics = await self.aggregate_team_metrics(user_team_id)

            if format.lower() == "json":
                return {
                    "user_team_id": metrics.user_team_id,
                    "league_id": metrics.league_id,
                    "period": metrics.period.value,
                    "generated_at": metrics.generated_at.isoformat(),
                    "overall_score": metrics.overall_performance_score,
                    "grade": metrics.performance_grade,
                    "categories": {
                        "scoring": {name: {
                            "value": metric.current_value,
                            "percentile": metric.percentile_rank,
                            "trend": metric.trend_direction
                        } for name, metric in metrics.scoring_metrics.items()},
                        "efficiency": {name: {
                            "value": metric.current_value,
                            "percentile": metric.percentile_rank,
                            "trend": metric.trend_direction
                        } for name, metric in metrics.efficiency_metrics.items()},
                        "consistency": {name: {
                            "value": metric.current_value,
                            "percentile": metric.percentile_rank,
                            "trend": metric.trend_direction
                        } for name, metric in metrics.consistency_metrics.items()}
                    }
                }
            else:
                raise ValueError(f"Unsupported export format: {format}")

        except Exception as e:
            self.logger.error(f"Failed to export metrics data: {e}")
            raise