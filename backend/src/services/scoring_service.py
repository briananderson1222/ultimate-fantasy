from __future__ import annotations

from datetime import date
from typing import Iterable

from sqlalchemy.orm import Session

from models.score import Score


class ScoringService:
    def __init__(self, session: Session) -> None:
        self.session = session

    def ingest_player_stats(self, *, game_day: date, items: Iterable[dict]) -> int:
        """Ingest raw stat items and persist Score rows.

        Each item must include: player_id (UUID as str), stats (dict)
        Returns number of upserts (currently inserts only).
        """
        count = 0
        for it in items:
            score = Score(player_id=it["player_id"], game_day=game_day, stats=it["stats"])
            self.session.add(score)
            count += 1
        self.session.flush()
        return count
