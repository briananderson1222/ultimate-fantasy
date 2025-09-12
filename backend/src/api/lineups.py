from __future__ import annotations

import uuid as _uuid
from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, Header, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from api.deps import get_db
from services.lineup_service import LineupService

router = APIRouter()


class LineupPlayer(BaseModel):
    player_id: _uuid.UUID
    position: str = Field(..., max_length=20)


class LineupRequest(BaseModel):
    team_id: _uuid.UUID
    game_day: date
    players: list[LineupPlayer]


class LineupResponse(BaseModel):
    team_id: _uuid.UUID
    game_day: date
    players: list[LineupPlayer]
    version: int | None = None


@router.put("/lineups", status_code=status.HTTP_200_OK, response_model=LineupResponse)
def set_lineup(
    payload: LineupRequest,
    db: Session = Depends(get_db),
    x_user_id: Annotated[str | None, Header(alias="x-user-id")] = None,
) -> LineupResponse:
    if not x_user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="missing user"
        )

    svc = LineupService(db)
    lu = svc.set_lineup(
        team_id=payload.team_id,
        game_day=payload.game_day,
        players=[p.model_dump() for p in payload.players],
    )
    # Echo back the canonical representation
    return LineupResponse(
        team_id=payload.team_id,
        game_day=payload.game_day,
        players=payload.players,
        version=getattr(lu, "version", None),
    )
