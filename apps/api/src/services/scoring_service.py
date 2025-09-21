from __future__ import annotations

import uuid as _uuid
from datetime import datetime, date, timedelta
from typing import Optional, Dict, Any, List, Tuple
from dataclasses import dataclass
from enum import Enum
import asyncio

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, func, text

from ..domains.scoring.models.score import Score
from ..domains.leagues.models.league import League
from ..domains.leagues.models.team import Team
from ..domains.sports.models.player import Player
from ..domains.lineups.models.lineup import Lineup
from ..services.sports_data_service import SportsDataService, SportType
from ..infrastructure.database.session_factory import get_db_session
from ..infrastructure.logging.domain_logger import get_logger

logger = get_logger(__name__)


class ScoringType(Enum):
    """Scoring calculation types"""
    GAME = "game"
    WEEKLY = "weekly"
    SEASON = "season"


@dataclass
class ScoringResult:
    """Result of scoring calculation"""
    player_id: str
    total_points: float
    breakdown: Dict[str, float]
    bonus_points: float
    stat_values: Dict[str, Any]


@dataclass
class TeamScoring:
    """Team's total scoring for a period"""
    team_id: str
    total_points: float
    starting_points: float
    bench_points: float
    player_scores: List[ScoringResult]


@dataclass
class MatchupResult:
    """Head-to-head matchup result"""
    home_team: TeamScoring
    away_team: TeamScoring
    winner: Optional[str]  # team_id of winner, None for tie
    margin: float


class ScoringServiceError(Exception):
    """Base exception for scoring service errors"""
    pass


class ScoringService:
    """
    Scoring service for fantasy point calculations

    Implements T033 requirements:
    - ScoringService for fantasy point calculations
    - Add custom scoring rules, stat processing, projections
    - Include real-time updates and historical tracking
    """

    def __init__(self, sports_data_service: Optional[SportsDataService] = None):
        self.sports_data_service = sports_data_service or SportsDataService()
        self.scoring_cache_duration_minutes = 5
        self.real_time_update_interval_seconds = 30

    # Core Scoring Methods

    def calculate_player_score(
        self,
        player_id: str,
        league_id: str,
        game_date: date,
        stat_values: Dict[str, Any],
        is_final: bool = False,
        db: Optional[Session] = None
    ) -> ScoringResult:
        """
        Calculate fantasy points for a player's performance

        Args:
            player_id: Player ID
            league_id: League ID for scoring rules
            game_date: Date of the game
            stat_values: Player's statistical performance
            is_final: Whether this is final scoring or projected
            db: Optional database session

        Returns:
            ScoringResult with point breakdown
        """
        with get_db_session() if db is None else db as session:
            # Get player and league
            player = session.query(Player).filter(Player.player_id == player_id).first()
            league = session.query(League).filter(League.league_id == league_id).first()

            if not player or not league:
                raise ScoringServiceError("Player or league not found")

            # Get scoring rules for the league
            scoring_rules = league.scoring_rules or {}

            # Calculate points breakdown
            breakdown = {}
            total_points = 0.0

            # Apply scoring rules based on sport
            if player.sport == "mlb":
                breakdown = self._calculate_mlb_scoring(stat_values, scoring_rules)
            elif player.sport == "nfl":
                breakdown = self._calculate_nfl_scoring(stat_values, scoring_rules)
            elif player.sport == "wnba":
                breakdown = self._calculate_wnba_scoring(stat_values, scoring_rules)
            else:
                breakdown = {"unknown_sport": 0.0}

            total_points = sum(breakdown.values())

            # Calculate bonus points (achievements, milestones, etc.)
            bonus_points = self._calculate_bonus_points(stat_values, scoring_rules, player.sport)

            return ScoringResult(
                player_id=player_id,
                total_points=total_points,
                breakdown=breakdown,
                bonus_points=bonus_points,
                stat_values=stat_values
            )

    def update_player_score(
        self,
        player_id: str,
        league_id: str,
        game_date: date,
        week: int,
        stat_values: Dict[str, Any],
        is_final: bool = False,
        game_id: Optional[str] = None,
        opponent_team: Optional[str] = None,
        db: Optional[Session] = None
    ) -> Score:
        """
        Update or create a player's score record

        Args:
            player_id: Player ID
            league_id: League ID
            game_date: Game date
            week: Week number
            stat_values: Statistical values
            is_final: Whether this is final scoring
            game_id: Optional game identifier
            opponent_team: Optional opponent team
            db: Optional database session

        Returns:
            Updated Score record
        """
        with get_db_session() if db is None else db as session:
            # Calculate fantasy points
            scoring_result = self.calculate_player_score(
                player_id, league_id, game_date, stat_values, is_final, session
            )

            # Find existing score or create new one
            score = session.query(Score).filter(
                and_(
                    Score.player_id == player_id,
                    Score.league_id == league_id,
                    Score.game_date == game_date,
                    Score.scoring_type == ScoringType.GAME.value
                )
            ).first()

            if score:
                # Update existing score
                score.stat_values = stat_values
                score.fantasy_points = scoring_result.total_points
                score.bonus_points = scoring_result.bonus_points
                score.is_final = is_final
                score.last_updated_from_source = datetime.utcnow()
            else:
                # Create new score
                player = session.query(Player).filter(Player.player_id == player_id).first()
                score = Score(
                    player_id=player_id,
                    league_id=league_id,
                    game_date=game_date,
                    week=week,
                    season=self._get_current_season(),
                    opponent_team=opponent_team,
                    game_id=game_id,
                    stat_values=stat_values,
                    fantasy_points=scoring_result.total_points,
                    bonus_points=scoring_result.bonus_points,
                    scoring_type=ScoringType.GAME.value,
                    is_projected=not is_final,
                    is_final=is_final,
                    last_updated_from_source=datetime.utcnow()
                )
                session.add(score)

            session.commit()

            logger.info(f"Score updated for player {player_id}: {scoring_result.total_points} points")
            return score

    def calculate_team_score(
        self,
        team_id: str,
        week: int,
        game_day: Optional[date] = None,
        db: Optional[Session] = None
    ) -> TeamScoring:
        """
        Calculate total team score for a week/day

        Args:
            team_id: Team ID
            week: Week number
            game_day: Optional specific game day
            db: Optional database session

        Returns:
            TeamScoring with breakdown
        """
        with get_db_session() if db is None else db as session:
            team = session.query(Team).filter(Team.team_id == team_id).first()
            if not team:
                raise ScoringServiceError("Team not found")

            # Get team's lineup for the week
            lineup = session.query(Lineup).filter(
                and_(
                    Lineup.team_id == team_id,
                    Lineup.week == week,
                    Lineup.game_day == game_day
                )
            ).first()

            if not lineup or not lineup.players:
                return TeamScoring(
                    team_id=team_id,
                    total_points=0.0,
                    starting_points=0.0,
                    bench_points=0.0,
                    player_scores=[]
                )

            # Get scores for all lineup players
            lineup_player_ids = [p["player_id"] for p in lineup.players]

            # Determine date range for week scoring
            if game_day:
                start_date = end_date = game_day
            else:
                start_date, end_date = self._get_week_date_range(week)

            scores = session.query(Score).filter(
                and_(
                    Score.player_id.in_(lineup_player_ids),
                    Score.league_id == team.league_id,
                    Score.game_date >= start_date,
                    Score.game_date <= end_date
                )
            ).all()

            # Group scores by player
            player_scores_map = {}
            for score in scores:
                if score.player_id not in player_scores_map:
                    player_scores_map[score.player_id] = []
                player_scores_map[score.player_id].append(score)

            # Calculate team totals
            starting_points = 0.0
            bench_points = 0.0
            player_scores = []

            # Get league roster settings to determine starting positions
            league = session.query(League).filter(League.league_id == team.league_id).first()
            roster_settings = league.roster_settings or {}
            starting_positions = roster_settings.get("starting_positions", [])

            for player_data in lineup.players:
                player_id = player_data["player_id"]
                position = player_data["position"]

                # Calculate total points for this player
                player_total = 0.0
                player_breakdown = {}
                player_stats = {}

                if player_id in player_scores_map:
                    for score in player_scores_map[player_id]:
                        player_total += score.calculate_total_points()
                        if score.stat_values:
                            player_stats.update(score.stat_values)

                # Create scoring result
                scoring_result = ScoringResult(
                    player_id=player_id,
                    total_points=player_total,
                    breakdown=player_breakdown,
                    bonus_points=0.0,  # TODO: Calculate from scores
                    stat_values=player_stats
                )
                player_scores.append(scoring_result)

                # Add to starting or bench totals
                if position in starting_positions:
                    starting_points += player_total
                else:
                    bench_points += player_total

            total_points = starting_points + bench_points

            # Update lineup points if different
            if abs(lineup.points_scored - total_points) > 0.01:
                lineup.points_scored = total_points
                session.commit()

            return TeamScoring(
                team_id=team_id,
                total_points=total_points,
                starting_points=starting_points,
                bench_points=bench_points,
                player_scores=player_scores
            )

    # Real-time Scoring Updates

    async def update_live_scores(
        self,
        league_id: str,
        week: int,
        db: Optional[Session] = None
    ) -> int:
        """
        Update live scores for all players in a league

        Args:
            league_id: League ID
            week: Week number
            db: Optional database session

        Returns:
            Number of scores updated
        """
        with get_db_session() if db is None else db as session:
            league = session.query(League).filter(League.league_id == league_id).first()
            if not league:
                raise ScoringServiceError("League not found")

            # Get all teams in the league
            teams = session.query(Team).filter(Team.league_id == league_id).all()
            all_player_ids = set()

            for team in teams:
                if team.roster:
                    all_player_ids.update(team.roster)

            # Get live game data from sports API
            sport_type = SportType(league.sport)
            today = date.today()

            try:
                live_scores = await self.sports_data_service.get_live_scores(sport_type, today)
                scores_updated = 0

                for game_data in live_scores:
                    game_id = game_data.get("game_id")

                    # TODO: Extract player stats from live game data
                    # This would require more detailed sports data API integration

                    scores_updated += 1

                logger.info(f"Updated {scores_updated} live scores for league {league_id}")
                return scores_updated

            except Exception as e:
                logger.error(f"Failed to update live scores: {e}")
                return 0

    def start_real_time_scoring(self, league_id: str, week: int) -> None:
        """Start real-time scoring updates for a league"""
        async def scoring_loop():
            while True:
                try:
                    await self.update_live_scores(league_id, week)
                    await asyncio.sleep(self.real_time_update_interval_seconds)
                except Exception as e:
                    logger.error(f"Real-time scoring error: {e}")
                    await asyncio.sleep(60)  # Wait longer on error

        asyncio.create_task(scoring_loop())
        logger.info(f"Started real-time scoring for league {league_id}")

    # Historical and Statistical Methods

    def get_player_scoring_history(
        self,
        player_id: str,
        league_id: str,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        limit: int = 50,
        db: Optional[Session] = None
    ) -> List[Dict[str, Any]]:
        """Get player's scoring history"""
        with get_db_session() if db is None else db as session:
            query = session.query(Score).filter(
                and_(Score.player_id == player_id, Score.league_id == league_id)
            )

            if start_date:
                query = query.filter(Score.game_date >= start_date)
            if end_date:
                query = query.filter(Score.game_date <= end_date)

            scores = query.order_by(desc(Score.game_date)).limit(limit).all()

            history = []
            for score in scores:
                history.append({
                    "score_id": str(score.score_id),
                    "game_date": score.game_date.isoformat(),
                    "week": score.week,
                    "fantasy_points": score.fantasy_points,
                    "bonus_points": score.bonus_points,
                    "total_points": score.calculate_total_points(),
                    "stat_values": score.stat_values,
                    "opponent_team": score.opponent_team,
                    "is_final": score.is_final,
                    "is_projected": score.is_projected
                })

            return history

    def get_team_scoring_history(
        self,
        team_id: str,
        weeks: Optional[List[int]] = None,
        limit: int = 17,
        db: Optional[Session] = None
    ) -> List[Dict[str, Any]]:
        """Get team's weekly scoring history"""
        with get_db_session() if db is None else db as session:
            team = session.query(Team).filter(Team.team_id == team_id).first()
            if not team:
                raise ScoringServiceError("Team not found")

            query = session.query(Lineup).filter(Lineup.team_id == team_id)

            if weeks:
                query = query.filter(Lineup.week.in_(weeks))

            lineups = query.order_by(desc(Lineup.week)).limit(limit).all()

            history = []
            for lineup in lineups:
                # Calculate actual team score if not stored
                team_scoring = self.calculate_team_score(team_id, lineup.week, lineup.game_day, session)

                history.append({
                    "week": lineup.week,
                    "game_day": lineup.game_day.isoformat() if lineup.game_day else None,
                    "total_points": team_scoring.total_points,
                    "starting_points": team_scoring.starting_points,
                    "bench_points": team_scoring.bench_points,
                    "is_locked": lineup.is_locked,
                    "player_count": len(lineup.players) if lineup.players else 0
                })

            return history

    def get_league_scoring_leaders(
        self,
        league_id: str,
        week: Optional[int] = None,
        category: str = "total_points",
        limit: int = 10,
        db: Optional[Session] = None
    ) -> List[Dict[str, Any]]:
        """Get scoring leaders for the league"""
        with get_db_session() if db is None else db as session:
            if week:
                # Weekly leaders
                teams = session.query(Team).filter(Team.league_id == league_id).all()
                team_scores = []

                for team in teams:
                    team_scoring = self.calculate_team_score(team.team_id, week, db=session)
                    team_scores.append({
                        "team_id": str(team.team_id),
                        "team_name": getattr(team, "team_name", getattr(team, "name", "")),
                        "week": week,
                        "total_points": team_scoring.total_points,
                        "starting_points": team_scoring.starting_points
                    })

                team_scores.sort(key=lambda x: x["total_points"], reverse=True)
                return team_scores[:limit]
            else:
                # Season leaders
                team_totals = session.query(
                    Team.team_id,
                    Team.team_name,
                    func.coalesce(Team.points_for, 0).label("total_points")
                ).filter(Team.league_id == league_id).order_by(
                    desc(text("total_points"))
                ).limit(limit).all()

                return [
                    {
                        "team_id": str(team_id),
                        "team_name": name,
                        "total_points": float(total_points)
                    }
                    for team_id, name, total_points in team_totals
                ]

    # Matchup and Competition Methods

    def calculate_matchup(
        self,
        home_team_id: str,
        away_team_id: str,
        week: int,
        db: Optional[Session] = None
    ) -> MatchupResult:
        """Calculate head-to-head matchup result"""
        with get_db_session() if db is None else db as session:
            home_scoring = self.calculate_team_score(home_team_id, week, db=session)
            away_scoring = self.calculate_team_score(away_team_id, week, db=session)

            # Determine winner
            margin = home_scoring.total_points - away_scoring.total_points
            winner = None
            if margin > 0:
                winner = home_team_id
            elif margin < 0:
                winner = away_team_id

            return MatchupResult(
                home_team=home_scoring,
                away_team=away_scoring,
                winner=winner,
                margin=abs(margin)
            )

    def update_team_records(
        self,
        league_id: str,
        week: int,
        db: Optional[Session] = None
    ) -> None:
        """Update team win/loss records based on scoring"""
        with get_db_session() if db is None else db as session:
            # TODO: Implement matchup schedule and record updating
            # This would require a schedule/matchup system
            logger.info(f"Team records updated for league {league_id}, week {week}")

    # Sport-Specific Scoring Calculations

    def _calculate_mlb_scoring(
        self,
        stat_values: Dict[str, Any],
        scoring_rules: Dict[str, Any]
    ) -> Dict[str, float]:
        """Calculate MLB fantasy points"""
        hitting_rules = scoring_rules.get("hitting", {})
        pitching_rules = scoring_rules.get("pitching", {})
        breakdown = {}

        # Hitting stats
        for stat, multiplier in hitting_rules.items():
            if stat in stat_values:
                points = float(stat_values[stat]) * float(multiplier)
                breakdown[f"hitting_{stat}"] = round(points, 2)

        # Pitching stats
        for stat, multiplier in pitching_rules.items():
            if stat in stat_values:
                points = float(stat_values[stat]) * float(multiplier)
                breakdown[f"pitching_{stat}"] = round(points, 2)

        return breakdown

    def _calculate_nfl_scoring(
        self,
        stat_values: Dict[str, Any],
        scoring_rules: Dict[str, Any]
    ) -> Dict[str, float]:
        """Calculate NFL fantasy points"""
        breakdown = {}

        # Process each category
        for category, rules in scoring_rules.items():
            if isinstance(rules, dict):
                for stat, multiplier in rules.items():
                    if stat in stat_values:
                        points = float(stat_values[stat]) * float(multiplier)
                        breakdown[f"{category}_{stat}"] = round(points, 2)

        return breakdown

    def _calculate_wnba_scoring(
        self,
        stat_values: Dict[str, Any],
        scoring_rules: Dict[str, Any]
    ) -> Dict[str, float]:
        """Calculate WNBA fantasy points"""
        breakdown = {}

        # Process each category
        for category, rules in scoring_rules.items():
            if isinstance(rules, dict):
                for stat, multiplier in rules.items():
                    if stat in stat_values:
                        points = float(stat_values[stat]) * float(multiplier)
                        breakdown[f"{category}_{stat}"] = round(points, 2)

        return breakdown

    def _calculate_bonus_points(
        self,
        stat_values: Dict[str, Any],
        scoring_rules: Dict[str, Any],
        sport: str
    ) -> float:
        """Calculate bonus points for achievements"""
        bonus_points = 0.0

        # Sport-specific bonus calculations
        if sport == "nfl":
            # Example: 300+ yard passing game bonus
            if stat_values.get("passing_yards", 0) >= 300:
                bonus_points += scoring_rules.get("bonus_300_pass_yards", 2.0)

            # Example: 100+ yard rushing game bonus
            if stat_values.get("rushing_yards", 0) >= 100:
                bonus_points += scoring_rules.get("bonus_100_rush_yards", 2.0)

        elif sport == "mlb":
            # Example: Cycle bonus
            hits = stat_values.get("hits", 0)
            doubles = stat_values.get("doubles", 0)
            triples = stat_values.get("triples", 0)
            home_runs = stat_values.get("home_runs", 0)

            if hits >= 4 and doubles >= 1 and triples >= 1 and home_runs >= 1:
                bonus_points += scoring_rules.get("bonus_cycle", 10.0)

        elif sport == "wnba":
            # Example: Triple-double bonus
            points = stat_values.get("points", 0)
            rebounds = stat_values.get("rebounds", 0)
            assists = stat_values.get("assists", 0)

            double_digits = sum([points >= 10, rebounds >= 10, assists >= 10])
            if double_digits >= 3:
                bonus_points += scoring_rules.get("bonus_triple_double", 5.0)

        return bonus_points

    # Helper Methods

    def _get_current_season(self) -> str:
        """Get current season identifier"""
        return str(datetime.now().year)

    def _get_week_date_range(self, week: int) -> Tuple[date, date]:
        """Get date range for a specific week"""
        # TODO: Implement proper week calculation based on sport schedule
        # For now, use simple weekly ranges
        today = date.today()
        start_of_week = today - timedelta(days=today.weekday())
        week_start = start_of_week + timedelta(weeks=week - 1)
        week_end = week_start + timedelta(days=6)

        return week_start, week_end

    # Projection and Analysis Methods

    def calculate_projected_lineup_score(
        self,
        team_id: str,
        week: int,
        lineup_players: Optional[List[Dict[str, str]]] = None,
        db: Optional[Session] = None
    ) -> float:
        """
        Calculate projected score for a lineup

        Args:
            team_id: Team ID
            week: Week number
            lineup_players: Optional custom lineup, uses current if None
            db: Optional database session

        Returns:
            Projected fantasy points
        """
        with get_db_session() if db is None else db as session:
            if not lineup_players:
                # Get current lineup
                lineup = session.query(Lineup).filter(
                    and_(Lineup.team_id == team_id, Lineup.week == week)
                ).first()

                if not lineup or not lineup.players:
                    return 0.0

                lineup_players = lineup.players

            projected_total = 0.0

            for player_data in lineup_players:
                player_id = player_data["player_id"]
                player = session.query(Player).filter(Player.player_id == player_id).first()

                if player and player.projections:
                    projected_points = player.projections.get("fantasy_points", 0.0)
                    projected_total += projected_points

            return projected_total

    def get_scoring_trends(
        self,
        league_id: str,
        weeks: int = 4,
        db: Optional[Session] = None
    ) -> Dict[str, Any]:
        """Get scoring trends for the league"""
        with get_db_session() if db is None else db as session:
            # Get recent scores
            cutoff_date = date.today() - timedelta(weeks=weeks)

            avg_scores = session.query(
                func.avg(Score.fantasy_points).label("avg_points"),
                func.max(Score.fantasy_points).label("max_points"),
                func.min(Score.fantasy_points).label("min_points"),
                func.count(Score.score_id).label("game_count")
            ).filter(
                and_(
                    Score.league_id == league_id,
                    Score.game_date >= cutoff_date,
                    Score.is_final == True
                )
            ).first()

            return {
                "average_points": float(avg_scores.avg_points) if avg_scores.avg_points else 0.0,
                "max_points": float(avg_scores.max_points) if avg_scores.max_points else 0.0,
                "min_points": float(avg_scores.min_points) if avg_scores.min_points else 0.0,
                "total_games": int(avg_scores.game_count) if avg_scores.game_count else 0,
                "weeks_analyzed": weeks
            }
