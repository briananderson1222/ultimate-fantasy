from __future__ import annotations

import uuid as _uuid
from collections.abc import Iterable
from datetime import date
from typing import Any

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
            score = Score(
                player_id=it["player_id"], game_day=game_day, stats=it["stats"]
            )
            self.session.add(score)
            count += 1
        self.session.flush()
        return count

    def compute_league_scoreboard(
        self, *, league_id: _uuid.UUID, game_day: date | None
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

        from models.lineup import Lineup
        from models.score import Score
        from models.team import Team

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
                    stats = s.stats or {}
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
