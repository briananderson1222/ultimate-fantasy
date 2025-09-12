from __future__ import annotations

import uuid as _uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Path, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from api.deps import get_db


router = APIRouter()


class ScoreboardResponse(BaseModel):
    league_id: _uuid.UUID
    items: list[dict] = Field(default_factory=list)


@router.get(
    "/leagues/{leagueId}/scoreboard",
    status_code=status.HTTP_200_OK,
    response_model=ScoreboardResponse,
)
def get_scoreboard(
    leagueId: Annotated[str, Path()],
    db: Session = Depends(get_db),  # noqa: ARG001 - reserved for future use
):
    # Placeholder. When ScoringService aggregates by league, populate items accordingly.
    return ScoreboardResponse(league_id=_uuid.UUID(leagueId), items=[])
