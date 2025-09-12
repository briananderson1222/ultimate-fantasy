from __future__ import annotations

import uuid as _uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Header, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from api.deps import get_db
from services.league_service import LeagueService

router = APIRouter()


class LeagueCreate(BaseModel):
    name: str = Field(..., max_length=200)
    sport: str = Field(..., max_length=50)
    league_type: str = Field(..., max_length=50)
    season: str = Field(..., max_length=16)


class LeagueResponse(BaseModel):
    league_id: _uuid.UUID
    name: str
    sport: str
    league_type: str
    season: str
    invite_link: str | None = None


@router.post(
    "/leagues", status_code=status.HTTP_201_CREATED, response_model=LeagueResponse
)
def create_league(
    payload: LeagueCreate,
    db: Session = Depends(get_db),
    x_user_id: Annotated[str | None, Header(alias="x-user-id")] = None,
) -> LeagueResponse:
    if not x_user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="missing user"
        )
    try:
        commissioner_id = _uuid.UUID(x_user_id)
    except ValueError as e:  # noqa: F841
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="invalid user id"
        )

    svc = LeagueService(db)
    league = svc.create(
        commissioner_id=commissioner_id,
        name=payload.name,
        sport=payload.sport,
        league_type=payload.league_type,
        season=payload.season,
    )

    return LeagueResponse(
        league_id=league.league_id,
        name=league.name,
        sport=league.sport,
        league_type=league.league_type,
        season=league.season,
        invite_link=f"/leagues/{league.league_id}/join",
    )
