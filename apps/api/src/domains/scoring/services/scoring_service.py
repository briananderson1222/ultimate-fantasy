from __future__ import annotations

import contextlib
import uuid as _uuid
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from typing import Any

from sqlalchemy import and_
from sqlalchemy.orm import Session

from domains.leagues.models.league import League
from domains.leagues.models.team import Team
from domains.lineups.models.lineup import Lineup
from domains.scoring.models.score import Score
from domains.shared.events.publisher import DomainEventPublisher
from domains.shared.interfaces.scoring_service import ScoringServiceInterface
from domains.sports.models.player import Player
from infrastructure.events.dispatcher import get_event_dispatcher

try:
    from infrastructure.database.session_factory import get_db_session
except ImportError:
    get_db_session = None  # type: ignore[misc,assignment]

try:
    from infrastructure.logging.domain_logger import get_logger
except ImportError:
    import logging

    get_logger = logging.getLogger  # type: ignore[assignment]

# Try to import consolidated sports data service
try:
    from domains.sports.services.sports_data_service import SportsDataService, SportType
except ImportError:
    SportsDataService = None  # type: ignore[misc,assignment]
    SportType = None  # type: ignore[misc,assignment]


logger = get_logger(__name__)


@dataclass
class ScoringResult:
    """Result of scoring calculation"""

    player_id: str
    total_points: float
    breakdown: dict[str, float]
    bonus_points: float
    stat_values: dict[str, Any]


@dataclass
class TeamScoring:
    """Team's total scoring for a period"""

    team_id: str
    total_points: float
    starting_points: float
    bench_points: float
    player_scores: list[ScoringResult]


@dataclass
class MatchupResult:
    """Head-to-head matchup result"""

    home_team: TeamScoring
    away_team: TeamScoring
    winner: str | None  # team_id of winner, None for tie
    margin: float


class ScoringServiceError(Exception):
    """Base exception for scoring service errors"""



class ScoringService(ScoringServiceInterface):
    def __init__(
        self, session: Session, sports_data_service: Any | None = None
    ) -> None:
        self.session = session
        self.sports_data_service = sports_data_service
        self.scoring_cache_duration_minutes = 5
        self.real_time_update_interval_seconds = 30

        # Initialize event publishing
        try:
            dispatcher = get_event_dispatcher()
            self.event_publisher: DomainEventPublisher | None = DomainEventPublisher(
                dispatcher, "scoring"
            )
        except RuntimeError:
            # Event dispatcher not initialized, disable events
            self.event_publisher = None

    def ingest_player_stats(self, *, game_day: date, items: Iterable[dict]) -> int:
        """Ingest raw stat items and persist Score rows.

        Each item must include: player_id (UUID as str), stats (dict)
        Returns number of upserts (currently inserts only).
        """
        count = 0
        for it in items:
            player_identifier = it.get("player_id")
            try:
                player_uuid = _uuid.UUID(str(player_identifier))
            except Exception:
                continue

            score = Score(
                player_id=player_uuid,
                game_day=game_day,
                stat_values=it.get("stats") or {},
            )
            self.session.add(score)
            count += 1
        self.session.flush()

        # Publish player stats ingested event
        if self.event_publisher:
            try:
                import asyncio

                task = asyncio.create_task(
                    self.event_publisher.publish_event(
                        "player_stats_ingested",
                        f"{game_day.isoformat()}_batch",
                        {
                            "game_day": game_day.isoformat(),
                            "player_count": count,
                            "stats_ingested": True,
                        },
                    )
                )
                task.add_done_callback(lambda t: t.exception())

                # Publish integration event for lineups to recalculate scores
                task = asyncio.create_task(
                    self.event_publisher.publish_integration_event(
                        "stats_available",
                        f"{game_day.isoformat()}_batch",
                        {
                            "game_day": game_day.isoformat(),
                            "player_count": count,
                        },
                        target_domains=["lineups", "leagues"],
                    )
                )
                task.add_done_callback(lambda t: t.exception())
            except Exception as e:
                import logging

                logging.getLogger(__name__).debug(f"Event publishing failed: {e}")

        return count

    # Core Fantasy Scoring Methods (from legacy service)

    def calculate_player_score(
        self,
        player_id: str,
        league_id: str,
        game_date: date,
        stat_values: dict[str, Any],
        is_final: bool = False,
    ) -> ScoringResult:
        """
        Calculate fantasy points for a player's performance

        Args:
            player_id: Player ID
            league_id: League ID for scoring rules
            game_date: Date of the game
            stat_values: Player's statistical performance
            is_final: Whether this is final scoring or projected

        Returns:
            ScoringResult with point breakdown
        """
        # Get player and league
        player = (
            self.session.query(Player).filter(Player.player_id == player_id).first()
        )
        league = (
            self.session.query(League).filter(League.league_id == league_id).first()
        )

        if not player or not league:
            raise ScoringServiceError("Player or league not found")

        # Get scoring rules for the league
        scoring_rules = league.scoring_rules or {}

        # Calculate points breakdown
        breakdown = {}

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
        bonus_points = self._calculate_bonus_points(
            stat_values, scoring_rules, player.sport
        )

        return ScoringResult(
            player_id=player_id,
            total_points=total_points,
            breakdown=breakdown,
            bonus_points=bonus_points,
            stat_values=stat_values,
        )

    def update_player_score(
        self,
        player_id: str,
        league_id: str,
        game_date: date,
        week: int,
        stat_values: dict[str, Any],
        is_final: bool = False,
        game_id: str | None = None,
        opponent_team: str | None = None,
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

        Returns:
            Updated Score record
        """
        # Calculate fantasy points
        scoring_result = self.calculate_player_score(
            player_id, league_id, game_date, stat_values, is_final
        )

        # Find existing score or create new one
        score = (
            self.session.query(Score)
            .filter(and_(Score.player_id == player_id, Score.game_day == game_date))
            .first()
        )

        if score:
            # Update existing score
            score.stat_values = stat_values
            # Add calculated fantasy points to existing stats
            if not score.stat_values:
                score.stat_values = {}
            score.stat_values.update(
                {
                    "fantasy_points": scoring_result.total_points,
                    "bonus_points": scoring_result.bonus_points,
                    "points_breakdown": scoring_result.breakdown,
                }
            )
        else:
            # Create new score with fantasy points included
            enhanced_stats = stat_values.copy()
            enhanced_stats.update(
                {
                    "fantasy_points": scoring_result.total_points,
                    "bonus_points": scoring_result.bonus_points,
                    "points_breakdown": scoring_result.breakdown,
                    "points": scoring_result.total_points,  # For compatibility
                }
            )

            score = Score(
                player_id=_uuid.UUID(player_id),
                game_day=game_date,
                stat_values=enhanced_stats,
            )
            self.session.add(score)

        self.session.flush()

        logger.info(
            f"Score updated for player {player_id}: {scoring_result.total_points} points"
        )
        return score

    def calculate_team_score(
        self, team_id: str, week: int, game_day: date | None = None
    ) -> TeamScoring:
        """
        Calculate total team score for a week/day

        Args:
            team_id: Team ID
            week: Week number
            game_day: Optional specific game day

        Returns:
            TeamScoring with breakdown
        """
        team_uuid = _uuid.UUID(team_id)

        # Get lineups for the team
        lineup_query = self.session.query(Lineup).filter(Lineup.team_id == team_uuid)
        if game_day:
            lineup_query = lineup_query.filter(Lineup.game_day == game_day)

        lineups = lineup_query.all()

        total_points = 0.0
        starting_points = 0.0
        bench_points = 0.0
        player_scores = []

        for lineup in lineups:
            if not lineup.players:
                continue

            for player_data in lineup.players:
                player_id = player_data.get("player_id")
                is_starter = player_data.get("is_starter", True)

                if not player_id:
                    continue

                # Get score for this player on this game day
                score = (
                    self.session.query(Score)
                    .filter(
                        and_(
                            Score.player_id == _uuid.UUID(player_id),
                            Score.game_day == lineup.game_day,
                        )
                    )
                    .first()
                )

                if score and score.stat_values:
                    points = score.stat_values.get(
                        "fantasy_points", 0
                    ) or score.stat_values.get("points", 0)
                    try:
                        points = float(points)
                    except (ValueError, TypeError):
                        points = 0.0

                    # Create scoring result for this player
                    player_scoring = ScoringResult(
                        player_id=player_id,
                        total_points=points,
                        breakdown=score.stat_values.get("points_breakdown", {}),
                        bonus_points=score.stat_values.get("bonus_points", 0),
                        stat_values=score.stat_values,
                    )
                    player_scores.append(player_scoring)

                    total_points += points
                    if is_starter:
                        starting_points += points
                    else:
                        bench_points += points

        return TeamScoring(
            team_id=team_id,
            total_points=total_points,
            starting_points=starting_points,
            bench_points=bench_points,
            player_scores=player_scores,
        )

    # Sport-specific scoring methods

    def _calculate_mlb_scoring(
        self, stat_values: dict[str, Any], scoring_rules: dict[str, Any]
    ) -> dict[str, float]:
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
        self, stat_values: dict[str, Any], scoring_rules: dict[str, Any]
    ) -> dict[str, float]:
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
        self, stat_values: dict[str, Any], scoring_rules: dict[str, Any]
    ) -> dict[str, float]:
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
        self, stat_values: dict[str, Any], scoring_rules: dict[str, Any], sport: str
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

    def _get_week_date_range(self, week: int) -> tuple[date, date]:
        """Get date range for a specific week"""
        # TODO: Implement proper week calculation based on sport schedule
        # For now, use simple weekly ranges
        today = date.today()
        start_of_week = today - timedelta(days=today.weekday())
        week_start = start_of_week + timedelta(weeks=week - 1)
        week_end = week_start + timedelta(days=6)

        return week_start, week_end

    def compute_league_scoreboard(
        self, *, league_id: _uuid.UUID | str, game_day: date | None
    ) -> list[dict[str, Any]]:
        """Compute per-team totals for a league.

        Aggregates scores by summing stats.points for players listed in each
        team's lineups.

        - league_id may be UUID or str
        - if game_day is None, include all days; otherwise filter to that day
        - returns list of { team_id: UUID, total_points: int, lineup_count: int }
          sorted by total_points desc
        """
        import uuid as _uuid

        from domains.lineups.models.lineup import Lineup
        from domains.scoring.models.score import Score

        league_uuid = _uuid.UUID(league_id) if isinstance(league_id, str) else league_id

        # Fetch relevant lineups for the league (optionally filter by day)
        q = (
            self.session.query(Lineup)
            .join(Team, Team.team_id == Lineup.team_id)
            .filter(Team.league_id == league_uuid)
        )
        if game_day is not None:
            q = q.filter(Lineup.game_day == game_day)

        lineups: list[Lineup] = q.all()

        totals: dict[_uuid.UUID, int] = {}
        counts: dict[_uuid.UUID, int] = {}

        for lu in lineups:
            team_id = lu.team_id
            counts[team_id] = counts.get(team_id, 0) + 1

            # players stored as list of dicts with player_id as str
            player_ids = []
            for p in lu.players or []:
                pid = p.get("player_id")
                if pid is None:
                    continue
                try:
                    pid_uuid = _uuid.UUID(str(pid))
                except ValueError:
                    continue
                player_ids.append(pid_uuid)

            # Sum points for these players on the lineup's game_day
            total_for_lineup = 0
            if player_ids:
                scores = (
                    self.session.query(Score)
                    .filter(
                        Score.player_id.in_(player_ids), Score.game_day == lu.game_day
                    )
                    .all()
                )
                for s in scores:
                    stats = s.stat_values or {}
                    pts = stats.get("points", 0)
                    try:
                        pts_val = int(pts)
                    except (ValueError, TypeError):
                        pts_val = 0
                    total_for_lineup += pts_val

            totals[team_id] = totals.get(team_id, 0) + total_for_lineup

        items = [
            {
                "team_id": tid,
                "total_points": totals.get(tid, 0),
                "lineup_count": counts.get(tid, 0),
            }
            for tid in totals
        ]
        items.sort(key=lambda x: float(str(x["total_points"])), reverse=True)
        return items

    # Interface implementation methods
    async def calculate_lineup_score(
        self, lineup_id: str, period: str
    ) -> dict[str, Any]:
        """Calculate total score for a lineup in a specific period."""
        from domains.lineups.models.lineup import Lineup

        lineup_uuid = _uuid.UUID(lineup_id)
        lineup = (
            self.session.query(Lineup).filter(Lineup.lineup_id == lineup_uuid).first()
        )
        if not lineup:
            raise ValueError(f"Lineup with ID {lineup_id} not found")

        # Calculate total points for the lineup's game day
        total_points = 0
        player_ids = []
        for player in lineup.players or []:
            pid = player.get("player_id")
            if pid:
                try:
                    player_ids.append(_uuid.UUID(str(pid)))
                except ValueError:
                    continue

        if player_ids:
            scores = (
                self.session.query(Score)
                .filter(
                    Score.player_id.in_(player_ids), Score.game_day == lineup.game_day
                )
                .all()
            )
            for score in scores:
                stats = score.stat_values or {}
                points = stats.get("points", 0)
                with contextlib.suppress(ValueError, TypeError):
                    total_points += int(points)

        return {
            "score_id": str(_uuid.uuid4()),
            "lineup_id": lineup_id,
            "period": period,
            "total_points": total_points,
            "calculated_at": date.today().isoformat(),
        }

    async def get_scoring_rules(self, league_id: str) -> dict[str, Any]:
        """Get scoring rules for a specific league."""
        # For now, return default scoring rules
        # In the future, this would be configurable per league
        return {
            "rules_id": str(_uuid.uuid4()),
            "league_id": league_id,
            "passing_yard": 0.04,
            "passing_td": 4,
            "rushing_yard": 0.1,
            "rushing_td": 6,
            "receiving_yard": 0.1,
            "receiving_td": 6,
            "interception": -2,
            "fumble": -2,
        }

    async def audit_score_calculation(self, score_id: str) -> dict[str, Any]:
        """Get audit trail for a score calculation."""
        # For now, return a placeholder audit trail
        # In the future, this would track actual calculation history
        return {
            "audit_id": str(_uuid.uuid4()),
            "score_id": score_id,
            "calculation_method": "standard",
            "calculated_by": "system",
            "calculation_steps": [
                {"step": "retrieve_stats", "status": "completed"},
                {"step": "apply_rules", "status": "completed"},
                {"step": "sum_totals", "status": "completed"},
            ],
        }

    async def get_player_performance(
        self, player_id: str, period: str
    ) -> dict[str, Any]:
        """Get performance data for a specific player in a period."""
        player_uuid = _uuid.UUID(player_id)

        # Get all scores for the player
        scores = self.session.query(Score).filter(Score.player_id == player_uuid).all()

        total_points = 0
        game_count = len(scores)
        for score in scores:
            stats = score.stat_values or {}
            points = stats.get("points", 0)
            with contextlib.suppress(ValueError, TypeError):
                total_points += int(points)

        return {
            "player_id": player_id,
            "period": period,
            "total_points": total_points,
            "games_played": game_count,
            "average_points": total_points / max(1, game_count),
        }

    async def get_league_standings(
        self, league_id: str, period: str
    ) -> list[dict[str, Any]]:
        """Get current standings for a league in a specific period."""
        league_uuid = _uuid.UUID(league_id)

        # Use the existing compute_league_scoreboard method
        scoreboard = self.compute_league_scoreboard(
            league_id=league_uuid, game_day=None
        )

        # Convert to standings format
        standings = []
        for rank, item in enumerate(scoreboard, 1):
            standings.append(
                {
                    "rank": rank,
                    "team_id": str(item["team_id"]),
                    "total_points": item["total_points"],
                    "games_played": item["lineup_count"],
                }
            )

        return standings

    async def recalculate_scores(
        self, league_id: str, period: str
    ) -> list[dict[str, Any]]:
        """Recalculate all scores for a league in a specific period."""
        from domains.lineups.models.lineup import Lineup

        league_uuid = _uuid.UUID(league_id)

        # Get all teams in the league
        teams = self.session.query(Team).filter(Team.league_id == league_uuid).all()
        team_ids = [team.team_id for team in teams]

        # Get all lineups for these teams
        lineups = self.session.query(Lineup).filter(Lineup.team_id.in_(team_ids)).all()

        scores = []
        for lineup in lineups:
            score = await self.calculate_lineup_score(str(lineup.lineup_id), period)
            scores.append(score)

        return scores
