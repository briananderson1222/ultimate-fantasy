from __future__ import annotations

import uuid as _uuid

from fastapi import APIRouter, Depends, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from api.deps import get_current_user_id, get_db
from services.waiver_service import WaiverService

router = APIRouter()


class WaiverBidRequest(BaseModel):
    league_id: _uuid.UUID
    team_id: _uuid.UUID
    player_id: _uuid.UUID
    bid: int = Field(..., ge=0)


class WaiverBidResponse(BaseModel):
    waiver_id: _uuid.UUID
    league_id: _uuid.UUID
    team_id: _uuid.UUID
    player_id: _uuid.UUID
    bid: int
    status: str


@router.post(
    "/waivers/bids",
    status_code=status.HTTP_201_CREATED,
    response_model=WaiverBidResponse,
)
def place_waiver_bid(
    payload: WaiverBidRequest,
    db: Session = Depends(get_db),
    _user_id: _uuid.UUID = Depends(get_current_user_id),
) -> WaiverBidResponse:

    svc = WaiverService(db)
    w = svc.place_bid(
        league_id=str(payload.league_id),
        team_id=str(payload.team_id),
        player_id=str(payload.player_id),
        bid=payload.bid,
    )
    return WaiverBidResponse(
        waiver_id=w.waiver_id,
        league_id=w.league_id,
        team_id=w.team_id,
        player_id=w.player_id,
        bid=w.bid,
        status=w.status,
    )


class WaiverListItem(BaseModel):
    waiver_id: _uuid.UUID
    league_id: _uuid.UUID
    team_id: _uuid.UUID
    player_id: _uuid.UUID
    bid: int
    status: str


class WaiverListResponse(BaseModel):
    items: list[WaiverListItem]


@router.get(
    "/waivers", status_code=status.HTTP_200_OK, response_model=WaiverListResponse
)
def list_waivers(
    league_id: _uuid.UUID = Query(...),
    team_id: _uuid.UUID | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
) -> WaiverListResponse:
    svc = WaiverService(db)
    items = svc.list(
        league_id=str(league_id),
        team_id=str(team_id) if team_id else None,
        limit=limit,
        offset=offset,
    )
    return WaiverListResponse(
        items=[
            WaiverListItem(
                waiver_id=w.waiver_id,
                league_id=w.league_id,
                team_id=w.team_id,
                player_id=w.player_id,
                bid=w.bid,
                status=w.status,
            )
            for w in items
        ]
    )
