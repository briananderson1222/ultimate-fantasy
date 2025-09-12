from __future__ import annotations

import uuid as _uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Header, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from services.waiver_service import WaiverService
from api.deps import get_db


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


@router.post("/waivers/bids", status_code=status.HTTP_201_CREATED, response_model=WaiverBidResponse)
def place_waiver_bid(
    payload: WaiverBidRequest,
    db: Session = Depends(get_db),
    x_user_id: Annotated[str | None, Header(alias="x-user-id")] = None,
):
    if not x_user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="missing user")

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
