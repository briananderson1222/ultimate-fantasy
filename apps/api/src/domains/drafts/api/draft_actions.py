"""
Draft actions API endpoints for starting drafts and making picks.
"""

import uuid
from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from api.middleware.auth import get_current_user
from domains.users.models.user import User

router = APIRouter(prefix="/api/v1/drafts", tags=["drafts"])


class DraftStartRequest(BaseModel):
    """Request to start a draft."""

    draft_settings: dict[str, Any] | None = None
    timer_seconds: int = Field(default=120, ge=30, le=600)
    auto_draft_enabled: bool = True


class DraftStartResponse(BaseModel):
    """Response when starting a draft."""

    draft_id: str
    status: str
    started_at: datetime
    current_pick: int
    current_round: int
    timer_seconds: int


class DraftPickRequest(BaseModel):
    """Request to make a draft pick."""

    player_id: str
    position: str | None = None


class DraftPickResponse(BaseModel):
    """Response after making a draft pick."""

    pick_id: str
    draft_id: str
    team_id: str
    player_id: str
    player_name: str
    position: str
    pick_number: int
    round_number: int
    picked_at: datetime
    next_pick_team_id: str | None = None
    time_remaining: int | None = None


class DraftStatus(BaseModel):
    """Current draft status."""

    draft_id: str
    status: str
    current_pick: int
    current_round: int
    total_rounds: int
    current_team_id: str | None
    time_remaining: int | None
    picks_made: int
    total_picks: int


@router.post("/{draft_id}/start", response_model=DraftStartResponse)
async def start_draft(
    draft_id: str,
    request: DraftStartRequest,
    current_user: User = Depends(get_current_user),
) -> DraftStartResponse:
    """
    Start a scheduled draft.

    This endpoint:
    - Validates the user has permission to start the draft
    - Updates draft status to 'active'
    - Initializes draft order and timer
    - Notifies all league members via WebSocket
    - Returns draft status information
    """

    # Mock validation - would check if user is commissioner and draft is scheduled
    if not draft_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Draft ID is required"
        )

    # Mock implementation - would interact with draft service
    draft_start_response = DraftStartResponse(
        draft_id=draft_id,
        status="active",
        started_at=datetime.utcnow(),
        current_pick=1,
        current_round=1,
        timer_seconds=request.timer_seconds,
    )

    return draft_start_response


@router.post("/{draft_id}/pick", response_model=DraftPickResponse)
async def make_draft_pick(
    draft_id: str,
    request: DraftPickRequest,
    current_user: User = Depends(get_current_user),
) -> DraftPickResponse:
    """
    Make a draft pick.

    This endpoint:
    - Validates it's the user's turn to pick
    - Validates the player is available
    - Records the pick in the database
    - Updates draft status to next pick
    - Broadcasts pick to all draft participants
    - Returns pick confirmation
    """

    # Mock validation
    if not draft_id or not request.player_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Draft ID and Player ID are required",
        )

    # Mock implementation - would interact with draft service
    pick_response = DraftPickResponse(
        pick_id=str(uuid.uuid4()),
        draft_id=draft_id,
        team_id=str(current_user.user_id),  # Simplified - would get actual team ID
        player_id=request.player_id,
        player_name="Mike Trout",  # Would look up player name
        position=request.position or "OF",
        pick_number=1,
        round_number=1,
        picked_at=datetime.utcnow(),
        next_pick_team_id=str(uuid.uuid4()),  # Would determine next team
        time_remaining=120,
    )

    return pick_response


@router.get("/{draft_id}/status", response_model=DraftStatus)
async def get_draft_status(
    draft_id: str,
    current_user: User = Depends(get_current_user),
) -> DraftStatus:
    """Get current draft status and state."""

    # Mock implementation
    return DraftStatus(
        draft_id=draft_id,
        status="active",
        current_pick=5,
        current_round=1,
        total_rounds=16,
        current_team_id=str(uuid.uuid4()),
        time_remaining=95,
        picks_made=4,
        total_picks=192,  # 12 teams * 16 rounds
    )


@router.get("/{draft_id}/picks", response_model=list[DraftPickResponse])
async def get_draft_picks(
    draft_id: str,
    round_number: int | None = None,
    team_id: str | None = None,
    current_user: User = Depends(get_current_user),
) -> list[DraftPickResponse]:
    """Get all picks made in the draft, optionally filtered."""

    # Mock implementation
    picks = [
        DraftPickResponse(
            pick_id=str(uuid.uuid4()),
            draft_id=draft_id,
            team_id=str(uuid.uuid4()),
            player_id="player_123",
            player_name="Christian McCaffrey",
            position="RB",
            pick_number=1,
            round_number=1,
            picked_at=datetime.utcnow(),
            next_pick_team_id=None,
            time_remaining=None,
        ),
        DraftPickResponse(
            pick_id=str(uuid.uuid4()),
            draft_id=draft_id,
            team_id=str(uuid.uuid4()),
            player_id="player_456",
            player_name="Josh Allen",
            position="QB",
            pick_number=2,
            round_number=1,
            picked_at=datetime.utcnow(),
            next_pick_team_id=None,
            time_remaining=None,
        ),
    ]

    # Apply filters
    if round_number:
        picks = [pick for pick in picks if pick.round_number == round_number]
    if team_id:
        picks = [pick for pick in picks if pick.team_id == team_id]

    return picks


@router.post("/{draft_id}/pause")
async def pause_draft(
    draft_id: str,
    current_user: User = Depends(get_current_user),
) -> dict[str, str]:
    """Pause an active draft (commissioner only)."""

    # Mock implementation
    return {"status": "paused", "message": "Draft has been paused"}


@router.post("/{draft_id}/resume")
async def resume_draft(
    draft_id: str,
    current_user: User = Depends(get_current_user),
) -> dict[str, str]:
    """Resume a paused draft (commissioner only)."""

    # Mock implementation
    return {"status": "active", "message": "Draft has been resumed"}


@router.post("/{draft_id}/autopick")
async def enable_autopick(
    draft_id: str,
    enabled: bool = True,
    current_user: User = Depends(get_current_user),
) -> dict[str, Any]:
    """Enable or disable autopick for current user."""

    # Mock implementation
    return {
        "autopick_enabled": enabled,
        "message": f"Autopick {'enabled' if enabled else 'disabled'} for your team",
    }
