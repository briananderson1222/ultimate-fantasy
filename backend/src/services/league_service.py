from __future__ import annotations

import uuid as _uuid

from sqlalchemy.orm import Session

from models.league import League
from models.team import Team


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

        return league

    def join(
        self,
        *,
        user_id: _uuid.UUID,
        league_id: _uuid.UUID,
        team_name: str | None = None,
    ) -> Team:
        team = Team(
            league_id=league_id,
            user_id=user_id,
            team_name=team_name or f"Team {str(user_id)[:8]}",
        )
        self.session.add(team)
        self.session.flush()
        return team
