from __future__ import annotations

import uuid as _uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Path, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from api.deps import get_db
from domains.scoring.services.scoring_service import ScoringService

router = APIRouter()


class ScoreboardItem(BaseModel):
    team_id: _uuid.UUID
    total_points: int
    lineup_count: int | None = None


class ScoreboardResponse(BaseModel):
    league_id: _uuid.UUID
    items: list[ScoreboardItem] = Field(default_factory=list)


@router.get(
    "/leagues/{leagueId}/scoreboard",
    status_code=status.HTTP_200_OK,
    response_model=ScoreboardResponse,
)
def get_scoreboard(
    leagueId: Annotated[str, Path()],
    db: Session = Depends(get_db),
) -> ScoreboardResponse:
    """
    Get the scoreboard for a specific league.

    This endpoint computes and returns the current scoreboard for a given league.
    The scoreboard includes the total points for each team in the league.

    - **leagueId**: The unique identifier of the league.

    The scoring logic is handled by the `ScoringService`.
    """
    svc = ScoringService(db)
    try:
        items = [
            ScoreboardItem(**it)
            for it in svc.compute_league_scoreboard(
                league_id=_uuid.UUID(leagueId), game_day=None
            )
        ]
    except Exception as e:
        # Log the exception for debugging
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="League not found or other error"
        ) from e

    return ScoreboardResponse(league_id=_uuid.UUID(leagueId), items=items)
