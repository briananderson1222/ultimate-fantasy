from __future__ import annotations

import uuid as _uuid
from datetime import date

from fastapi import APIRouter, Depends, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from src.api.deps import get_current_user_id, get_db
from src.services.lineup_service import LineupService

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
    _user_id: _uuid.UUID = Depends(get_current_user_id),
) -> LineupResponse:
    """
    Set the lineup for a specific team and game day.

    This endpoint allows an authenticated user to set their team's lineup for a
    particular day. The user must be the owner of the team.

    - **team_id**: The unique identifier of the team.
    - **game_day**: The date for which the lineup is being set.
    - **players**: A list of players and their assigned positions in the lineup.

    The service layer handles the logic of creating or updating the lineup for the
    given day.
    """

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


class LineupListItem(BaseModel):
    lineup_id: _uuid.UUID
    team_id: _uuid.UUID
    game_day: date
    players: list[LineupPlayer]
    version: int


class LineupListResponse(BaseModel):
    items: list[LineupListItem]


@router.get(
    "/lineups", status_code=status.HTTP_200_OK, response_model=LineupListResponse
)
def list_lineups(
    team_id: _uuid.UUID = Query(...),
    game_day: date | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
) -> LineupListResponse:
    """
    List historical lineups for a team.

    This endpoint retrieves a paginated list of lineups for a specific team.
    It can be filtered by `game_day`.

    - **team_id**: The unique identifier of the team.
    - **game_day** (optional): Filter lineups for a specific date.
    - **limit**: The maximum number of lineups to return.
    - **offset**: The starting point for pagination.
    """
    svc = LineupService(db)
    items = svc.list(
        team_id=str(team_id), game_day=game_day, limit=limit, offset=offset
    )

    def to_player(obj: dict) -> LineupPlayer:
        return LineupPlayer(
            player_id=_uuid.UUID(str(obj.get("player_id"))),
            position=str(obj.get("position")),
        )

    casted = [
        LineupListItem(
            lineup_id=it.lineup_id,
            team_id=it.team_id,
            game_day=it.game_day,
            players=[to_player(p) for p in (it.players or [])],
            version=getattr(it, "version", 1),
        )
        for it in items
    ]
    return LineupListResponse(items=casted)
