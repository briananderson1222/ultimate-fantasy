from __future__ import annotations

import logging
import secrets
import string
import uuid as _uuid
from typing import Any, Dict, List, Optional

from sqlalchemy import and_, desc, func, or_
from sqlalchemy.orm import Session

from domains.leagues.models.league import League
from domains.leagues.models.team import Team
from domains.shared.exceptions import (
    AlreadyInLeagueError,
    CommissionerOnlyError,
    InsufficientPermissionsError,
    InvalidInviteCodeError,
    LeagueError,
    LeagueFullError,
    LeagueNotFoundError,
    LeagueValidationError,
    UserNotFoundError,
)
from domains.shared.events.publisher import DomainEventPublisher
from domains.shared.interfaces.league_service import LeagueServiceInterface
from domains.users.models.user import User
from infrastructure.events.dispatcher import get_event_dispatcher
logger = logging.getLogger(__name__)


class LeagueService(LeagueServiceInterface):
    """Domain league service implementing full league lifecycle operations."""

    def __init__(self, session: Session) -> None:
        self.session = session
        self.invite_code_length = 8
        self.max_leagues_per_commissioner = 10
        self.max_teams_per_user_per_league = 1

        try:
            dispatcher = get_event_dispatcher()
            self.event_publisher: DomainEventPublisher | None = DomainEventPublisher(
                dispatcher, "leagues"
            )
        except RuntimeError:
            self.event_publisher = None

    # ------------------------------------------------------------------
    # Creation & Updates
    # ------------------------------------------------------------------
    def create_league(
        self,
        *,
        commissioner_id: str,
        name: str,
        sport: str,
        league_type: str,
        season: str,
        max_teams: int = 12,
        custom_settings: Optional[Dict[str, Any]] = None,
        db: Optional[Session] = None,
    ) -> League:
        session = db or self.session
        commissioner_uuid = _uuid.UUID(str(commissioner_id))

        commissioner = (
            session.query(User)
            .filter(User.user_id == commissioner_uuid)
            .one_or_none()
        )
        if not commissioner:
            default_username = f"user_{str(commissioner_uuid)[:8]}"
            commissioner = User(
                user_id=commissioner_uuid,
                username=default_username,
                email=f"{commissioner_uuid}@ultimatefantasy.app",
                display_name=f"User {str(commissioner_uuid)[:8]}",
                password_hash="",
            )
            session.add(commissioner)
            session.flush()

        league_count = (
            session.query(League)
            .filter(League.commissioner_id == commissioner_uuid)
            .count()
        )
        if league_count >= self.max_leagues_per_commissioner:
            raise LeagueValidationError(
                f"Commissioner already manages {self.max_leagues_per_commissioner} leagues"
            )

        invite_code = self._generate_invite_code(session)

        league = League(
            name=name,
            sport=sport,
            league_type=league_type,
            season=season,
            commissioner_id=commissioner_uuid,
            max_teams=max_teams,
            invite_code=invite_code,
        )
        league.scoring_rules = self._get_default_scoring_rules(
            sport, custom_settings
        )
        league.roster_settings = self._get_default_roster_settings(
            sport, custom_settings
        )
        league.draft_settings = self._get_default_draft_settings(custom_settings)
        league.waiver_settings = self._get_default_waiver_settings(custom_settings)
        league.trade_settings = self._get_default_trade_settings(custom_settings)
        league.playoff_settings = self._get_default_playoff_settings(custom_settings)

        session.add(league)
        session.flush()

        team = Team(
            league_id=league.league_id,
            user_id=commissioner_uuid,
            team_name=f"{commissioner.display_name or commissioner.username}'s Team",
            wins=0,
            losses=0,
            ties=0,
            points_for=0.0,
            points_against=0.0,
            waiver_priority=1,
            faab_budget=100,
            roster=[],
        )
        session.add(team)
        session.flush()
        session.commit()

        logger.info("League created", extra={"league_id": str(league.league_id)})
        self._publish_event(
            "league_created",
            str(league.league_id),
            {
                "league_id": str(league.league_id),
                "name": league.name,
                "sport": league.sport,
                "league_type": league.league_type,
                "season": league.season,
                "commissioner_id": str(commissioner_uuid),
                "commissioner_team_id": str(team.team_id),
            },
        )
        return league

    def create(
        self,
        *,
        commissioner_id: _uuid.UUID,
        name: str,
        sport: str,
        league_type: str,
        season: str,
        max_teams: int = 12,
    ) -> League:
        return self.create_league(
            commissioner_id=str(commissioner_id),
            name=name,
            sport=sport,
            league_type=league_type,
            season=season,
            max_teams=max_teams,
        )

    def update_league_settings(
        self,
        *,
        league_id: str,
        user_id: str,
        updates: Dict[str, Any],
        db: Optional[Session] = None,
    ) -> League:
        session = db or self.session
        league = self.get_league(league_id, session)

        if str(league.commissioner_id) != str(user_id):
            raise InsufficientPermissionsError("Only commissioner can update settings")

        if league.status != "setup":
            raise LeagueValidationError("Settings can only be updated during setup phase")

        allowed_fields = {
            "name",
            "max_teams",
            "scoring_rules",
            "roster_settings",
            "draft_settings",
            "waiver_settings",
            "trade_settings",
            "playoff_settings",
        }

        for field, value in updates.items():
            if field in allowed_fields:
                setattr(league, field, value)

        session.commit()
        logger.info("League settings updated", extra={"league_id": str(league.league_id)})
        return league

    def delete_league(
        self,
        *,
        league_id: str,
        user_id: str,
        db: Optional[Session] = None,
    ) -> None:
        session = db or self.session
        league = self.get_league(league_id, session)
        if str(league.commissioner_id) != str(user_id):
            raise InsufficientPermissionsError("Only commissioner can delete league")

        session.query(Team).filter(Team.league_id == league.league_id).delete()
        session.delete(league)
        session.commit()
        logger.info("League deleted", extra={"league_id": league_id})

    def transition_league_status(
        self,
        *,
        league_id: str,
        user_id: str,
        new_status: str,
        db: Optional[Session] = None,
    ) -> League:
        session = db or self.session
        league = self.get_league(league_id, session)
        if str(league.commissioner_id) != str(user_id):
            raise InsufficientPermissionsError("Only commissioner can change status")
        if not league.can_transition_to(new_status):
            raise LeagueValidationError(
                f"Cannot transition from {league.status} to {new_status}"
            )
        league.status = new_status
        session.commit()
        return league

    # ------------------------------------------------------------------
    # Queries
    # ------------------------------------------------------------------
    def get_league(self, league_id: str, db: Optional[Session] = None) -> League:
        session = db or self.session
        league_uuid = _uuid.UUID(str(league_id))
        league = (
            session.query(League)
            .filter(League.league_id == league_uuid)
            .one_or_none()
        )
        if not league:
            raise LeagueNotFoundError("League not found")
        return league

    def get_league_by_invite_code(
        self, invite_code: str, db: Optional[Session] = None
    ) -> League:
        session = db or self.session
        league = (
            session.query(League)
            .filter(League.invite_code == invite_code)
            .one_or_none()
        )
        if not league:
            raise InvalidInviteCodeError("Invalid invite code")
        return league

    def get_user_leagues(
        self,
        *,
        user_id: str,
        sport: Optional[str] = None,
        status: Optional[str] = None,
        db: Optional[Session] = None,
    ) -> List[League]:
        session = db or self.session
        user_uuid = _uuid.UUID(str(user_id))

        query = (
            session.query(League)
            .join(Team, Team.league_id == League.league_id)
            .filter(Team.user_id == user_uuid)
        )
        if sport:
            query = query.filter(League.sport == sport)
        if status:
            query = query.filter(League.status == status)

        return query.order_by(League.created_at.desc()).all()

    def get_public_leagues(
        self,
        *,
        sport: Optional[str] = None,
        league_type: Optional[str] = None,
        limit: int = 20,
        offset: int = 0,
        db: Optional[Session] = None,
    ) -> List[League]:
        session = db or self.session
        query = session.query(League).filter(League.status == "recruiting")
        if sport:
            query = query.filter(League.sport == sport)
        if league_type:
            query = query.filter(League.league_type == league_type)
        return (
            query.order_by(League.created_at.desc())
            .offset(offset)
            .limit(limit)
            .all()
        )

    def list_by_user(
        self, *, user_id: _uuid.UUID, db: Optional[Session] = None
    ) -> List[Dict[str, Any]]:
        session = db or self.session
        results = (
            session.query(Team, League)
            .join(League, League.league_id == Team.league_id)
            .filter(Team.user_id == user_id)
            .all()
        )
        items: List[Dict[str, Any]] = []
        for team, league in results:
            items.append(
                {
                    "league_id": str(league.league_id),
                    "name": league.name,
                    "season": league.season,
                    "team_id": str(team.team_id),
                }
            )
        return items

    def list_league_members(
        self, *, league_id: str, db: Optional[Session] = None
    ) -> List[User]:
        session = db or self.session
        league_uuid = _uuid.UUID(str(league_id))
        teams = (
            session.query(Team)
            .filter(Team.league_id == league_uuid)
            .all()
        )
        user_ids = [team.user_id for team in teams]
        if not user_ids:
            return []
        return (
            session.query(User)
            .filter(User.user_id.in_(user_ids))
            .all()
        )

    def get_league_members(
        self, *, league_id: str, db: Optional[Session] = None
    ) -> List[User]:
        return self.list_league_members(league_id=league_id, db=db)

    def get_league_teams(
        self, *, league_id: str, db: Optional[Session] = None
    ) -> List[Team]:
        session = db or self.session
        league_uuid = _uuid.UUID(str(league_id))
        return (
            session.query(Team)
            .filter(Team.league_id == league_uuid)
            .order_by(Team.waiver_priority)
            .all()
        )

    def list_members(
        self, *, league_id: _uuid.UUID, db: Optional[Session] = None
    ) -> List[Dict[str, str]]:
        session = db or self.session
        teams = (
            session.query(Team)
            .filter(Team.league_id == league_id)
            .all()
        )
        items: List[Dict[str, str]] = []
        for team in teams:
            items.append(
                {
                    "team_id": str(team.team_id),
                    "user_id": str(team.user_id),
                    "team_name": team.team_name,
                }
            )
        return items

    # ------------------------------------------------------------------
    # Membership & Teams
    # ------------------------------------------------------------------
    def join_league(
        self,
        *,
        user_id: str,
        invite_code: Optional[str] = None,
        league_id: Optional[str] = None,
        team_name: Optional[str] = None,
        db: Optional[Session] = None,
    ) -> Team:
        session = db or self.session
        if invite_code:
            league = self.get_league_by_invite_code(invite_code, session)
        elif league_id:
            league = self.get_league(league_id, session)
        else:
            raise LeagueValidationError("Invite code or league_id required")
        try:
            user = self._get_user(_uuid.UUID(str(user_id)), session)
        except UserNotFoundError:
            default_username = f"user_{str(user_id)[:8]}"
            user = User(
                user_id=_uuid.UUID(str(user_id)),
                username=default_username,
                email=f"{user_id}@ultimatefantasy.app",
                display_name=f"User {str(user_id)[:8]}",
                password_hash="",
            )
            session.add(user)
            session.flush()

        if league.status not in {"setup", "drafting"}:
            raise LeagueValidationError("League is not accepting new members")

        existing_team = (
            session.query(Team)
            .filter(Team.league_id == league.league_id, Team.user_id == user.user_id)
            .one_or_none()
        )
        if existing_team:
            raise AlreadyInLeagueError("User already has team in league")

        current_team_count = (
            session.query(Team)
            .filter(Team.league_id == league.league_id)
            .count()
        )
        if league.is_full(current_team_count):
            raise LeagueFullError("League is full")

        resolved_name = team_name or f"{user.display_name or user.username}'s Team"
        duplicate = (
            session.query(Team)
            .filter(
                Team.league_id == league.league_id,
                Team.team_name == resolved_name,
            )
            .one_or_none()
        )
        if duplicate:
            resolved_name = f"{resolved_name} ({user.username})"

        max_priority = (
            session.query(func.max(Team.waiver_priority))
            .filter(Team.league_id == league.league_id)
            .scalar()
        ) or 0

        team = Team(
            league_id=league.league_id,
            user_id=user.user_id,
            team_name=resolved_name,
            waiver_priority=max_priority + 1,
            roster=[],
        )
        session.add(team)
        session.flush()
        session.commit()

        self._publish_event(
            "user_joined_league",
            str(league.league_id),
            {
                "league_id": str(league.league_id),
                "user_id": str(user.user_id),
                "team_id": str(team.team_id),
                "team_name": team.team_name,
            },
        )
        return team

    def join(
        self,
        *,
        user_id: _uuid.UUID,
        league_id: _uuid.UUID,
        team_name: Optional[str] = None,
    ) -> Team:
        return self.join_league(
            user_id=str(user_id), league_id=str(league_id), team_name=team_name
        )

    def leave_league(
        self,
        *,
        league_id: str,
        user_id: str,
        db: Optional[Session] = None,
    ) -> None:
        session = db or self.session
        league = self.get_league(league_id, session)
        user_uuid = _uuid.UUID(str(user_id))

        if league.status != "setup":
            raise LeagueValidationError("Cannot leave league after draft starts")
        if league.commissioner_id == user_uuid:
            raise LeagueValidationError("Commissioner cannot leave their league")

        team = (
            session.query(Team)
            .filter(Team.league_id == league.league_id, Team.user_id == user_uuid)
            .one_or_none()
        )
        if not team:
            raise AlreadyInLeagueError("User is not in this league")

        session.delete(team)
        session.commit()

    def remove_member(
        self,
        *,
        league_id: str,
        requester_id: str,
        user_id: str,
        db: Optional[Session] = None,
    ) -> None:
        session = db or self.session
        league = self.get_league(league_id, session)
        if str(league.commissioner_id) != str(requester_id):
            raise CommissionerOnlyError("Only commissioners can remove members")
        if league.status != "setup":
            raise LeagueValidationError("Cannot remove members after draft starts")

        team = (
            session.query(Team)
            .filter(
                Team.league_id == league.league_id,
                Team.user_id == _uuid.UUID(str(user_id)),
            )
            .one_or_none()
        )
        if not team:
            raise UserNotFoundError("User not found in league")

        session.delete(team)
        session.commit()

    def update_team(
        self,
        *,
        team_id: str,
        updates: Dict[str, Any],
        db: Optional[Session] = None,
    ) -> Team:
        session = db or self.session
        team = (
            session.query(Team)
            .filter(Team.team_id == _uuid.UUID(str(team_id)))
            .one_or_none()
        )
        if not team:
            raise UserNotFoundError("Team not found")

        allowed_fields = {"team_name", "logo_url", "waiver_priority"}
        for field, value in updates.items():
            if field in allowed_fields:
                setattr(team, field, value)
        session.commit()
        return team

    def get_user_team_in_league(
        self,
        *,
        league_id: str,
        user_id: str,
        db: Optional[Session] = None,
    ) -> Team:
        session = db or self.session
        team = (
            session.query(Team)
            .filter(
                Team.league_id == _uuid.UUID(str(league_id)),
                Team.user_id == _uuid.UUID(str(user_id)),
            )
            .one_or_none()
        )
        if not team:
            raise UserNotFoundError("Team not found in league")
        return team

    # ------------------------------------------------------------------
    # Commissioner utilities
    # ------------------------------------------------------------------
    def is_commissioner(
        self, *, league_id: str, user_id: str, db: Optional[Session] = None
    ) -> bool:
        league = self.get_league(league_id, db)
        return str(league.commissioner_id) == str(user_id)

    def is_user_in_league(
        self, *, league_id: str, user_id: str, db: Optional[Session] = None
    ) -> bool:
        session = db or self.session
        return (
            session.query(Team)
            .filter(
                Team.league_id == _uuid.UUID(str(league_id)),
                Team.user_id == _uuid.UUID(str(user_id)),
            )
            .count()
            > 0
        )

    def transfer_commissioner(
        self,
        *,
        league_id: str,
        current_commissioner_id: str,
        new_commissioner_user_id: str,
        db: Optional[Session] = None,
    ) -> None:
        session = db or self.session
        league = self.get_league(league_id, session)
        if str(league.commissioner_id) != str(current_commissioner_id):
            raise CommissionerOnlyError("Only current commissioner can transfer role")

        new_commissioner = self._get_user(
            _uuid.UUID(str(new_commissioner_user_id)), session
        )
        if not self.is_user_in_league(
            league_id=league_id, user_id=new_commissioner_user_id, db=session
        ):
            raise UserNotFoundError("New commissioner must be in league")

        league.commissioner_id = new_commissioner.user_id
        session.commit()

    def regenerate_invite_code(
        self,
        *,
        league_id: str,
        user_id: str,
        db: Optional[Session] = None,
    ) -> str:
        session = db or self.session
        league = self.get_league(league_id, session)
        if str(league.commissioner_id) != str(user_id):
            raise CommissionerOnlyError("Only commissioner can regenerate invite code")

        league.invite_code = self._generate_invite_code(session)
        session.commit()
        return league.invite_code

    def get_league_standings(
        self, *, league_id: str, db: Optional[Session] = None
    ) -> Dict[str, Any]:
        session = db or self.session
        league = self.get_league(league_id, session)
        teams = (
            session.query(Team)
            .filter(Team.league_id == league.league_id)
            .order_by(desc(Team.wins), desc(Team.points_for))
            .all()
        )
        standings = []
        for rank, team in enumerate(teams, start=1):
            standings.append(
                {
                    "rank": rank,
                    "team_id": str(team.team_id),
                    "team_name": team.team_name,
                    "wins": team.wins,
                    "losses": team.losses,
                    "ties": team.ties,
                    "points_for": float(team.points_for),
                    "points_against": float(team.points_against),
                }
            )
        return {
            "league_id": str(league.league_id),
            "season": league.season,
            "standings": standings,
        }

    # ------------------------------------------------------------------
    # Interface Implementations
    # ------------------------------------------------------------------
    async def get_league_members(self, league_id: str) -> List[User]:  # type: ignore[override]
        return self.list_league_members(league_id=league_id)

    async def validate_league_access(
        self, league_id: str, user_id: str
    ) -> bool:  # type: ignore[override]
        return self.is_user_in_league(league_id=league_id, user_id=user_id)

    async def get_league_settings(self, league_id: str) -> League:  # type: ignore[override]
        return self.get_league(league_id)

    async def get_league_by_id(self, league_id: str) -> League:  # type: ignore[override]
        return self.get_league(league_id)

    async def is_league_commissioner(
        self, league_id: str, user_id: str
    ) -> bool:  # type: ignore[override]
        return self.is_commissioner(league_id=league_id, user_id=user_id)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _generate_invite_code(self, session: Session) -> str:
        while True:
            code = "".join(
                secrets.choice(string.ascii_uppercase + string.digits)
                for _ in range(self.invite_code_length)
            )
            exists = (
                session.query(League)
                .filter(League.invite_code == code)
                .one_or_none()
            )
            if not exists:
                return code

    def _get_user(self, user_id: _uuid.UUID, session: Session) -> User:
        user = session.query(User).filter(User.user_id == user_id).one_or_none()
        if not user:
            raise UserNotFoundError("User not found")
        return user

    def _get_default_scoring_rules(
        self, sport: str, custom_settings: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        defaults: Dict[str, Any] = {
            "mlb": {
                "hitting": {
                    "hits": 1,
                    "doubles": 2,
                    "triples": 3,
                    "home_runs": 4,
                    "rbis": 1,
                    "runs": 1,
                    "stolen_bases": 2,
                    "walks": 1,
                    "strikeouts": -1,
                },
                "pitching": {
                    "wins": 5,
                    "saves": 5,
                    "innings_pitched": 1,
                    "strikeouts": 1,
                    "earned_runs": -1,
                    "hits_allowed": -0.5,
                    "walks_allowed": -0.5,
                },
            },
            "nfl": {
                "passing": {
                    "yards": 0.04,
                    "touchdowns": 4,
                    "interceptions": -2,
                },
                "rushing": {
                    "yards": 0.1,
                    "touchdowns": 6,
                },
                "receiving": {
                    "yards": 0.1,
                    "touchdowns": 6,
                    "receptions": 1,
                },
                "kicking": {
                    "field_goals": 3,
                    "extra_points": 1,
                },
                "defense": {
                    "touchdowns": 6,
                    "sacks": 1,
                    "interceptions": 2,
                },
            },
            "wnba": {
                "scoring": {
                    "points": 1,
                    "three_pointers": 1,
                },
                "rebounding": {
                    "rebounds": 1.2,
                },
                "playmaking": {
                    "assists": 1.5,
                    "steals": 2,
                    "blocks": 2,
                },
                "turnovers": {
                    "turnovers": -1,
                },
            },
        }
        rules = defaults.get(sport, defaults["nfl"]).copy()
        if custom_settings and "scoring_rules" in custom_settings:
            self._deep_merge_dict(rules, custom_settings["scoring_rules"])
        return rules

    def _get_default_roster_settings(
        self, sport: str, custom_settings: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        defaults: Dict[str, Any] = {
            "mlb": {
                "starting_positions": [
                    "C",
                    "1B",
                    "2B",
                    "3B",
                    "SS",
                    "OF",
                    "OF",
                    "OF",
                    "P",
                    "P",
                ],
                "bench_spots": 5,
                "ir_spots": 2,
                "total_roster_size": 17,
            },
            "nfl": {
                "starting_positions": [
                    "QB",
                    "RB",
                    "RB",
                    "WR",
                    "WR",
                    "TE",
                    "FLEX",
                    "K",
                    "DEF",
                ],
                "bench_spots": 6,
                "ir_spots": 1,
                "total_roster_size": 16,
            },
            "wnba": {
                "starting_positions": [
                    "PG",
                    "SG",
                    "SF",
                    "PF",
                    "C",
                    "FLEX",
                    "FLEX",
                ],
                "bench_spots": 5,
                "ir_spots": 1,
                "total_roster_size": 13,
            },
        }
        roster = defaults.get(sport, defaults["nfl"]).copy()
        if custom_settings and "roster_settings" in custom_settings:
            self._deep_merge_dict(roster, custom_settings["roster_settings"])
        return roster

    def _get_default_draft_settings(
        self, custom_settings: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        defaults = {
            "draft_type": "snake",
            "pick_timer_seconds": 90,
            "auto_draft_enabled": True,
            "draft_order": "random",
            "allow_draft_trades": False,
            "pause_on_disconnect": True,
        }
        if custom_settings and "draft_settings" in custom_settings:
            self._deep_merge_dict(defaults, custom_settings["draft_settings"])
        return defaults

    def _get_default_waiver_settings(
        self, custom_settings: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        defaults = {
            "waiver_type": "rolling",
            "waiver_period_hours": 24,
            "waiver_budget": 100,
            "minimum_bid": 1,
            "waiver_days": ["Wednesday", "Saturday"],
            "allow_same_day_drops": False,
            "waiver_priority_reset": "never",
        }
        if custom_settings and "waiver_settings" in custom_settings:
            self._deep_merge_dict(defaults, custom_settings["waiver_settings"])
        return defaults

    def _get_default_trade_settings(
        self, custom_settings: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        defaults = {
            "trade_deadline_week": 13,
            "trade_review_period_hours": 48,
            "commissioner_approval_required": False,
            "league_vote_enabled": False,
            "vote_threshold_percentage": 60,
            "allow_future_picks": True,
            "veto_threshold": 4,
            "trade_processing": "immediate",
        }
        if custom_settings and "trade_settings" in custom_settings:
            self._deep_merge_dict(defaults, custom_settings["trade_settings"])
        return defaults

    def _get_default_playoff_settings(
        self, custom_settings: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        defaults = {
            "playoff_teams": 6,
            "playoff_start_week": 15,
            "championship_week": 17,
            "playoff_seeding": "record",
            "consolation_bracket": True,
            "playoff_matchup_length": 1,
            "tiebreaker_rules": ["head_to_head", "points_for", "points_against"],
        }
        if custom_settings and "playoff_settings" in custom_settings:
            self._deep_merge_dict(defaults, custom_settings["playoff_settings"])
        return defaults

    def _deep_merge_dict(self, base: Dict[str, Any], override: Dict[str, Any]) -> None:
        for key, value in override.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                self._deep_merge_dict(base[key], value)
            else:
                base[key] = value

    def _publish_event(self, event: str, entity_id: str, payload: Dict[str, Any]) -> None:
        if not self.event_publisher:
            return
        import asyncio

        task = asyncio.create_task(
            self.event_publisher.publish_event(event, entity_id, payload)
        )
        task.add_done_callback(lambda t: t.exception())


__all__ = ["LeagueService"]
