from __future__ import annotations

import uuid as _uuid

from fastapi import APIRouter, Depends, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from api.deps import get_current_user_id, get_db
from services.league_service import LeagueService

router = APIRouter()


class MeLeagueItem(BaseModel):
    league_id: _uuid.UUID
    name: str
    season: str
    team_id: _uuid.UUID


class MeLeaguesResponse(BaseModel):
    items: list[MeLeagueItem]


@router.get(
    "/me/leagues", status_code=status.HTTP_200_OK, response_model=MeLeaguesResponse
)
def list_my_leagues(
    user_id: _uuid.UUID = Depends(get_current_user_id),
    db: Session = Depends(get_db),
) -> MeLeaguesResponse:
    """
    List all leagues the current user has joined.

    This endpoint retrieves a list of all leagues that the authenticated user
    is a member of. The user is identified via their authentication token.

    For each league, it returns the `league_id`, `name`, `season`, and the user's
    corresponding `team_id` in that league.
    """
    items = LeagueService(db).list_by_user(user_id=user_id)
    casted = [
        MeLeagueItem(
            league_id=_uuid.UUID(it["league_id"]),
            name=it["name"],
            season=it["season"],
            team_id=_uuid.UUID(it["team_id"]),
        )
        for it in items
    ]
    return MeLeaguesResponse(items=casted)
