from __future__ import annotations

import uuid as _uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Path, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from api.deps import get_db
from models.league import League

router = APIRouter()


class LeaguePublic(BaseModel):
    league_id: _uuid.UUID
    name: str
    sport: str
    league_type: str
    season: str


@router.get(
    "/leagues/{leagueId}/public",
    status_code=status.HTTP_200_OK,
    response_model=LeaguePublic,
)
def public_league(
    leagueId: Annotated[str, Path()],
    db: Session = Depends(get_db),
) -> LeaguePublic:
    try:
        league_uuid = _uuid.UUID(leagueId)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="invalid league id"
        )

    league = db.get(League, league_uuid)
    if not league:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="league not found"
        )

    return LeaguePublic(
        league_id=league.league_id,
        name=league.name,
        sport=league.sport,
        league_type=league.league_type,
        season=league.season,
    )
