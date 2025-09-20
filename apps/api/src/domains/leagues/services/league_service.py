from __future__ import annotations

import uuid as _uuid

from sqlalchemy.orm import Session

from domains.leagues.models.league import League
from domains.leagues.models.team import Team
from domains.shared.events.publisher import DomainEventPublisher
from domains.shared.interfaces.league_service import LeagueServiceInterface
from domains.users.models.user import User
from infrastructure.events.dispatcher import get_event_dispatcher


class LeagueService(LeagueServiceInterface):
    def __init__(self, session: Session) -> None:
        self.session = session

        # Initialize event publishing
        try:
            dispatcher = get_event_dispatcher()
            self.event_publisher: DomainEventPublisher | None = DomainEventPublisher(
                dispatcher, "leagues"
            )
        except RuntimeError:
            # Event dispatcher not initialized, disable events
            self.event_publisher = None

    def create(
        self,
        *,
        commissioner_id: _uuid.UUID,
        name: str,
        sport: str,
        league_type: str,
        season: str,
    ) -> League:
        # Ensure user exists
        user = (
            self.session.query(User)
            .filter(User.user_id == commissioner_id)
            .one_or_none()
        )
        if not user:
            user = User(
                user_id=commissioner_id,
                email=f"{commissioner_id}@ultimatefantasy.app",
                display_name=f"User {str(commissioner_id)[:8]}",
                cognito_sub=str(commissioner_id),
            )
            self.session.add(user)
            self.session.flush()

        league = League(
            name=name,
            sport=sport,
            league_type=league_type,
            season=season,
            commissioner_id=commissioner_id,
        )
        self.session.add(league)
        self.session.flush()

        # Create commissioner team placeholder
        team = Team(
            league_id=league.league_id,
            user_id=commissioner_id,
            team_name=f"{name} - {commissioner_id}",
        )
        self.session.add(team)
        self.session.flush()
        self.session.commit()

        # Publish league created event
        if self.event_publisher:
            try:
                import asyncio

                task = asyncio.create_task(
                    self.event_publisher.publish_event(
                        "league_created",
                        str(league.league_id),
                        {
                            "league_id": str(league.league_id),
                            "name": name,
                            "sport": sport,
                            "league_type": league_type,
                            "season": season,
                            "commissioner_id": str(commissioner_id),
                            "commissioner_team_id": str(team.team_id),
                        },
                    )
                )
                task.add_done_callback(lambda t: t.exception())

                # Also publish integration event for other domains
                task = asyncio.create_task(
                    self.event_publisher.publish_integration_event(
                        "league_created",
                        str(league.league_id),
                        {
                            "league_id": str(league.league_id),
                            "name": name,
                            "commissioner_id": str(commissioner_id),
                        },
                        target_domains=["users", "scoring", "waitlist"],
                    )
                )
                task.add_done_callback(lambda t: t.exception())
            except Exception as e:
                # Don't fail the operation if event publishing fails
                import logging

                logging.getLogger(__name__).debug(f"Event publishing failed: {e}")

        return league

    def join(
        self,
        *,
        user_id: _uuid.UUID,
        league_id: _uuid.UUID,
        team_name: str | None = None,
    ) -> Team:
        # Ensure league exists
        league = (
            self.session.query(League)
            .filter(League.league_id == league_id)
            .one_or_none()
        )
        if not league:
            raise ValueError(
                f"League with ID {league_id} not found."
            )  # Or a more specific exception

        # Ensure user exists
        user = self.session.query(User).filter(User.user_id == user_id).one_or_none()
        if not user:
            user = User(
                user_id=user_id,
                email=f"{user_id}@ultimatefantasy.app",
                display_name=f"User {str(user_id)[:8]}",
                cognito_sub=str(user_id),
            )
            self.session.add(user)
            self.session.flush()

        team = Team(
            league_id=league_id,
            user_id=user_id,
            team_name=team_name or f"Team {str(user_id)[:8]}",
        )
        self.session.add(team)
        self.session.flush()
        self.session.commit()

        # Publish team joined event
        if self.event_publisher:
            try:
                import asyncio

                task = asyncio.create_task(
                    self.event_publisher.publish_event(
                        "user_joined_league",
                        str(league_id),
                        {
                            "league_id": str(league_id),
                            "user_id": str(user_id),
                            "team_id": str(team.team_id),
                            "team_name": team.team_name,
                        },
                    )
                )
                task.add_done_callback(lambda t: t.exception())

                # Publish integration event for other domains
                task = asyncio.create_task(
                    self.event_publisher.publish_integration_event(
                        "user_joined_league",
                        str(league_id),
                        {
                            "league_id": str(league_id),
                            "user_id": str(user_id),
                            "team_id": str(team.team_id),
                        },
                        target_domains=["users", "lineups", "scoring"],
                    )
                )
                task.add_done_callback(lambda t: t.exception())
            except Exception as e:
                import logging

                logging.getLogger(__name__).debug(f"Event publishing failed: {e}")

        return team

    # Read helpers for UI lists
    def list_by_user(self, *, user_id: _uuid.UUID) -> list[dict]:
        from domains.leagues.models.team import Team

        q = (
            self.session.query(Team, League)
            .join(League, League.league_id == Team.league_id)
            .filter(Team.user_id == user_id)
        )
        items = []
        for team, league in q.all():
            items.append(
                {
                    "league_id": str(league.league_id),
                    "name": league.name,
                    "season": league.season,
                    "team_id": str(team.team_id),
                }
            )
        return items

    def list_members(self, *, league_id: _uuid.UUID) -> list[dict]:
        from domains.leagues.models.team import Team

        q = self.session.query(Team).filter(Team.league_id == league_id)
        return [
            {
                "team_id": str(t.team_id),
                "user_id": str(t.user_id),
                "team_name": t.team_name,
            }
            for t in q.all()
        ]

    # Interface implementation methods
    async def get_league_members(self, league_id: str) -> list[User]:
        """Get all members of a league."""
        league_uuid = _uuid.UUID(league_id)
        teams = self.session.query(Team).filter(Team.league_id == league_uuid).all()
        user_ids = [team.user_id for team in teams]
        users = self.session.query(User).filter(User.user_id.in_(user_ids)).all()
        return users

    async def validate_league_access(self, league_id: str, user_id: str) -> bool:
        """Validate if a user has access to a league."""
        league_uuid = _uuid.UUID(league_id)
        user_uuid = _uuid.UUID(user_id)

        # Check if user is a member of the league
        team = (
            self.session.query(Team)
            .filter(Team.league_id == league_uuid, Team.user_id == user_uuid)
            .first()
        )
        return team is not None

    async def get_league_settings(self, league_id: str) -> League:
        """Get league configuration and settings."""
        league_uuid = _uuid.UUID(league_id)
        league = (
            self.session.query(League).filter(League.league_id == league_uuid).first()
        )
        if not league:
            raise ValueError(f"League with ID {league_id} not found")
        return league

    async def get_league_by_id(self, league_id: str) -> League:
        """Get league entity by ID."""
        league_uuid = _uuid.UUID(league_id)
        league = (
            self.session.query(League).filter(League.league_id == league_uuid).first()
        )
        if not league:
            raise ValueError(f"League with ID {league_id} not found")
        return league

    async def is_league_commissioner(self, league_id: str, user_id: str) -> bool:
        """Check if user is the commissioner of a league."""
        league_uuid = _uuid.UUID(league_id)
        user_uuid = _uuid.UUID(user_id)

        league = (
            self.session.query(League).filter(League.league_id == league_uuid).first()
        )
        if not league:
            return False
        return league.commissioner_id == user_uuid
