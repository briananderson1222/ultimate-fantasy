from __future__ import annotations

import builtins
import logging
import uuid as _uuid
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from typing import Any, Union

from sqlalchemy import and_, desc
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from domains.leagues.models.league import League
from domains.leagues.models.team import Team
from domains.lineups.models.lineup import Lineup
from domains.shared.events.publisher import DomainEventPublisher
from domains.shared.exceptions import (
    InsufficientPermissionsError,
    LeagueNotFoundError,
    LineupLockedError,
    LineupNotFoundError,
    LineupValidationError,
    OptimisticLockError,
    UserNotFoundError,
)
from domains.shared.interfaces.lineup_service import LineupServiceInterface
from domains.shared.models.notification import Notification
from domains.sports.models.player import Player
from infrastructure.events.dispatcher import get_event_dispatcher

logger = logging.getLogger(__name__)


UUIDLike = Union[str, _uuid.UUID]


@dataclass
class LineupPlayer:
    """Player in lineup with position."""

    player_id: str
    position: str


@dataclass
class LineupValidation:
    """Lineup validation result."""

    is_valid: bool
    errors: list[str]
    warnings: list[str]
    missing_positions: list[str]
    invalid_players: list[str]


@dataclass
class LineupOptimization:
    """Lineup optimization suggestion."""

    current_projected_points: float
    optimized_projected_points: float
    suggested_changes: list[dict[str, str]]
    improvement_percentage: float


class LineupService(LineupServiceInterface):
    """Domain lineup service with full roster-management logic."""

    def __init__(self, session: Session) -> None:
        self.session = session
        self.default_lock_time_hours = 1
        self.max_retries = 3

        try:
            dispatcher = get_event_dispatcher()
            self.event_publisher: DomainEventPublisher | None = DomainEventPublisher(
                dispatcher, "lineups"
            )
        except RuntimeError:
            self.event_publisher = None

    # ------------------------------------------------------------------
    # Internal utilities
    # ------------------------------------------------------------------
    @staticmethod
    def _as_uuid(value: UUIDLike) -> _uuid.UUID:
        if isinstance(value, _uuid.UUID):
            return value
        return _uuid.UUID(str(value))

    def _normalize_lineup_players(
        self, players: Iterable[LineupPlayer | dict[str, Any]]
    ) -> builtins.list[LineupPlayer]:
        normalized: list[LineupPlayer] = []
        for entry in players:
            if isinstance(entry, LineupPlayer):
                normalized.append(entry)
                continue
            if not isinstance(entry, dict):
                raise LineupValidationError("Invalid lineup player payload")
            player_id = entry.get("player_id")
            position = entry.get("position")
            if not player_id or not position:
                raise LineupValidationError(
                    "Lineup player requires player_id and position"
                )
            normalized.append(
                LineupPlayer(player_id=str(player_id), position=str(position))
            )
        return normalized

    @staticmethod
    def _resolve_week(game_day: date | None, fallback: int = 1) -> int:
        if not game_day:
            return fallback
        # ISO calendar week keeps behaviour predictable without schedule data
        return int(game_day.isocalendar().week)

    # ------------------------------------------------------------------
    # Creation and load helpers
    # ------------------------------------------------------------------
    def create_lineup(
        self,
        *,
        team_id: str,
        week: int,
        game_day: date | None = None,
        user_id: str | None = None,
        db: Session | None = None,
    ) -> Lineup:
        session = db or self.session
        team_uuid = self._as_uuid(team_id)
        team = session.query(Team).filter(Team.team_id == team_uuid).first()
        if not team:
            raise LineupValidationError("Team not found")
        if user_id and str(team.user_id) != str(user_id):
            raise InsufficientPermissionsError("User does not own this team")

        existing = (
            session.query(Lineup)
            .filter(
                and_(
                    Lineup.team_id == team_uuid,
                    Lineup.week == week,
                    Lineup.game_day == game_day,
                )
            )
            .first()
        )
        if existing:
            return existing

        lineup = Lineup(
            team_id=team_uuid,
            week=week,
            game_day=game_day,
            players=[],
            points_scored=0.0,
            is_locked=False,
            version=1,
        )
        session.add(lineup)
        session.commit()
        logger.info(
            "Lineup created for team %s, week %s",
            getattr(team, "team_name", getattr(team, "name", "")),
            week,
        )
        return lineup

    def get_team_lineup(
        self,
        *,
        team_id: str | _uuid.UUID,
        week: int,
        game_day: date | None = None,
        db: Session | None = None,
    ) -> Lineup | None:
        session = db or self.session
        team_uuid = self._as_uuid(team_id)
        return (
            session.query(Lineup)
            .filter(
                and_(
                    Lineup.team_id == team_uuid,
                    Lineup.week == week,
                    Lineup.game_day == game_day,
                )
            )
            .first()
        )

    def get_lineup_by_id(
        self, lineup_id: str, db: Session | None = None
    ) -> Lineup | None:
        session = db or self.session
        lineup_uuid = self._as_uuid(lineup_id)
        return session.query(Lineup).filter(Lineup.lineup_id == lineup_uuid).first()

    def list(
        self,
        *,
        team_id: UUIDLike,
        game_day: date | None = None,
        limit: int = 50,
        offset: int = 0,
        db: Session | None = None,
    ) -> builtins.list[Lineup]:
        session = db or self.session
        team_uuid = self._as_uuid(team_id)
        query = session.query(Lineup).filter(Lineup.team_id == team_uuid)
        if game_day is not None:
            query = query.filter(Lineup.game_day == game_day)
        query = query.order_by(
            desc(Lineup.game_day), desc(Lineup.week), desc(Lineup.created_at)
        )
        bounded_limit = max(1, min(100, limit))
        return query.offset(max(0, offset)).limit(bounded_limit).all()

    def set_lineup(
        self,
        *,
        team_id: UUIDLike,
        game_day: date,
        players: Iterable[LineupPlayer | dict[str, Any]],
        user_id: UUIDLike | None = None,
        week: int | None = None,
        expected_version: int | None = None,
        db: Session | None = None,
    ) -> Lineup:
        """Create or update a lineup for the given day."""

        session = db or self.session
        team_uuid = self._as_uuid(team_id)
        team = session.query(Team).filter(Team.team_id == team_uuid).first()
        owner_id = str(team.user_id) if team else (str(user_id) if user_id else None)
        if team and user_id is not None and str(user_id) != owner_id:
            raise InsufficientPermissionsError("User does not own this team")

        normalized_players = self._normalize_lineup_players(players)

        if team:
            validation = self.validate_lineup(
                team_id=str(team_uuid), lineup_players=normalized_players, db=session
            )
            if not validation.is_valid:
                details = ", ".join(validation.errors) or "Lineup validation failed"
                raise LineupValidationError(f"Invalid lineup: {details}")
        else:
            validation = LineupValidation(
                is_valid=True,
                errors=[],
                warnings=[],
                missing_positions=[],
                invalid_players=[],
            )

        target_week = week or self._resolve_week(game_day)
        lineup = self.get_team_lineup(
            team_id=team_uuid,
            week=target_week,
            game_day=game_day,
            db=session,
        )

        if not lineup:
            lineup = Lineup(
                team_id=team_uuid,
                week=target_week,
                game_day=game_day,
                players=[
                    {"player_id": lp.player_id, "position": lp.position}
                    for lp in normalized_players
                ],
                points_scored=0.0,
                is_locked=False,
                version=1,
            )
            session.add(lineup)
            session.commit()
            self._publish_event(
                "lineup.created",
                str(lineup.lineup_id),
                {
                    "lineup_id": str(lineup.lineup_id),
                    "team_id": str(team_uuid),
                    "game_day": game_day.isoformat(),
                    "week": target_week,
                    "player_count": len(lineup.players or []),
                    "version": lineup.version,
                },
            )
            return lineup

        if lineup.is_locked:
            raise LineupLockedError("Lineup is locked and cannot be modified")

        target_version = (
            expected_version if expected_version is not None else lineup.version
        )

        if team:
            user_for_update = str(user_id) if user_id is not None else owner_id or ""
            return self.update_lineup(
                lineup_id=str(lineup.lineup_id),
                lineup_players=normalized_players,
                user_id=user_for_update,
                expected_version=target_version,
                db=session,
            )

        lineup.players = [
            {"player_id": lp.player_id, "position": lp.position}
            for lp in normalized_players
        ]
        lineup.version += 1
        session.commit()
        self._publish_event(
            "lineup.updated",
            str(lineup.lineup_id),
            {
                "lineup_id": str(lineup.lineup_id),
                "team_id": str(lineup.team_id),
                "week": lineup.week,
                "game_day": lineup.game_day.isoformat() if lineup.game_day else None,
                "player_count": len(lineup.players or []),
                "version": lineup.version,
            },
        )
        return lineup

    def get_team(self, team_id: str, db: Session | None = None) -> Team | None:
        session = db or self.session
        team_uuid = self._as_uuid(team_id)
        return session.query(Team).filter(Team.team_id == team_uuid).first()

    def update_lineup(
        self,
        *,
        lineup_id: str,
        lineup_players: Iterable[LineupPlayer],
        user_id: str,
        expected_version: int | None = None,
        db: Session | None = None,
    ) -> Lineup:
        session = db or self.session
        lineup_uuid = self._as_uuid(lineup_id)
        lineup = session.query(Lineup).filter(Lineup.lineup_id == lineup_uuid).first()
        if not lineup:
            raise LineupNotFoundError("Lineup not found")

        team = session.query(Team).filter(Team.team_id == lineup.team_id).first()
        if not team:
            raise LineupValidationError("Team not found for lineup")
        if str(team.user_id) != str(user_id):
            raise InsufficientPermissionsError("User does not own this team")
        if lineup.is_locked:
            raise LineupLockedError("Lineup is locked and cannot be modified")
        if expected_version is not None and lineup.version != expected_version:
            raise OptimisticLockError(
                f"Version conflict. Expected {expected_version}, got {lineup.version}"
            )

        validation = self.validate_lineup(
            team_id=str(lineup.team_id),
            lineup_players=list(lineup_players),
            db=session,
        )
        if not validation.is_valid:
            raise LineupValidationError(
                f"Invalid lineup: {', '.join(validation.errors)}"
            )

        lineup.players = [
            {"player_id": lp.player_id, "position": lp.position}
            for lp in lineup_players
        ]
        lineup.version += 1
        try:
            session.commit()
            logger.info(
                "Lineup updated for team %s, week %s",
                getattr(team, "team_name", getattr(team, "name", "")),
                lineup.week,
            )
        except IntegrityError as exc:
            session.rollback()
            raise OptimisticLockError("Lineup was modified by another request") from exc

        self._publish_event(
            "lineup.updated",
            str(lineup.lineup_id),
            {
                "lineup_id": str(lineup.lineup_id),
                "team_id": str(lineup.team_id),
                "week": lineup.week,
                "game_day": lineup.game_day.isoformat() if lineup.game_day else None,
                "player_count": len(lineup.players or []),
                "version": lineup.version,
            },
        )
        return lineup

    def set_starting_player(
        self,
        *,
        lineup_id: str,
        player_id: str,
        position: str,
        user_id: str,
        db: Session | None = None,
    ) -> Lineup:
        session = db or self.session
        lineup_uuid = self._as_uuid(lineup_id)
        lineup = session.query(Lineup).filter(Lineup.lineup_id == lineup_uuid).first()
        if not lineup:
            raise LineupNotFoundError("Lineup not found")

        lineup_dict: dict[str, str] = {
            player_data["position"]: player_data["player_id"]
            for player_data in (lineup.players or [])
        }
        lineup_dict[position] = player_id
        players = [
            LineupPlayer(player_id=pid, position=pos)
            for pos, pid in lineup_dict.items()
        ]
        return self.update_lineup(
            lineup_id=lineup_id,
            lineup_players=players,
            user_id=user_id,
            expected_version=lineup.version,
            db=session,
        )

    def swap_players(
        self,
        *,
        lineup_id: str,
        player1_id: str,
        player2_id: str,
        user_id: str,
        db: Session | None = None,
    ) -> Lineup:
        session = db or self.session
        lineup_uuid = self._as_uuid(lineup_id)
        lineup = session.query(Lineup).filter(Lineup.lineup_id == lineup_uuid).first()
        if not lineup:
            raise LineupNotFoundError("Lineup not found")

        lineup_dict = {
            player_data["position"]: player_data["player_id"]
            for player_data in (lineup.players or [])
        }
        player1_pos = next(
            (pos for pos, pid in lineup_dict.items() if pid == player1_id),
            None,
        )
        player2_pos = next(
            (pos for pos, pid in lineup_dict.items() if pid == player2_id),
            None,
        )
        if not player1_pos or not player2_pos:
            raise LineupValidationError("Players must be in lineup to swap")

        lineup_dict[player1_pos], lineup_dict[player2_pos] = (
            lineup_dict[player2_pos],
            lineup_dict[player1_pos],
        )
        players = [
            LineupPlayer(player_id=pid, position=pos)
            for pos, pid in lineup_dict.items()
        ]
        return self.update_lineup(
            lineup_id=lineup_id,
            lineup_players=players,
            user_id=user_id,
            expected_version=lineup.version,
            db=session,
        )

    # ------------------------------------------------------------------
    # Analysis & optimization
    # ------------------------------------------------------------------
    def get_lineup_analysis(
        self, *, lineup_id: str, db: Session | None = None
    ) -> dict[str, Any]:
        session = db or self.session
        lineup_uuid = self._as_uuid(lineup_id)
        lineup = session.query(Lineup).filter(Lineup.lineup_id == lineup_uuid).first()
        if not lineup:
            raise LineupNotFoundError("Lineup not found")

        team = session.query(Team).filter(Team.team_id == lineup.team_id).first()
        if not team:
            raise LineupValidationError("Team not found")
        league = (
            session.query(League).filter(League.league_id == team.league_id).first()
        )
        if not league:
            raise LeagueNotFoundError("League not found")

        player_details = []
        total_projected_points = 0.0
        for player_data in lineup.players or []:
            player = (
                session.query(Player)
                .filter(Player.player_id == player_data["player_id"])
                .first()
            )
            if not player:
                continue
            projected_points = 0.0
            if player.projections and "fantasy_points" in player.projections:
                projected_points = player.projections["fantasy_points"]
            total_projected_points += projected_points
            player_details.append(
                {
                    "player_id": str(player.player_id),
                    "name": player.name,
                    "position": player.position,
                    "lineup_position": player_data["position"],
                    "team_id": player.team_id,
                    "injury_status": player.injury_status,
                    "projected_points": projected_points,
                    "season_stats": player.season_stats,
                }
            )

        position_distribution: dict[str, int] = {}
        for player_data in lineup.players or []:
            pos = player_data["position"]
            position_distribution[pos] = position_distribution.get(pos, 0) + 1

        validation = self.validate_lineup(
            team_id=str(team.team_id),
            lineup_players=[
                LineupPlayer(
                    player_id=p["player_id"],
                    position=p["lineup_position"],
                )
                for p in player_details
            ],
            db=session,
        )

        return {
            "lineup_id": str(lineup.lineup_id),
            "team_name": getattr(team, "team_name", getattr(team, "name", "")),
            "week": lineup.week,
            "is_locked": lineup.is_locked,
            "version": lineup.version,
            "total_projected_points": total_projected_points,
            "player_count": len(player_details),
            "players": player_details,
            "position_distribution": position_distribution,
            "validation": validation,
        }

    def suggest_lineup_optimization(
        self, *, lineup_id: str, db: Session | None = None
    ) -> LineupOptimization:
        session = db or self.session
        lineup_uuid = self._as_uuid(lineup_id)
        lineup = session.query(Lineup).filter(Lineup.lineup_id == lineup_uuid).first()
        if not lineup:
            raise LineupNotFoundError("Lineup not found")

        current_analysis = self.get_lineup_analysis(
            lineup_id=str(lineup_uuid), db=session
        )
        current_projected = current_analysis["total_projected_points"]

        team = session.query(Team).filter(Team.team_id == lineup.team_id).first()
        if not team:
            raise LineupValidationError("Team not found")
        roster_player_ids = team.roster or []

        roster_players = (
            session.query(Player).filter(Player.player_id.in_(roster_player_ids)).all()
        )

        lineup_positions = current_analysis["position_distribution"].keys()
        list(lineup.players or [])
        best_projected = current_projected
        suggestions: list[dict[str, str]] = []

        for player in roster_players:
            eligible_positions = self._get_player_eligible_positions(
                player,
                session.query(League)
                .filter(League.league_id == team.league_id)
                .first(),
            )
            for position in eligible_positions:
                if position not in lineup_positions:
                    continue
                current_player = next(
                    (p for p in (lineup.players or []) if p["position"] == position),
                    None,
                )
                current_points = 0.0
                if current_player:
                    current_projection = (
                        session.query(Player)
                        .filter(Player.player_id == current_player["player_id"])
                        .first()
                    )
                    if current_projection and current_projection.projections:
                        current_points = current_projection.projections.get(
                            "fantasy_points", 0.0
                        )
                new_points = (
                    player.projections.get("fantasy_points", 0.0)
                    if player.projections
                    else 0.0
                )
                if new_points > current_points:
                    improvement = new_points - current_points
                    if best_projected + improvement > best_projected:
                        best_projected = current_projected + improvement
                        suggestions.append(
                            {
                                "out": (
                                    current_player["player_id"]
                                    if current_player
                                    else ""
                                ),
                                "in": str(player.player_id),
                                "position": position,
                            }
                        )

        improvement_percentage = 0.0
        if current_projected > 0:
            improvement_percentage = (
                (best_projected - current_projected) / current_projected
            ) * 100

        return LineupOptimization(
            current_projected_points=current_projected,
            optimized_projected_points=best_projected,
            suggested_changes=suggestions,
            improvement_percentage=improvement_percentage,
        )

    def validate_lineup(
        self,
        *,
        team_id: str,
        lineup_players: Iterable[LineupPlayer],
        db: Session | None = None,
    ) -> LineupValidation:
        session = db or self.session
        team_uuid = self._as_uuid(team_id)
        team = session.query(Team).filter(Team.team_id == team_uuid).first()
        if not team:
            raise LineupValidationError("Team not found")
        league = (
            session.query(League).filter(League.league_id == team.league_id).first()
        )
        if not league:
            raise LeagueNotFoundError("League not found")

        errors: list[str] = []
        warnings: list[str] = []
        missing_positions: list[str] = []
        invalid_players: list[str] = []
        player_ids_used: set[str] = set()
        positions_filled: dict[str, int] = {}

        roster_settings = league.roster_settings or {}
        required_positions: list[str] = roster_settings.get("starting_positions", [])

        for lineup_player in lineup_players:
            if lineup_player.player_id in player_ids_used:
                errors.append(f"Player {lineup_player.player_id} used multiple times")
            player_ids_used.add(lineup_player.player_id)

            try:
                player_uuid = (
                    _uuid.UUID(lineup_player.player_id)
                    if isinstance(lineup_player.player_id, str)
                    else lineup_player.player_id
                )
            except ValueError:
                invalid_players.append(lineup_player.player_id)
                errors.append(f"Invalid player ID format: {lineup_player.player_id}")
                continue

            player = (
                session.query(Player).filter(Player.player_id == player_uuid).first()
            )
            if not player:
                invalid_players.append(lineup_player.player_id)
                errors.append(f"Player {lineup_player.player_id} not found")
                continue

            if lineup_player.player_id not in (team.roster or []):
                invalid_players.append(lineup_player.player_id)
                errors.append(f"Player {player.name} not on team roster")
                continue

            eligible_positions = self._get_player_eligible_positions(player, league)
            if lineup_player.position not in eligible_positions:
                errors.append(
                    f"Player {player.name} not eligible for position {lineup_player.position}"
                )

            positions_filled[lineup_player.position] = (
                positions_filled.get(lineup_player.position, 0) + 1
            )

        for required_pos in required_positions:
            if required_pos not in positions_filled:
                missing_positions.append(required_pos)

        for position, count in positions_filled.items():
            required_count = required_positions.count(position)
            if required_count and count > required_count:
                errors.append(f"Too many players at position {position}")

        if missing_positions:
            errors.extend(
                [f"Missing required position: {pos}" for pos in missing_positions]
            )

        is_valid = len(errors) == 0
        return LineupValidation(
            is_valid=is_valid,
            errors=errors,
            warnings=warnings,
            missing_positions=missing_positions,
            invalid_players=invalid_players,
        )

    def _get_player_eligible_positions(
        self, player: Player, league: League
    ) -> builtins.list[str]:
        eligible = [player.position]
        if league.sport == "nfl":
            if player.position in {"RB", "WR", "TE"}:
                eligible.append("FLEX")
            if player.position in {"RB", "WR", "TE", "QB"}:
                eligible.append("SUPERFLEX")
        elif league.sport == "wnba":
            eligible.append("FLEX")
        return eligible

    # ------------------------------------------------------------------
    # Locking and reminders
    # ------------------------------------------------------------------
    def lock_lineup(self, *, lineup_id: str, db: Session | None = None) -> Lineup:
        session = db or self.session
        lineup_uuid = self._as_uuid(lineup_id)
        lineup = session.query(Lineup).filter(Lineup.lineup_id == lineup_uuid).first()
        if not lineup:
            raise LineupNotFoundError("Lineup not found")
        lineup.is_locked = True
        session.commit()
        logger.info("Lineup locked", extra={"lineup_id": lineup_id})
        return lineup

    def unlock_lineup(
        self,
        *,
        lineup_id: str,
        commissioner_id: str,
        db: Session | None = None,
    ) -> Lineup:
        session = db or self.session
        lineup_uuid = self._as_uuid(lineup_id)
        lineup = session.query(Lineup).filter(Lineup.lineup_id == lineup_uuid).first()
        if not lineup:
            raise LineupNotFoundError("Lineup not found")
        team = session.query(Team).filter(Team.team_id == lineup.team_id).first()
        league = (
            session.query(League).filter(League.league_id == team.league_id).first()
        )
        if str(league.commissioner_id) != str(commissioner_id):
            raise InsufficientPermissionsError("Only commissioner can unlock lineups")
        lineup.is_locked = False
        session.commit()
        logger.info("Lineup unlocked", extra={"lineup_id": lineup_id})
        return lineup

    def auto_lock_lineups(
        self,
        *,
        league_id: str,
        lock_time: datetime | None = None,
        db: Session | None = None,
    ) -> int:
        session = db or self.session
        if not lock_time:
            lock_time = datetime.utcnow() + timedelta(
                hours=self.default_lock_time_hours
            )
        league_uuid = self._as_uuid(league_id)
        teams = session.query(Team).filter(Team.league_id == league_uuid).all()
        team_ids = [team.team_id for team in teams]
        lineups = (
            session.query(Lineup)
            .filter(
                and_(
                    Lineup.team_id.in_(team_ids),
                    Lineup.is_locked.is_(False),
                )
            )
            .all()
        )
        count = 0
        for lineup in lineups:
            lineup.is_locked = True
            count += 1
        session.commit()
        if count:
            logger.info("Auto-locked %s lineups", count)
        return count

    def get_lineup_reminders(
        self,
        *,
        league_id: str,
        reminder_hours: int = 24,
        db: Session | None = None,
    ) -> builtins.list[str]:
        # TODO: implement schedule-based reminders
        return []

    def send_lineup_reminders(
        self,
        *,
        league_id: str,
        week: int,
        db: Session | None = None,
    ) -> int:
        session = db or self.session
        teams_needing_reminders = self.get_lineup_reminders(
            league_id=league_id, db=session
        )
        notifications_sent = 0
        for team_id in teams_needing_reminders:
            team = session.query(Team).filter(Team.team_id == team_id).first()
            if team:
                notification = Notification(
                    user_id=team.user_id,
                    league_id=league_id,
                    team_id=team_id,
                    notification_type="lineup_reminder",
                    title="Lineup Reminder",
                    message=f"Don't forget to set your lineup for Week {week}!",
                    action_url=f"/leagues/{league_id}/lineup",
                    priority="normal",
                )
                session.add(notification)
                notifications_sent += 1
        session.commit()
        if notifications_sent:
            logger.info(
                "Sent %s lineup reminders for league %s",
                notifications_sent,
                league_id,
            )
        return notifications_sent

    # ------------------------------------------------------------------
    # Bulk operations
    # ------------------------------------------------------------------
    def copy_lineup(
        self,
        *,
        source_lineup_id: str,
        target_week: int,
        target_game_day: date | None = None,
        user_id: str,
        db: Session | None = None,
    ) -> Lineup:
        session = db or self.session
        source_uuid = self._as_uuid(source_lineup_id)
        source_lineup = (
            session.query(Lineup).filter(Lineup.lineup_id == source_uuid).first()
        )
        if not source_lineup:
            raise LineupNotFoundError("Source lineup not found")
        team = session.query(Team).filter(Team.team_id == source_lineup.team_id).first()
        if not team or str(team.user_id) != str(user_id):
            raise InsufficientPermissionsError("User does not own this team")

        target_lineup = self.get_team_lineup(
            team_id=str(source_lineup.team_id),
            week=target_week,
            game_day=target_game_day,
            db=session,
        )
        if not target_lineup:
            target_lineup = self.create_lineup(
                team_id=str(source_lineup.team_id),
                week=target_week,
                game_day=target_game_day,
                user_id=user_id,
                db=session,
            )

        if not target_lineup.is_locked:
            players = [
                LineupPlayer(player_id=p["player_id"], position=p["position"])
                for p in (source_lineup.players or [])
            ]
            target_lineup = self.update_lineup(
                lineup_id=str(target_lineup.lineup_id),
                lineup_players=players,
                user_id=user_id,
                expected_version=target_lineup.version,
                db=session,
            )
            logger.info(
                "Lineup copied from week %s to week %s",
                source_lineup.week,
                target_week,
            )

        return target_lineup

    def auto_set_lineup(
        self,
        *,
        team_id: str,
        week: int,
        db: Session | None = None,
    ) -> Lineup:
        session = db or self.session
        team_uuid = self._as_uuid(team_id)
        team = session.query(Team).filter(Team.team_id == team_uuid).first()
        if not team:
            raise LineupValidationError("Team not found")
        league = (
            session.query(League).filter(League.league_id == team.league_id).first()
        )
        if not league:
            raise LeagueNotFoundError("League not found")

        lineup = self.get_team_lineup(team_id=team_uuid, week=week, db=session)
        if not lineup:
            lineup = self.create_lineup(
                team_id=str(team_uuid),
                week=week,
                user_id=str(team.user_id),
                db=session,
            )

        if lineup.is_locked:
            raise LineupLockedError("Lineup is locked")

        roster_players = (
            session.query(Player).filter(Player.player_id.in_(team.roster or [])).all()
        )

        selected: dict[str, str] = {}
        for player in roster_players:
            eligible_positions = self._get_player_eligible_positions(player, league)
            for position in eligible_positions:
                if position not in selected:
                    selected[position] = str(player.player_id)
                    break

        players = [
            LineupPlayer(player_id=pid, position=pos) for pos, pid in selected.items()
        ]
        return self.update_lineup(
            lineup_id=str(lineup.lineup_id),
            lineup_players=players,
            user_id=str(team.user_id),
            expected_version=lineup.version,
            db=session,
        )

    def get_lineup_history(
        self,
        *,
        team_id: str,
        limit: int = 10,
        offset: int = 0,
        db: Session | None = None,
    ) -> builtins.list[dict[str, Any]]:
        session = db or self.session
        team_uuid = self._as_uuid(team_id)
        lineups = (
            session.query(Lineup)
            .filter(Lineup.team_id == team_uuid)
            .order_by(desc(Lineup.week))
            .offset(offset)
            .limit(limit)
            .all()
        )
        history: list[dict[str, Any]] = []
        for lineup in lineups:
            history.append(
                {
                    "lineup_id": str(lineup.lineup_id),
                    "week": lineup.week,
                    "game_day": (
                        lineup.game_day.isoformat() if lineup.game_day else None
                    ),
                    "points_scored": lineup.points_scored,
                    "is_locked": lineup.is_locked,
                    "player_count": len(lineup.players or []),
                    "created_at": lineup.created_at.isoformat(),
                }
            )
        return history

    def get_league_lineups(
        self,
        *,
        league_id: str,
        week: int | None = None,
        db: Session | None = None,
    ) -> builtins.list[Lineup]:
        session = db or self.session
        league_uuid = self._as_uuid(league_id)
        teams = session.query(Team).filter(Team.league_id == league_uuid).all()
        team_ids = [team.team_id for team in teams]
        query = session.query(Lineup).filter(Lineup.team_id.in_(team_ids))
        if week is not None:
            query = query.filter(Lineup.week == week)
        return query.all()

    def get_team_lineup_analytics(
        self,
        *,
        team_id: str,
        db: Session | None = None,
    ) -> dict[str, Any]:
        session = db or self.session
        team_uuid = self._as_uuid(team_id)
        lineups = (
            session.query(Lineup)
            .filter(Lineup.team_id == team_uuid)
            .order_by(Lineup.week)
            .all()
        )
        total_points = sum(lineup.points_scored or 0 for lineup in lineups)
        weeks = len(lineups)
        return {
            "team_id": str(team_uuid),
            "total_points": total_points,
            "weeks": weeks,
            "average_points": (total_points / weeks) if weeks else 0.0,
        }

    # ------------------------------------------------------------------
    # Interface async wrappers
    # ------------------------------------------------------------------
    async def get_lineup(self, lineup_id: str) -> Lineup:  # type: ignore[override]
        lineup = self.get_lineup_by_id(lineup_id, self.session)
        if not lineup:
            raise LineupNotFoundError("Lineup not found")
        return lineup

    async def validate_lineup_ownership(
        self, lineup_id: str, user_id: str
    ) -> bool:  # type: ignore[override]
        lineup = self.get_lineup_by_id(lineup_id, self.session)
        if not lineup:
            return False
        team = self.session.query(Team).filter(Team.team_id == lineup.team_id).first()
        if not team:
            return False
        return str(team.user_id) == str(user_id)

    async def get_lineup_by_user_league(
        self, user_id: str, league_id: str
    ) -> Lineup:  # type: ignore[override]
        team = (
            self.session.query(Team)
            .filter(
                Team.user_id == _uuid.UUID(str(user_id)),
                Team.league_id == _uuid.UUID(str(league_id)),
            )
            .first()
        )
        if not team:
            raise UserNotFoundError("User has no team in league")
        lineup = (
            self.session.query(Lineup)
            .filter(Lineup.team_id == team.team_id)
            .order_by(Lineup.game_day.desc())
            .first()
        )
        if not lineup:
            raise LineupValidationError("No lineup found for user in league")
        return lineup

    async def get_lineups_by_league(
        self, league_id: str
    ) -> builtins.list[Lineup]:  # type: ignore[override]
        return self.get_league_lineups(league_id=league_id)

    async def is_lineup_active(self, lineup_id: str) -> bool:  # type: ignore[override]
        return self.get_lineup_by_id(lineup_id, self.session) is not None

    async def get_lineup_slots(
        self, lineup_id: str
    ) -> builtins.list[dict[str, Any]]:  # type: ignore[override]
        lineup = self.get_lineup_by_id(lineup_id, self.session)
        if not lineup:
            raise LineupNotFoundError("Lineup not found")
        return lineup.players or []

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------
    def _publish_event(
        self, event: str, entity_id: str, payload: dict[str, Any]
    ) -> None:
        if not self.event_publisher:
            return
        import asyncio

        task = asyncio.create_task(
            self.event_publisher.publish_event(event, entity_id, payload)
        )
        task.add_done_callback(lambda t: t.exception())
