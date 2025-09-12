from __future__ import annotations

import uuid as _uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Header, HTTPException, Path, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from api.deps import get_db
from services.league_service import LeagueService

router = APIRouter()


class JoinResponse(BaseModel):
    team_id: _uuid.UUID
    league_id: _uuid.UUID
    user_id: _uuid.UUID
    team_name: str


@router.post(
    "/leagues/{leagueId}/join",
    status_code=status.HTTP_200_OK,
    response_model=JoinResponse,
)
def join_league(
    leagueId: Annotated[str, Path()],
    db: Session = Depends(get_db),
    x_user_id: Annotated[str | None, Header(alias="x-user-id")] = None,
) -> JoinResponse:
    if not x_user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="missing user"
        )
    try:
        user_id = _uuid.UUID(x_user_id)
        league_uuid = _uuid.UUID(leagueId)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="invalid id format"
        )

    svc = LeagueService(db)
    team = svc.join(user_id=user_id, league_id=league_uuid)
    return JoinResponse(
        team_id=team.team_id,
        league_id=team.league_id,
        user_id=team.user_id,
        team_name=team.team_name,
    )
