from __future__ import annotations

import uuid as _uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Path, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from src.api.deps import get_db
from services.league_service import LeagueService

router = APIRouter()


class MemberItem(BaseModel):
    team_id: _uuid.UUID
    user_id: _uuid.UUID
    team_name: str


class MembersResponse(BaseModel):
    items: list[MemberItem]


@router.get(
    "/leagues/{leagueId}/members",
    status_code=status.HTTP_200_OK,
    response_model=MembersResponse,
)
def list_members(
    leagueId: Annotated[str, Path()], db: Session = Depends(get_db)
) -> MembersResponse:
    """
    List all members of a specific league.

    This endpoint retrieves a list of all members (and their teams) for a given
    league. This is a public endpoint and does not require authentication.

    - **leagueId**: The unique identifier of the league.

    For each member, it returns their `team_id`, `user_id`, and `team_name`.
    """
    try:
        league_uuid = _uuid.UUID(leagueId)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="invalid league id"
        )

    items = LeagueService(db).list_members(league_id=league_uuid)
    casted = [
        MemberItem(
            team_id=_uuid.UUID(it["team_id"]),
            user_id=_uuid.UUID(it["user_id"]),
            team_name=it["team_name"],
        )
        for it in items
    ]
    return MembersResponse(items=casted)
