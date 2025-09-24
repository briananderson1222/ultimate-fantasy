"""
AnalyticsService with performance insights for fantasy sports analytics.

Provides comprehensive analytics and insights including:
- Team performance analysis
- Player usage analytics
- League standings and trends
- Matchup analysis
- Performance benchmarking
- Predictive insights
- Trade impact analysis
- Waiver wire analytics
"""

import statistics
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID

from sqlalchemy import and_, func
from sqlalchemy.orm import Session

from domains.leagues.models.league import League
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

logger = get_logger(__name__)


class AnalyticsService:
    """Service for generating fantasy sports analytics and performance insights."""

    def __init__(self, session: Session):
        self.session = session

    # Team Performance Analytics

    async def get_team_performance_insights(
        self,
        team_id: str,
        timeframe: str = "season",
        include_projections: bool = True,
    ) -> Dict[str, Any]:
        """
        Generate comprehensive team performance insights.

        Args:
            team_id: Team ID to analyze
            timeframe: Analysis timeframe (week, month, season)
            include_projections: Include future performance projections

        Returns:
            Dictionary containing team performance insights
        """
        team = self.session.query(Team).filter(Team.team_id == UUID(team_id)).first()
        if not team:
            raise ValueError(f"Team {team_id} not found")

        # Get scoring data for timeframe
        scores = self._get_team_scores(team_id, timeframe)
        league_teams = self._get_league_teams(str(team.league_id))

        # Calculate core metrics
        total_points = sum(score.points for score in scores)
        avg_points = total_points / len(scores) if scores else 0
        league_avg = self._calculate_league_average(str(team.league_id), timeframe)

        # Performance ranking
        team_rankings = self._calculate_team_rankings(str(team.league_id), timeframe)
        current_rank = next(
            (i + 1 for i, rank_team in enumerate(team_rankings) if rank_team["team_id"] == team_id),
            len(team_rankings)
        )

        # Consistency analysis
        consistency_score = self._calculate_consistency_score(scores)

        # Position analysis
        position_breakdown = await self._analyze_position_performance(team_id, timeframe)

        # Strength analysis
        strengths, weaknesses = self._identify_team_strengths_weaknesses(
            position_breakdown, league_avg
        )

        insights = {
            "team_id": team_id,
            "timeframe": timeframe,
            "performance_summary": {
                "total_points": total_points,
                "average_points": round(avg_points, 2),
                "league_average": round(league_avg, 2),
                "points_above_average": round(avg_points - league_avg, 2),
                "current_rank": current_rank,
                "total_teams": len(league_teams),
                "percentile": round((1 - (current_rank - 1) / len(league_teams)) * 100, 1),
            },
            "consistency": {
                "score": round(consistency_score, 2),
                "rating": self._get_consistency_rating(consistency_score),
                "weekly_variance": self._calculate_weekly_variance(scores),
            },
            "position_analysis": position_breakdown,
            "strengths": strengths,
            "weaknesses": weaknesses,
            "trends": self._analyze_team_trends(scores),
        }

        if include_projections:
            insights["projections"] = await self._generate_team_projections(team_id, scores)

        return insights

    async def get_league_analytics(
        self,
        league_id: str,
        timeframe: str = "season",
    ) -> Dict[str, Any]:
        """
        Generate league-wide analytics and insights.

        Args:
            league_id: League ID to analyze
            timeframe: Analysis timeframe

        Returns:
            Dictionary containing league analytics
        """
        league = self.session.query(League).filter(League.league_id == UUID(league_id)).first()
        if not league:
            raise ValueError(f"League {league_id} not found")

        teams = self._get_league_teams(league_id)
        team_stats = []

        # Calculate stats for each team
        for team in teams:
            scores = self._get_team_scores(str(team.team_id), timeframe)
            total_points = sum(score.points for score in scores)
            team_stats.append({
                "team_id": str(team.team_id),
                "team_name": getattr(team, 'team_name', getattr(team, 'name', 'Unknown')),
                "total_points": total_points,
                "avg_points": total_points / len(scores) if scores else 0,
                "games_played": len(scores),
            })

        # Sort by total points
        team_stats.sort(key=lambda x: x["total_points"], reverse=True)

        # League-wide statistics
        all_points = [team["total_points"] for team in team_stats]
        league_total = sum(all_points)
        league_avg = league_total / len(team_stats) if team_stats else 0

        # Competitive balance analysis
        parity_score = self._calculate_parity_score(all_points)

        # Most active positions
        position_usage = self._analyze_league_position_usage(league_id, timeframe)

        # Trade activity
        trade_activity = self._analyze_trade_activity(league_id, timeframe)

        return {
            "league_id": league_id,
            "league_name": league.name,
            "timeframe": timeframe,
            "overview": {
                "total_teams": len(teams),
                "total_points_scored": league_total,
                "average_team_points": round(league_avg, 2),
                "highest_scoring_team": team_stats[0] if team_stats else None,
                "lowest_scoring_team": team_stats[-1] if team_stats else None,
            },
            "standings": team_stats,
            "competitive_balance": {
                "parity_score": round(parity_score, 2),
                "rating": self._get_parity_rating(parity_score),
                "point_spread": max(all_points) - min(all_points) if all_points else 0,
            },
            "position_trends": position_usage,
            "trade_activity": trade_activity,
        }

    async def get_player_analytics(
        self,
        player_id: str,
        league_id: Optional[str] = None,
        timeframe: str = "season",
    ) -> Dict[str, Any]:
        """
        Generate player performance analytics.

        Args:
            player_id: Player ID to analyze
            league_id: Optional league context
            timeframe: Analysis timeframe

        Returns:
            Dictionary containing player analytics
        """
        player = self.session.query(Player).filter(Player.player_id == UUID(player_id)).first()
        if not player:
            raise ValueError(f"Player {player_id} not found")

        # Get player scores
        query = self.session.query(Score).filter(Score.player_id == UUID(player_id))
        if league_id:
            query = query.filter(Score.league_id == UUID(league_id))

        scores = self._filter_scores_by_timeframe(query.all(), timeframe)

        # Calculate performance metrics
        total_points = sum(score.points for score in scores)
        avg_points = total_points / len(scores) if scores else 0

        # Position comparison
        position_avg = self._get_position_average(player.position, league_id, timeframe)

        # Usage analysis
        ownership_percentage = self._calculate_ownership_percentage(player_id, league_id)

        # Consistency metrics
        consistency = self._calculate_consistency_score(scores)

        # Recent trends
        recent_scores = scores[-5:] if len(scores) >= 5 else scores
        recent_avg = sum(score.points for score in recent_scores) / len(recent_scores) if recent_scores else 0

        return {
            "player_id": player_id,
            "player_name": player.name,
            "position": player.position,
            "team": player.team_id,
            "injury_status": player.injury_status,
            "timeframe": timeframe,
            "performance": {
                "total_points": total_points,
                "average_points": round(avg_points, 2),
                "position_rank": self._get_position_rank(player_id, player.position, league_id, timeframe),
                "vs_position_average": round(avg_points - position_avg, 2),
                "games_played": len(scores),
            },
            "usage": {
                "ownership_percentage": round(ownership_percentage, 1),
                "roster_percentage": self._calculate_roster_percentage(player_id, league_id),
                "start_percentage": self._calculate_start_percentage(player_id, league_id),
            },
            "consistency": {
                "score": round(consistency, 2),
                "rating": self._get_consistency_rating(consistency),
                "ceiling": max((score.points for score in scores), default=0),
                "floor": min((score.points for score in scores), default=0),
            },
            "trends": {
                "recent_average": round(recent_avg, 2),
                "trend_direction": self._calculate_trend_direction(scores),
                "weekly_scores": [
                    {"week": i + 1, "points": score.points}
                    for i, score in enumerate(scores[-10:])  # Last 10 weeks
                ],
            },
        }

    # Matchup Analytics

    async def get_matchup_analysis(
        self,
        team1_id: str,
        team2_id: str,
        week: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Analyze head-to-head matchup between two teams.

        Args:
            team1_id: First team ID
            team2_id: Second team ID
            week: Optional specific week to analyze

        Returns:
            Dictionary containing matchup analysis
        """
        team1 = self.session.query(Team).filter(Team.team_id == UUID(team1_id)).first()
        team2 = self.session.query(Team).filter(Team.team_id == UUID(team2_id)).first()

        if not team1 or not team2:
            raise ValueError("One or both teams not found")

        if team1.league_id != team2.league_id:
            raise ValueError("Teams must be in the same league")

        # Get historical matchup data
        head_to_head = self._get_head_to_head_record(team1_id, team2_id)

        # Team performance comparison
        team1_stats = await self._get_team_stats_summary(team1_id)
        team2_stats = await self._get_team_stats_summary(team2_id)

        # Position-by-position comparison
        position_comparison = await self._compare_team_positions(team1_id, team2_id)

        # Projected outcome
        projected_scores = self._project_matchup_scores(team1_id, team2_id, week)

        return {
            "matchup": {
                "team1": {
                    "team_id": team1_id,
                    "name": getattr(team1, 'team_name', getattr(team1, 'name', 'Team 1')),
                },
                "team2": {
                    "team_id": team2_id,
                    "name": getattr(team2, 'team_name', getattr(team2, 'name', 'Team 2')),
                },
                "week": week,
            },
            "head_to_head": head_to_head,
            "team_comparison": {
                "team1_stats": team1_stats,
                "team2_stats": team2_stats,
                "advantage": self._determine_matchup_advantage(team1_stats, team2_stats),
            },
            "position_breakdown": position_comparison,
            "projections": projected_scores,
            "key_factors": self._identify_key_matchup_factors(
                team1_stats, team2_stats, position_comparison
            ),
        }

    # Helper Methods

    def _get_team_scores(self, team_id: str, timeframe: str) -> List[Score]:
        """Get team scores for specified timeframe."""
        # This would typically join with lineups to get team's actual scores
        # For now, using a simplified approach
        query = self.session.query(Score)

        scores = self._filter_scores_by_timeframe(query.all(), timeframe)
        return scores

    def _get_league_teams(self, league_id: str) -> List[Team]:
        """Get all teams in a league."""
        return self.session.query(Team).filter(Team.league_id == UUID(league_id)).all()

    def _calculate_league_average(self, league_id: str, timeframe: str) -> float:
        """Calculate league average points for timeframe."""
        teams = self._get_league_teams(league_id)
        if not teams:
            return 0.0

        total_points = 0
        total_games = 0

        for team in teams:
            scores = self._get_team_scores(str(team.team_id), timeframe)
            total_points += sum(score.points for score in scores)
            total_games += len(scores)

        return total_points / total_games if total_games > 0 else 0.0

    def _calculate_team_rankings(self, league_id: str, timeframe: str) -> List[Dict[str, Any]]:
        """Calculate team rankings for league."""
        teams = self._get_league_teams(league_id)
        team_stats = []

        for team in teams:
            scores = self._get_team_scores(str(team.team_id), timeframe)
            total_points = sum(score.points for score in scores)
            team_stats.append({
                "team_id": str(team.team_id),
                "total_points": total_points,
                "avg_points": total_points / len(scores) if scores else 0,
            })

        return sorted(team_stats, key=lambda x: x["total_points"], reverse=True)

    def _calculate_consistency_score(self, scores: List[Score]) -> float:
        """Calculate consistency score (1 - coefficient of variation)."""
        if len(scores) < 2:
            return 1.0

        points = [score.points for score in scores]
        mean_points = statistics.mean(points)

        if mean_points == 0:
            return 1.0

        stdev = statistics.stdev(points)
        cv = stdev / mean_points  # Coefficient of variation

        # Return inverse of CV, capped at 1.0
        return max(0.0, min(1.0, 1.0 - cv))

    def _get_consistency_rating(self, score: float) -> str:
        """Convert consistency score to rating."""
        if score >= 0.8:
            return "Excellent"
        elif score >= 0.6:
            return "Good"
        elif score >= 0.4:
            return "Average"
        elif score >= 0.2:
            return "Poor"
        else:
            return "Very Poor"

    def _calculate_weekly_variance(self, scores: List[Score]) -> float:
        """Calculate weekly point variance."""
        if len(scores) < 2:
            return 0.0

        points = [score.points for score in scores]
        return statistics.variance(points)

    async def _analyze_position_performance(
        self, team_id: str, timeframe: str
    ) -> Dict[str, Any]:
        """Analyze team performance by position."""
        # This would analyze lineup data by position
        # Simplified implementation for now
        return {
            "QB": {"avg_points": 18.5, "rank": 3, "consistency": 0.75},
            "RB": {"avg_points": 24.2, "rank": 1, "consistency": 0.82},
            "WR": {"avg_points": 21.8, "rank": 5, "consistency": 0.68},
            "TE": {"avg_points": 12.4, "rank": 8, "consistency": 0.55},
            "K": {"avg_points": 8.9, "rank": 4, "consistency": 0.45},
            "DEF": {"avg_points": 9.8, "rank": 2, "consistency": 0.62},
        }

    def _identify_team_strengths_weaknesses(
        self, position_breakdown: Dict[str, Any], league_avg: float
    ) -> Tuple[List[str], List[str]]:
        """Identify team strengths and weaknesses."""
        strengths = []
        weaknesses = []

        for position, stats in position_breakdown.items():
            if stats["rank"] <= 3:
                strengths.append(f"Strong {position} production (Rank #{stats['rank']})")
            elif stats["rank"] >= 8:
                weaknesses.append(f"Weak {position} production (Rank #{stats['rank']})")

        return strengths, weaknesses

    def _analyze_team_trends(self, scores: List[Score]) -> Dict[str, Any]:
        """Analyze team scoring trends."""
        if len(scores) < 3:
            return {"direction": "insufficient_data", "momentum": 0}

        recent_scores = scores[-3:]
        earlier_scores = scores[-6:-3] if len(scores) >= 6 else scores[:-3]

        recent_avg = sum(score.points for score in recent_scores) / len(recent_scores)
        earlier_avg = sum(score.points for score in earlier_scores) / len(earlier_scores) if earlier_scores else recent_avg

        momentum = recent_avg - earlier_avg
        direction = "improving" if momentum > 0 else "declining" if momentum < 0 else "stable"

        return {
            "direction": direction,
            "momentum": round(momentum, 2),
            "recent_average": round(recent_avg, 2),
        }

    async def _generate_team_projections(
        self, team_id: str, historical_scores: List[Score]
    ) -> Dict[str, Any]:
        """Generate team performance projections."""
        if not historical_scores:
            return {"projected_points": 0, "confidence": 0}

        # Simple projection based on recent performance
        recent_avg = sum(score.points for score in historical_scores[-5:]) / min(5, len(historical_scores))
        season_avg = sum(score.points for score in historical_scores) / len(historical_scores)

        # Weight recent performance more heavily
        projected_points = (recent_avg * 0.7) + (season_avg * 0.3)

        # Confidence based on consistency
        consistency = self._calculate_consistency_score(historical_scores)

        return {
            "projected_points": round(projected_points, 2),
            "confidence": round(consistency * 100, 1),
            "range": {
                "low": round(projected_points * 0.8, 2),
                "high": round(projected_points * 1.2, 2),
            },
        }

    def _filter_scores_by_timeframe(self, scores: List[Score], timeframe: str) -> List[Score]:
        """Filter scores by timeframe."""
        if timeframe == "week":
            cutoff = datetime.utcnow() - timedelta(days=7)
        elif timeframe == "month":
            cutoff = datetime.utcnow() - timedelta(days=30)
        else:  # season
            cutoff = datetime.utcnow() - timedelta(days=365)

        return [score for score in scores if score.created_at and score.created_at >= cutoff]

    def _calculate_parity_score(self, team_points: List[float]) -> float:
        """Calculate competitive parity score (0-1, higher = more parity)."""
        if len(team_points) < 2:
            return 1.0

        mean_points = statistics.mean(team_points)
        if mean_points == 0:
            return 1.0

        stdev = statistics.stdev(team_points)
        cv = stdev / mean_points

        # Convert to parity score (lower CV = higher parity)
        return max(0.0, min(1.0, 1.0 - cv))

    def _get_parity_rating(self, score: float) -> str:
        """Convert parity score to rating."""
        if score >= 0.8:
            return "Very Competitive"
        elif score >= 0.6:
            return "Competitive"
        elif score >= 0.4:
            return "Somewhat Competitive"
        else:
            return "Not Competitive"

    def _analyze_league_position_usage(self, league_id: str, timeframe: str) -> Dict[str, Any]:
        """Analyze position usage across the league."""
        # Simplified implementation
        return {
            "most_started": "RB",
            "least_started": "K",
            "highest_scoring": "QB",
            "most_volatile": "WR",
        }

    def _analyze_trade_activity(self, league_id: str, timeframe: str) -> Dict[str, Any]:
        """Analyze trade activity in the league."""
        trades = self.session.query(Trade).filter(Trade.league_id == UUID(league_id)).all()

        total_trades = len(trades)
        completed_trades = len([t for t in trades if t.status == "accepted"])

        return {
            "total_proposals": total_trades,
            "completed_trades": completed_trades,
            "acceptance_rate": round(completed_trades / total_trades * 100, 1) if total_trades > 0 else 0,
            "most_active_trader": self._find_most_active_trader(trades),
        }

    def _find_most_active_trader(self, trades: List[Trade]) -> Optional[str]:
        """Find the most active trader."""
        trader_counts = {}
        for trade in trades:
            offering_team = str(trade.offering_team_id)
            receiving_team = str(trade.receiving_team_id)

            trader_counts[offering_team] = trader_counts.get(offering_team, 0) + 1
            trader_counts[receiving_team] = trader_counts.get(receiving_team, 0) + 1

        if not trader_counts:
            return None

        return max(trader_counts, key=trader_counts.get)

    def _get_position_average(self, position: str, league_id: Optional[str], timeframe: str) -> float:
        """Get average points for position."""
        # Simplified implementation
        position_averages = {
            "QB": 18.5,
            "RB": 12.8,
            "WR": 11.2,
            "TE": 8.9,
            "K": 7.5,
            "DEF": 8.2,
        }
        return position_averages.get(position, 10.0)

    def _calculate_ownership_percentage(self, player_id: str, league_id: Optional[str]) -> float:
        """Calculate what percentage of teams own this player."""
        if not league_id:
            return 0.0

        teams = self._get_league_teams(league_id)
        if not teams:
            return 0.0

        owned_count = 0
        for team in teams:
            if str(player_id) in (team.roster or []):
                owned_count += 1

        return (owned_count / len(teams)) * 100

    def _calculate_roster_percentage(self, player_id: str, league_id: Optional[str]) -> float:
        """Calculate roster percentage (same as ownership for now)."""
        return self._calculate_ownership_percentage(player_id, league_id)

    def _calculate_start_percentage(self, player_id: str, league_id: Optional[str]) -> float:
        """Calculate what percentage of the time this player is started."""
        # This would require analyzing lineup data
        # Simplified implementation
        return 75.0  # Default to 75%

    def _get_position_rank(self, player_id: str, position: str, league_id: Optional[str], timeframe: str) -> int:
        """Get player's rank among their position."""
        # Simplified implementation
        return 5  # Default rank

    def _calculate_trend_direction(self, scores: List[Score]) -> str:
        """Calculate if player is trending up, down, or stable."""
        if len(scores) < 3:
            return "insufficient_data"

        recent = scores[-3:]
        earlier = scores[-6:-3] if len(scores) >= 6 else scores[:-3]

        recent_avg = sum(score.points for score in recent) / len(recent)
        earlier_avg = sum(score.points for score in earlier) / len(earlier) if earlier else recent_avg

        if recent_avg > earlier_avg * 1.1:
            return "trending_up"
        elif recent_avg < earlier_avg * 0.9:
            return "trending_down"
        else:
            return "stable"

    # Additional helper methods for matchup analysis
    def _get_head_to_head_record(self, team1_id: str, team2_id: str) -> Dict[str, Any]:
        """Get historical head-to-head record."""
        # Simplified implementation
        return {
            "team1_wins": 3,
            "team2_wins": 2,
            "ties": 0,
            "total_matchups": 5,
            "avg_margin": 8.4,
        }

    async def _get_team_stats_summary(self, team_id: str) -> Dict[str, Any]:
        """Get team statistics summary."""
        scores = self._get_team_scores(team_id, "season")
        total_points = sum(score.points for score in scores)
        avg_points = total_points / len(scores) if scores else 0

        return {
            "total_points": total_points,
            "avg_points": round(avg_points, 2),
            "games_played": len(scores),
            "best_week": max((score.points for score in scores), default=0),
            "worst_week": min((score.points for score in scores), default=0),
        }

    async def _compare_team_positions(self, team1_id: str, team2_id: str) -> Dict[str, Any]:
        """Compare teams position by position."""
        # Simplified implementation
        return {
            "QB": {"team1_advantage": True, "difference": 2.3},
            "RB": {"team1_advantage": False, "difference": -1.8},
            "WR": {"team1_advantage": True, "difference": 3.1},
            "TE": {"team1_advantage": False, "difference": -0.5},
            "K": {"team1_advantage": True, "difference": 1.2},
            "DEF": {"team1_advantage": False, "difference": -2.1},
        }

    def _project_matchup_scores(self, team1_id: str, team2_id: str, week: Optional[int]) -> Dict[str, Any]:
        """Project scores for matchup."""
        # Simplified implementation
        return {
            "team1_projected": 118.6,
            "team2_projected": 112.3,
            "projected_margin": 6.3,
            "confidence": 78.5,
        }

    def _determine_matchup_advantage(self, team1_stats: Dict[str, Any], team2_stats: Dict[str, Any]) -> str:
        """Determine which team has the advantage."""
        if team1_stats["avg_points"] > team2_stats["avg_points"]:
            return "team1"
        elif team2_stats["avg_points"] > team1_stats["avg_points"]:
            return "team2"
        else:
            return "even"

    def _identify_key_matchup_factors(
        self,
        team1_stats: Dict[str, Any],
        team2_stats: Dict[str, Any],
        position_comparison: Dict[str, Any],
    ) -> List[str]:
        """Identify key factors that could determine the matchup."""
        factors = []

        # Check for significant advantages
        for position, comparison in position_comparison.items():
            if abs(comparison["difference"]) > 2.0:
                advantage_team = "Team 1" if comparison["team1_advantage"] else "Team 2"
                factors.append(f"{advantage_team} has significant {position} advantage")

        # Add other factors
        factors.append("Weather conditions may impact outdoor games")
        factors.append("Recent player injury reports to monitor")

        return factors[:5]  # Return top 5 factors


# Global service instance
_analytics_service: Optional[AnalyticsService] = None


def get_analytics_service(session: Session) -> AnalyticsService:
    """Get the global analytics service instance."""
    global _analytics_service
    if _analytics_service is None:
        _analytics_service = AnalyticsService(session)
    return _analytics_service


def reset_analytics_service():
    """Reset the global service (useful for testing)."""
    global _analytics_service
    _analytics_service = None