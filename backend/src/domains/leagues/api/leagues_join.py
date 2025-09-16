from __future__ import annotations

import uuid as _uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Path, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from src.api.deps import get_current_user_id, get_db
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
    user_id: _uuid.UUID = Depends(get_current_user_id),
) -> JoinResponse:
    """
    Join a fantasy league.

    This endpoint allows an authenticated user to join an existing league using its
    `leagueId`. When a user joins a league, a new team is automatically created
    for them within that league.

    - **leagueId**: The unique identifier of the league to join.

    The user is identified via their authentication token. If the user is already
    a member of the league, the service layer will prevent them from joining again.

    Returns the details of the newly created team, including its `team_id`.
    """
    try:
        league_uuid = _uuid.UUID(leagueId)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="invalid id format"
        )

    svc = LeagueService(db)
    try:
        team = svc.join(user_id=user_id, league_id=league_uuid)
    except Exception as e: # Catch all exceptions
        print(f"Error in join_league endpoint: {type(e).__name__}: {e}") # Log the exception type and message
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal Server Error"
        ) from e # Change to 500 for now, to distinguish from 404

    return JoinResponse(
        team_id=team.team_id,
        league_id=team.league_id,
        user_id=team.user_id,
        team_name=team.team_name,
    )
