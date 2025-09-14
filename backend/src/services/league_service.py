from __future__ import annotations

import uuid as _uuid

from sqlalchemy.orm import Session

from models.league import League
from models.team import Team
from models.user import User


class LeagueService:
    def __init__(self, session: Session) -> None:
        self.session = session

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
                email=f"{commissioner_id}@example.com",
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

        return league

    def join(
        self,
        *,
        user_id: _uuid.UUID,
        league_id: _uuid.UUID,
        team_name: str | None = None,
    ) -> Team:
        # Ensure user exists
        user = self.session.query(User).filter(User.user_id == user_id).one_or_none()
        if not user:
            user = User(
                user_id=user_id,
                email=f"{user_id}@example.com",
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
        return team

    # Read helpers for UI lists
    def list_by_user(self, *, user_id: _uuid.UUID) -> list[dict]:
        from models.team import Team

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
        from models.team import Team

        q = self.session.query(Team).filter(Team.league_id == league_id)
        return [
            {
                "team_id": str(t.team_id),
                "user_id": str(t.user_id),
                "team_name": t.team_name,
            }
            for t in q.all()
        ]
