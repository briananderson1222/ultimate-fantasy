from __future__ import annotations

import uuid

from sqlalchemy.orm import Session

from models.waiver import Waiver


class WaiverService:
    def __init__(self, session: Session) -> None:
        self.session = session

    def place_bid(
        self,
        *,
        league_id: str | uuid.UUID,
        team_id: str | uuid.UUID,
        player_id: str | uuid.UUID,
        bid: int,
    ) -> Waiver:
        league_uuid = uuid.UUID(league_id) if isinstance(league_id, str) else league_id
        team_uuid = uuid.UUID(team_id) if isinstance(team_id, str) else team_id
        player_uuid = uuid.UUID(player_id) if isinstance(player_id, str) else player_id

        waiver = Waiver(
            league_id=league_uuid, team_id=team_uuid, player_id=player_uuid, bid=bid
        )
        self.session.add(waiver)
        self.session.flush()
        return waiver

    def resolve(self, *, league_id: str | uuid.UUID) -> int:
        # TODO: implement resolution logic: highest bid wins, status updates
        return 0

    def list(
        self,
        *,
        league_id: str | uuid.UUID,
        team_id: str | uuid.UUID | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[Waiver]:
        league_uuid = uuid.UUID(league_id) if isinstance(league_id, str) else league_id
        q = self.session.query(Waiver).filter(Waiver.league_id == league_uuid)
        if team_id is not None:
            team_uuid = uuid.UUID(team_id) if isinstance(team_id, str) else team_id
            q = q.filter(Waiver.team_id == team_uuid)
        q = q.offset(max(0, offset)).limit(max(1, min(100, limit)))
        return q.all()
