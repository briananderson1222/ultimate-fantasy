from __future__ import annotations

import uuid
from collections.abc import Iterable
from datetime import date

from sqlalchemy.orm import Session

from src.domains.lineups.models.lineup import Lineup


class LineupService:
    def __init__(self, session: Session) -> None:
        self.session = session

    def set_lineup(
        self, *, team_id: str | uuid.UUID, game_day: date, players: Iterable[dict]
    ) -> Lineup:
        # TODO: enforce league rules and roster checks (positions, duplicates, etc.)
        team_uuid = uuid.UUID(team_id) if isinstance(team_id, str) else team_id

        # Convert UUIDs to strings for JSON serialization
        serializable_players = []
        for player in players:
            player_copy = player.copy()
            if "player_id" in player_copy and hasattr(player_copy["player_id"], "hex"):
                player_copy["player_id"] = str(player_copy["player_id"])
            serializable_players.append(player_copy)

        lineup = Lineup(
            team_id=team_uuid,
            game_day=game_day,
            players=serializable_players,
            version=1,
        )
        self.session.add(lineup)
        self.session.flush()
        return lineup

    def list(
        self,
        *,
        team_id: str | uuid.UUID,
        game_day: date | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[Lineup]:
        team_uuid = uuid.UUID(team_id) if isinstance(team_id, str) else team_id
        q = self.session.query(Lineup).filter(Lineup.team_id == team_uuid)
        if game_day is not None:
            q = q.filter(Lineup.game_day == game_day)
        q = q.offset(max(0, offset)).limit(max(1, min(100, limit)))
        return q.all()
