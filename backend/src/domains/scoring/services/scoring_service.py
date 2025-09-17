from __future__ import annotations

import uuid as _uuid
from collections.abc import Iterable
from datetime import date
from typing import Any, List, Dict

from sqlalchemy.orm import Session

from src.domains.scoring.models.score import Score
from src.domains.shared.interfaces.scoring_service import ScoringServiceInterface


class ScoringService(ScoringServiceInterface):
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
        self, *, league_id: _uuid.UUID | str, game_day: date | None
    ) -> list[dict[str, Any]]:
        """Compute per-team totals for a league.

        Aggregates scores by summing stats.points for players listed in each
        team's lineups.

        - league_id may be UUID or str
        - if game_day is None, include all days; otherwise filter to that day
        - returns list of { team_id: UUID, total_points: int, lineup_count: int }
          sorted by total_points desc
        """
        print(f"ScoringService.compute_league_scoreboard - league_id: {league_id}") # Added
        import uuid as _uuid

        from src.domains.scoring.models.lineup import Lineup
        from src.domains.scoring.models.score import Score
        from src.domains.scoring.models.team import Team

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
        print(f"ScoringService.compute_league_scoreboard - lineups found: {len(lineups)}") # Added

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

    # Interface implementation methods
    async def calculate_lineup_score(self, lineup_id: str, period: str) -> Dict[str, Any]:
        """Calculate total score for a lineup in a specific period."""
        from src.domains.lineups.models.lineup import Lineup

        lineup_uuid = _uuid.UUID(lineup_id)
        lineup = self.session.query(Lineup).filter(Lineup.lineup_id == lineup_uuid).first()
        if not lineup:
            raise ValueError(f"Lineup with ID {lineup_id} not found")

        # Calculate total points for the lineup's game day
        total_points = 0
        player_ids = []
        for player in lineup.players or []:
            pid = player.get("player_id")
            if pid:
                try:
                    player_ids.append(_uuid.UUID(str(pid)))
                except ValueError:
                    continue

        if player_ids:
            scores = (
                self.session.query(Score)
                .filter(
                    Score.player_id.in_(player_ids), Score.game_day == lineup.game_day
                )
                .all()
            )
            for score in scores:
                stats = score.stats or {}
                points = stats.get("points", 0)
                try:
                    total_points += int(points)
                except (ValueError, TypeError):
                    pass

        return {
            "score_id": str(_uuid.uuid4()),
            "lineup_id": lineup_id,
            "period": period,
            "total_points": total_points,
            "calculated_at": date.today().isoformat(),
        }

    async def get_scoring_rules(self, league_id: str) -> Dict[str, Any]:
        """Get scoring rules for a specific league."""
        # For now, return default scoring rules
        # In the future, this would be configurable per league
        return {
            "rules_id": str(_uuid.uuid4()),
            "league_id": league_id,
            "passing_yard": 0.04,
            "passing_td": 4,
            "rushing_yard": 0.1,
            "rushing_td": 6,
            "receiving_yard": 0.1,
            "receiving_td": 6,
            "interception": -2,
            "fumble": -2,
        }

    async def audit_score_calculation(self, score_id: str) -> Dict[str, Any]:
        """Get audit trail for a score calculation."""
        # For now, return a placeholder audit trail
        # In the future, this would track actual calculation history
        return {
            "audit_id": str(_uuid.uuid4()),
            "score_id": score_id,
            "calculation_method": "standard",
            "calculated_by": "system",
            "calculation_steps": [
                {"step": "retrieve_stats", "status": "completed"},
                {"step": "apply_rules", "status": "completed"},
                {"step": "sum_totals", "status": "completed"},
            ],
        }

    async def get_player_performance(
        self, player_id: str, period: str
    ) -> Dict[str, Any]:
        """Get performance data for a specific player in a period."""
        player_uuid = _uuid.UUID(player_id)

        # Get all scores for the player
        scores = self.session.query(Score).filter(Score.player_id == player_uuid).all()

        total_points = 0
        game_count = len(scores)
        for score in scores:
            stats = score.stats or {}
            points = stats.get("points", 0)
            try:
                total_points += int(points)
            except (ValueError, TypeError):
                pass

        return {
            "player_id": player_id,
            "period": period,
            "total_points": total_points,
            "games_played": game_count,
            "average_points": total_points / max(1, game_count),
        }

    async def get_league_standings(self, league_id: str, period: str) -> List[Dict[str, Any]]:
        """Get current standings for a league in a specific period."""
        league_uuid = _uuid.UUID(league_id)

        # Use the existing compute_league_scoreboard method
        scoreboard = self.compute_league_scoreboard(
            league_id=league_uuid, game_day=None
        )

        # Convert to standings format
        standings = []
        for rank, item in enumerate(scoreboard, 1):
            standings.append(
                {
                    "rank": rank,
                    "team_id": str(item["team_id"]),
                    "total_points": item["total_points"],
                    "games_played": item["lineup_count"],
                }
            )

        return standings

    async def recalculate_scores(self, league_id: str, period: str) -> List[Dict[str, Any]]:
        """Recalculate all scores for a league in a specific period."""
        from src.domains.lineups.models.lineup import Lineup
        from src.domains.leagues.models.team import Team

        league_uuid = _uuid.UUID(league_id)

        # Get all teams in the league
        teams = self.session.query(Team).filter(Team.league_id == league_uuid).all()
        team_ids = [team.team_id for team in teams]

        # Get all lineups for these teams
        lineups = self.session.query(Lineup).filter(Lineup.team_id.in_(team_ids)).all()

        scores = []
        for lineup in lineups:
            score = await self.calculate_lineup_score(str(lineup.lineup_id), period)
            scores.append(score)

        return scores