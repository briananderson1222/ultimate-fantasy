from __future__ import annotations

import uuid as _uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Path, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from api.deps import get_db
from services.scoring_service import ScoringService

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
    svc = ScoringService(db)
    items = [
        ScoreboardItem(**it)
        for it in svc.compute_league_scoreboard(
            league_id=_uuid.UUID(leagueId), game_day=None
        )
    ]
    return ScoreboardResponse(league_id=_uuid.UUID(leagueId), items=items)
