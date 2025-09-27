from __future__ import annotations

import asyncio
import random
import uuid as _uuid
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any

from sqlalchemy.orm import Session

from domains.drafts.models.draft import Draft
from domains.leagues.models.league import League
from domains.leagues.models.team import Team
from domains.shared.models.notification import Notification
from domains.sports.models.player import Player
from infrastructure.database.session_factory import get_session_factory
from infrastructure.logging.domain_logger import get_logger

logger = get_logger(__name__)


class DraftStatus(Enum):
    """Draft status types."""

    SCHEDULED = "scheduled"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"


class DraftType(Enum):
    """Draft types."""

    SNAKE = "snake"
    AUCTION = "auction"
    LINEAR = "linear"


@dataclass
class DraftPick:
    """Draft pick information."""

    pick_number: int
    round_number: int
    team_id: str
    player_id: str | None = None
    pick_time: datetime | None = None
    is_autopick: bool = False


@dataclass
class DraftSettings:
    """Draft configuration settings."""

    draft_type: str = "snake"
    pick_timer_seconds: int = 90
    auto_draft_enabled: bool = True
    draft_order: list[str] | None = None
    pause_between_rounds: bool = False
    allow_pick_trading: bool = False
    rounds: int | None = None


class DraftServiceError(Exception):
    """Base exception for draft service errors."""


class DraftNotFoundError(DraftServiceError):
    """Draft was not found."""


class InvalidDraftStateError(DraftServiceError):
    """Invalid state transition attempted."""


class PickTimerExpiredError(DraftServiceError):
    """Pick timer expired before selection."""


class DraftService:
    """Domain draft service providing roster draft workflows."""

    def __init__(self, session: Session) -> None:
        self.session = session
        self.timer_callbacks: dict[str, list[Callable[[int], None]]] = {}
        self.active_timers: dict[str, asyncio.Task] = {}
        self.min_pick_timer = 30
        self.max_pick_timer = 300

    # ------------------------------------------------------------------
    # Draft lifecycle
    # ------------------------------------------------------------------
    def create_draft(
        self,
        *,
        league_id: str,
        commissioner_id: str,
        draft_settings: DraftSettings | None = None,
        db: Session | None = None,
    ) -> Draft:
        session = db or self.session

        league = session.query(League).filter(League.league_id == league_id).first()
        if not league:
            raise DraftServiceError("League not found")
        if str(league.commissioner_id) != str(commissioner_id):
            raise DraftServiceError("Only commissioner can create draft")
        if league.status != "setup":
            raise DraftServiceError("League must be in setup phase to create draft")

        existing = session.query(Draft).filter(Draft.league_id == league_id).first()
        if existing:
            raise DraftServiceError("Draft already exists for this league")

        teams = (
            session.query(Team)
            .filter(Team.league_id == league_id)
            .order_by(Team.created_at)
            .all()
        )
        if len(teams) < 2:
            raise DraftServiceError("Need at least 2 teams to create a draft")

        draft_settings = draft_settings or DraftSettings()
        draft_order = (
            draft_settings.draft_order
            if draft_settings.draft_order
            else self._generate_draft_order(teams)
        )

        pick_timer = max(
            self.min_pick_timer,
            min(self.max_pick_timer, draft_settings.pick_timer_seconds),
        )
        rounds = (
            draft_settings.rounds
            if draft_settings.rounds and draft_settings.rounds > 0
            else self._calculate_total_rounds(league, teams)
        )

        draft = Draft(
            league_id=_uuid.UUID(str(league_id)),
            draft_type=draft_settings.draft_type,
            status=DraftStatus.SCHEDULED.value,
            pick_timer=pick_timer,
            pick_time_limit=pick_timer,
            auto_draft_enabled=draft_settings.auto_draft_enabled,
            rounds=rounds,
            current_pick=1,
            current_round=1,
            current_team_id=_uuid.UUID(draft_order[0]) if draft_order else None,
            draft_order=draft_order,
            picks=[],
        )

        session.add(draft)
        session.commit()
        session.refresh(draft)

        logger.info(
            "Draft created",
            extra={"league_id": league_id, "draft_id": str(draft.draft_id)},
        )
        return draft

    def start_draft(
        self,
        *,
        draft_id: str,
        commissioner_id: str,
        db: Session | None = None,
    ) -> Draft:
        session = db or self.session

        draft = session.query(Draft).filter(Draft.draft_id == draft_id).first()
        if not draft:
            raise DraftNotFoundError("Draft not found")

        league = (
            session.query(League).filter(League.league_id == draft.league_id).first()
        )
        if not league or str(league.commissioner_id) != str(commissioner_id):
            raise DraftServiceError("Only commissioner can start draft")

        if draft.status != DraftStatus.SCHEDULED.value:
            raise InvalidDraftStateError(
                f"Cannot start draft with status {draft.status}"
            )

        draft.status = DraftStatus.ACTIVE.value
        draft.started_at = datetime.utcnow()
        draft.current_pick = 1
        draft.current_round = 1
        if draft.draft_order:
            draft.current_team_id = _uuid.UUID(draft.draft_order[0])

        if league.can_transition_to("drafting"):
            league.status = "drafting"

        session.commit()

        asyncio.create_task(self._start_pick_timer(str(draft.draft_id)))
        self._notify_current_pick(draft, session)
        logger.info("Draft started", extra={"draft_id": str(draft.draft_id)})
        return draft

    def pause_draft(
        self,
        *,
        draft_id: str,
        commissioner_id: str,
        db: Session | None = None,
    ) -> Draft:
        session = db or self.session
        draft = session.query(Draft).filter(Draft.draft_id == draft_id).first()
        if not draft:
            raise DraftNotFoundError("Draft not found")

        league = (
            session.query(League).filter(League.league_id == draft.league_id).first()
        )
        if not league or str(league.commissioner_id) != str(commissioner_id):
            raise DraftServiceError("Only commissioner can pause draft")
        if draft.status != DraftStatus.ACTIVE.value:
            raise InvalidDraftStateError("Draft is not active")

        draft.status = DraftStatus.PAUSED.value
        session.commit()

        self._cancel_pick_timer(str(draft.draft_id))
        logger.info("Draft paused", extra={"draft_id": str(draft.draft_id)})
        return draft

    def resume_draft(
        self,
        *,
        draft_id: str,
        commissioner_id: str,
        db: Session | None = None,
    ) -> Draft:
        session = db or self.session
        draft = session.query(Draft).filter(Draft.draft_id == draft_id).first()
        if not draft:
            raise DraftNotFoundError("Draft not found")

        league = (
            session.query(League).filter(League.league_id == draft.league_id).first()
        )
        if not league or str(league.commissioner_id) != str(commissioner_id):
            raise DraftServiceError("Only commissioner can resume draft")
        if draft.status != DraftStatus.PAUSED.value:
            raise InvalidDraftStateError("Draft is not paused")

        draft.status = DraftStatus.ACTIVE.value
        session.commit()

        asyncio.create_task(self._start_pick_timer(str(draft.draft_id)))
        logger.info("Draft resumed", extra={"draft_id": str(draft.draft_id)})
        return draft

    def get_draft(self, draft_id: str, db: Session | None = None) -> Draft | None:
        session = db or self.session
        return session.query(Draft).filter(Draft.draft_id == draft_id).first()

    def get_draft_by_league(
        self, league_id: str, db: Session | None = None
    ) -> Draft | None:
        session = db or self.session
        return session.query(Draft).filter(Draft.league_id == league_id).first()

    # ------------------------------------------------------------------
    # Picks
    # ------------------------------------------------------------------
    def make_pick(
        self,
        *,
        draft_id: str,
        team_id: str,
        player_id: str,
        user_id: str,
        is_autopick: bool = False,
        db: Session | None = None,
    ) -> DraftPick:
        session = db or self.session

        draft = session.query(Draft).filter(Draft.draft_id == draft_id).first()
        if not draft:
            raise DraftNotFoundError("Draft not found")
        if draft.status != DraftStatus.ACTIVE.value:
            raise InvalidDraftStateError("Draft is not active")

        current_team_id = str(draft.current_team_id) if draft.current_team_id else None
        if current_team_id != str(team_id):
            raise DraftServiceError("It's not your turn to pick")

        team = session.query(Team).filter(Team.team_id == team_id).first()
        if not team:
            raise DraftServiceError("Team not found")
        if not is_autopick and str(team.user_id) != str(user_id):
            raise DraftServiceError("User doesn't own this team")

        player = session.query(Player).filter(Player.player_id == player_id).first()
        if not player:
            raise DraftServiceError("Player not found")
        if self._is_player_drafted(draft_id, player_id, session):
            raise DraftServiceError("Player already drafted")

        self._validate_roster_limits(team_id, player, session)

        pick_number = draft.current_pick
        pick_data = {
            "pick_number": pick_number,
            "round_number": self._calculate_round_number(pick_number, session, draft),
            "team_id": str(team_id),
            "player_id": str(player_id),
            "pick_time": datetime.utcnow().isoformat(),
            "is_autopick": is_autopick,
        }

        picks = draft.picks or []
        picks.append(pick_data)
        draft.picks = picks

        team.add_player_to_roster(str(player_id))
        self._advance_to_next_pick(draft, session)
        session.commit()

        self._cancel_pick_timer(str(draft.draft_id))
        if draft.status == DraftStatus.ACTIVE.value:
            asyncio.create_task(self._start_pick_timer(str(draft.draft_id)))
            self._notify_current_pick(draft, session)

        logger.info(
            "Pick made",
            extra={
                "draft_id": str(draft.draft_id),
                "team_id": str(team_id),
                "player_id": str(player_id),
                "autopick": is_autopick,
            },
        )

        return DraftPick(
            pick_number=pick_number,
            round_number=pick_data["round_number"],
            team_id=str(team_id),
            player_id=str(player_id),
            pick_time=datetime.fromisoformat(pick_data["pick_time"]),
            is_autopick=is_autopick,
        )

    def make_autopick(
        self,
        *,
        draft_id: str,
        team_id: str,
        db: Session | None = None,
    ) -> DraftPick:
        session = db or self.session
        available_players = self.get_available_players(draft_id, limit=50, db=session)
        if not available_players:
            raise DraftServiceError("No players available for auto-pick")

        selection = available_players[0]
        return self.make_pick(
            draft_id=draft_id,
            team_id=team_id,
            player_id=selection["player_id"],
            user_id="system",
            is_autopick=True,
            db=session,
        )

    # ------------------------------------------------------------------
    # Queries
    # ------------------------------------------------------------------
    def get_draft_board(
        self,
        draft_id: str,
        db: Session | None = None,
    ) -> dict[str, Any]:
        session = db or self.session
        draft = session.query(Draft).filter(Draft.draft_id == draft_id).first()
        if not draft:
            raise DraftNotFoundError("Draft not found")

        league = (
            session.query(League).filter(League.league_id == draft.league_id).first()
        )
        teams = (
            session.query(Team)
            .filter(Team.league_id == draft.league_id)
            .order_by(Team.created_at)
            .all()
        )

        draft_order = self._get_draft_order(draft, teams)
        total_rounds = self._calculate_total_rounds(league, teams)
        total_picks = len(teams) * total_rounds

        picks_with_players: list[dict[str, Any]] = []
        for pick in draft.picks or []:
            player = (
                session.query(Player)
                .filter(Player.player_id == pick["player_id"])
                .first()
            )
            team = session.query(Team).filter(Team.team_id == pick["team_id"]).first()
            picks_with_players.append(
                {
                    "pick_number": pick["pick_number"],
                    "round_number": pick["round_number"],
                    "team": (
                        {
                            "team_id": str(team.team_id),
                            "name": (
                                team.team_name
                                if hasattr(team, "team_name")
                                else team.name
                            ),
                            "user_id": str(team.user_id),
                        }
                        if team
                        else None
                    ),
                    "player": (
                        {
                            "player_id": str(player.player_id),
                            "name": player.name,
                            "position": player.position,
                            "team_id": player.team_id,
                        }
                        if player
                        else None
                    ),
                    "pick_time": pick.get("pick_time"),
                    "is_autopick": pick.get("is_autopick", False),
                }
            )

        current_pick_info: dict[str, Any] | None = None
        if (
            draft.status == DraftStatus.ACTIVE.value
            and draft.current_pick <= total_picks
        ):
            current_team = None
            if draft.current_team_id:
                current_team = (
                    session.query(Team)
                    .filter(Team.team_id == draft.current_team_id)
                    .first()
                )
            if current_team:
                current_pick_info = {
                    "pick_number": draft.current_pick,
                    "round_number": self._calculate_round_number(
                        draft.current_pick, session, draft
                    ),
                    "team": {
                        "team_id": str(current_team.team_id),
                        "name": (
                            current_team.team_name
                            if hasattr(current_team, "team_name")
                            else current_team.name
                        ),
                        "user_id": str(current_team.user_id),
                    },
                    "time_remaining": self._get_time_remaining(str(draft.draft_id)),
                }

        return {
            "draft": {
                "draft_id": str(draft.draft_id),
                "league_id": str(draft.league_id),
                "status": draft.status,
                "draft_type": draft.draft_type,
                "rounds": draft.rounds,
                "pick_timer_seconds": draft.pick_timer,
                "current_pick": draft.current_pick,
                "total_picks": total_picks,
                "total_rounds": total_rounds,
                "started_at": (
                    draft.started_at.isoformat() if draft.started_at else None
                ),
            },
            "teams": [
                {
                    "team_id": str(team.team_id),
                    "name": team.team_name if hasattr(team, "team_name") else team.name,
                    "user_id": str(team.user_id),
                    "draft_position": draft_order.index(str(team.team_id)) + 1,
                }
                for team in teams
            ],
            "picks": picks_with_players,
            "current_pick": current_pick_info,
            "draft_order": draft_order,
        }

    def get_available_players(
        self,
        draft_id: str,
        position: str | None = None,
        limit: int = 100,
        offset: int = 0,
        db: Session | None = None,
    ) -> list[dict[str, Any]]:
        session = db or self.session
        draft = session.query(Draft).filter(Draft.draft_id == draft_id).first()
        if not draft:
            raise DraftNotFoundError("Draft not found")

        drafted_ids = {pick.get("player_id") for pick in (draft.picks or [])}
        query = session.query(Player)
        if position:
            query = query.filter(Player.position == position)
        if drafted_ids:
            query = query.filter(Player.player_id.notin_(drafted_ids))

        players = query.order_by(Player.name).offset(offset).limit(limit).all()

        results: list[dict[str, Any]] = []
        for player in players:
            results.append(
                {
                    "player_id": str(player.player_id),
                    "name": player.name,
                    "position": player.position,
                    "team_id": player.team_id,
                    "injury_status": player.injury_status,
                    "projections": player.projections,
                }
            )
        return results

    def enable_autodraft_for_team(
        self,
        draft_id: str,
        team_id: str,
        user_id: str,
        db: Session | None = None,
    ) -> None:
        logger.info(
            "Auto-draft enabled",
            extra={"draft_id": draft_id, "team_id": team_id, "user_id": user_id},
        )

    def get_draft_summary(
        self,
        draft_id: str,
        db: Session | None = None,
    ) -> dict[str, Any]:
        session = db or self.session
        draft = session.query(Draft).filter(Draft.draft_id == draft_id).first()
        if not draft:
            raise DraftNotFoundError("Draft not found")

        league = (
            session.query(League).filter(League.league_id == draft.league_id).first()
        )
        teams = session.query(Team).filter(Team.league_id == draft.league_id).all()

        total_picks = len(draft.picks or [])
        autopicks = sum(
            1 for pick in (draft.picks or []) if pick.get("is_autopick", False)
        )

        duration_minutes = None
        if draft.started_at and draft.completed_at:
            duration_minutes = (
                draft.completed_at - draft.started_at
            ).total_seconds() / 60.0

        return {
            "draft_id": str(draft.draft_id),
            "league_name": league.name if league else None,
            "status": draft.status,
            "total_teams": len(teams),
            "total_picks": total_picks,
            "autopick_count": autopicks,
            "manual_pick_count": total_picks - autopicks,
            "started_at": draft.started_at.isoformat() if draft.started_at else None,
            "completed_at": (
                draft.completed_at.isoformat() if draft.completed_at else None
            ),
            "duration_minutes": duration_minutes,
            "current_pick": (
                draft.current_pick if draft.status == DraftStatus.ACTIVE.value else None
            ),
        }

    # ------------------------------------------------------------------
    # Timer coordination
    # ------------------------------------------------------------------
    async def _start_pick_timer(self, draft_id: str) -> None:
        self._cancel_pick_timer(draft_id)
        task = asyncio.create_task(self._pick_timer_countdown(draft_id))
        self.active_timers[draft_id] = task
        try:
            await task
        except asyncio.CancelledError:
            logger.debug("Pick timer cancelled", extra={"draft_id": draft_id})

    async def _pick_timer_countdown(self, draft_id: str) -> None:
        session_factory = get_session_factory()
        with session_factory.get_sync_session() as session:
            draft = session.query(Draft).filter(Draft.draft_id == draft_id).first()
            if not draft or draft.status != DraftStatus.ACTIVE.value:
                return

            time_remaining = draft.pick_timer
            while time_remaining > 0:
                await asyncio.sleep(1)
                time_remaining -= 1
                self._notify_timer_callbacks(draft_id, time_remaining)
                session.refresh(draft)
                if draft.status != DraftStatus.ACTIVE.value:
                    return

            try:
                self.make_autopick(
                    draft_id=draft_id, team_id=str(draft.current_team_id), db=session
                )
            except Exception as exc:  # pragma: no cover - defensive logging
                logger.error(
                    "Auto-pick failed",
                    extra={"draft_id": draft_id, "error": str(exc)},
                )

    def _cancel_pick_timer(self, draft_id: str) -> None:
        task = self.active_timers.pop(draft_id, None)
        if task:
            task.cancel()

    def _get_time_remaining(self, draft_id: str) -> int:
        # TODO: track per-draft countdown accurately
        return 60

    def register_timer_callback(
        self, draft_id: str, callback: Callable[[int], None]
    ) -> None:
        callbacks = self.timer_callbacks.setdefault(draft_id, [])
        callbacks.append(callback)

    def _notify_timer_callbacks(self, draft_id: str, time_remaining: int) -> None:
        for callback in self.timer_callbacks.get(draft_id, []):
            try:
                callback(time_remaining)
            except Exception as exc:  # pragma: no cover - defensive
                logger.error("Timer callback error", extra={"error": str(exc)})

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _generate_draft_order(self, teams: list[Team]) -> list[str]:
        team_ids = [str(team.team_id) for team in teams]
        random.shuffle(team_ids)
        return team_ids

    def _get_draft_order(self, draft: Draft, teams: list[Team]) -> list[str]:
        if draft.draft_order:
            return list(draft.draft_order)
        return [str(team.team_id) for team in teams]

    def _calculate_round_number(
        self, pick_number: int, session: Session, draft: Draft
    ) -> int:
        team_count = (
            session.query(Team).filter(Team.league_id == draft.league_id).count()
        )
        if team_count == 0:
            return 1
        return ((pick_number - 1) // team_count) + 1

    def _calculate_total_rounds(self, league: League | None, teams: list[Team]) -> int:
        roster_settings = (league.roster_settings if league else {}) or {}
        starting_positions = roster_settings.get("starting_positions", [])
        bench_spots = roster_settings.get("bench_spots", 5)
        return len(starting_positions) + bench_spots

    def _advance_to_next_pick(self, draft: Draft, session: Session) -> None:
        teams = (
            session.query(Team)
            .filter(Team.league_id == draft.league_id)
            .order_by(Team.created_at)
            .all()
        )
        if not teams:
            draft.status = DraftStatus.COMPLETED.value
            draft.completed_at = datetime.utcnow()
            draft.current_team_id = None
            return

        league = (
            session.query(League).filter(League.league_id == draft.league_id).first()
        )
        total_rounds = draft.rounds or self._calculate_total_rounds(league, teams)
        total_picks = len(teams) * total_rounds

        if draft.current_pick >= total_picks:
            draft.status = DraftStatus.COMPLETED.value
            draft.completed_at = datetime.utcnow()
            draft.current_team_id = None
            if league and league.can_transition_to("active"):
                league.status = "active"
            return

        draft.current_pick += 1
        draft.current_round = self._calculate_round_number(
            draft.current_pick, session, draft
        )

        draft_order = self._get_draft_order(draft, teams)
        team_count = len(draft_order)
        pick_in_round = (draft.current_pick - 1) % team_count

        if draft.draft_type == DraftType.SNAKE.value and draft.current_round % 2 == 0:
            team_index = team_count - 1 - pick_in_round
        else:
            team_index = pick_in_round

        draft.current_team_id = _uuid.UUID(draft_order[team_index])

    def _is_player_drafted(
        self, draft_id: str, player_id: str, session: Session
    ) -> bool:
        draft = session.query(Draft).filter(Draft.draft_id == draft_id).first()
        if not draft or not draft.picks:
            return False
        return any(pick.get("player_id") == str(player_id) for pick in draft.picks)

    def _validate_roster_limits(
        self, team_id: str, player: Player, session: Session
    ) -> None:
        team = session.query(Team).filter(Team.team_id == team_id).first()
        league = (
            session.query(League).filter(League.league_id == team.league_id).first()
        )

        roster_settings = league.roster_settings or {}
        max_per_position = roster_settings.get("max_per_position", {})
        if player.position not in max_per_position:
            return

        current_count = 0
        for roster_player_id in team.roster or []:
            roster_player = (
                session.query(Player)
                .filter(Player.player_id == roster_player_id)
                .first()
            )
            if roster_player and roster_player.position == player.position:
                current_count += 1

        if current_count >= max_per_position[player.position]:
            raise DraftServiceError(
                f"Team has reached maximum {player.position} players"
            )

    def _notify_current_pick(self, draft: Draft, session: Session) -> None:
        if not draft.current_team_id:
            return

        team = session.query(Team).filter(Team.team_id == draft.current_team_id).first()
        if not team:
            return

        notification = Notification.create_draft_notification(
            user_id=str(team.user_id),
            league_id=str(draft.league_id),
            team_id=str(team.team_id),
            pick_number=draft.current_pick,
            time_remaining=draft.pick_timer,
        )
        session.add(notification)
        session.commit()


__all__ = [
    "DraftNotFoundError",
    "DraftPick",
    "DraftService",
    "DraftServiceError",
    "DraftSettings",
    "InvalidDraftStateError",
    "PickTimerExpiredError",
]
