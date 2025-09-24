"""
POST /api/v1/draft/{leagueId} endpoint implementation.

Provides draft initialization and management functionality including:
- Draft creation and setup for a league
- Validation of league state and member readiness
- Draft order generation with snake algorithm
- Timer initialization and WebSocket setup
- Real-time participant notification
- Error handling for invalid states
"""

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Path
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from api.deps import get_current_user, get_db
from api.models.response import StandardResponse
from domains.drafts.algorithms.snake_draft import get_snake_draft_algorithm
from domains.drafts.services.draft_timer import get_draft_timer_service
from domains.leagues.models.league import League
from domains.teams.models.team import Team
from domains.users.models.user import User

try:
    from infrastructure.logging.domain_logger import get_logger
except ImportError:
    import logging
    get_logger = logging.getLogger  # type: ignore[assignment]

logger = get_logger(__name__)

router = APIRouter()


class DraftStartRequest(BaseModel):
    """Request model for starting a draft."""

    pick_time_seconds: int = Field(
        default=90,
        ge=30,
        le=300,
        description="Time limit per pick in seconds (30-300)"
    )
    randomize_order: bool = Field(
        default=True,
        description="Whether to randomize the initial draft order"
    )
    total_rounds: int = Field(
        default=15,
        ge=1,
        le=25,
        description="Total number of draft rounds (1-25)"
    )
    seed: Optional[int] = Field(
        default=None,
        description="Random seed for reproducible draft order"
    )


class DraftStartResponse(BaseModel):
    """Response model for draft start."""

    draft_id: str
    league_id: str
    status: str
    draft_order: list[dict]
    current_pick: dict
    timer_status: dict
    participants: list[dict]
    settings: dict
    websocket_url: str
    created_at: str


@router.post("/draft/{league_id}", response_model=StandardResponse[DraftStartResponse])
async def start_draft(
    league_id: str = Path(..., description="League ID to start draft for"),
    request: DraftStartRequest = DraftStartRequest(),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> StandardResponse[DraftStartResponse]:
    """
    Start a draft for the specified league.

    This endpoint initializes a new draft with the following features:
    - Validates league state and permissions
    - Generates snake draft order with randomization
    - Sets up real-time timer and WebSocket connections
    - Notifies all league members
    - Returns draft details and connection information

    **Requirements:**
    - User must be league commissioner or admin
    - League must be in 'setup' status (not already drafting)
    - League must have sufficient teams (minimum 2)
    - All teams must have active owners

    **Returns:**
    - Draft ID and configuration details
    - Current pick information and timer status
    - WebSocket URL for real-time updates
    - Participant list and draft order
    """
    try:
        logger.info(
            f"Draft start request",
            extra={
                "user_id": str(current_user.user_id),
                "league_id": league_id,
                "pick_time_seconds": request.pick_time_seconds,
                "total_rounds": request.total_rounds,
            }
        )

        # Get and validate league
        league = db.query(League).filter(
            League.league_id == league_id
        ).first()

        if not league:
            raise HTTPException(
                status_code=404,
                detail=f"League {league_id} not found"
            )

        # Check permissions - user must be commissioner
        if league.commissioner_id != current_user.user_id:
            raise HTTPException(
                status_code=403,
                detail="Only the league commissioner can start a draft"
            )

        # Validate league state
        if league.status != "setup":
            raise HTTPException(
                status_code=400,
                detail=f"Cannot start draft for league in '{league.status}' status. League must be in 'setup' status."
            )

        # Get league teams
        teams = db.query(Team).filter(
            Team.league_id == league_id
        ).all()

        if len(teams) < 2:
            raise HTTPException(
                status_code=400,
                detail="League must have at least 2 teams to start a draft"
            )

        # Validate all teams have active owners
        for team in teams:
            if not team.owner_id:
                raise HTTPException(
                    status_code=400,
                    detail=f"Team '{team.team_name}' does not have an active owner"
                )

        # Check for existing active draft
        draft_timer_service = get_draft_timer_service()
        existing_timer = draft_timer_service.get_draft_timer(league_id)
        if existing_timer:
            raise HTTPException(
                status_code=409,
                detail="Draft is already in progress for this league"
            )

        # Generate draft order using snake algorithm
        snake_algorithm = get_snake_draft_algorithm()
        team_ids = [team.team_id for team in teams]

        draft_order = snake_algorithm.generate_draft_order(
            teams=team_ids,
            total_rounds=request.total_rounds,
            randomize=request.randomize_order,
            seed=request.seed,
            draft_id=league_id,
        )

        # Create draft timer
        draft_timer = await draft_timer_service.create_draft_timer(
            draft_id=league_id,
            draft_order=draft_order,
            pick_time_seconds=request.pick_time_seconds,
        )

        # Update league status to drafting
        league.status = "drafting"
        league.draft_started_at = datetime.utcnow()
        db.commit()

        # Start the draft
        await draft_timer.start_draft()

        # Get current timer status
        timer_status = draft_timer.get_timer_status()

        # Build participant information
        participants = []
        for team in teams:
            participants.append({
                "team_id": team.team_id,
                "team_name": team.team_name,
                "owner_id": str(team.owner_id),
                "draft_position": next(
                    (i + 1 for i, t_id in enumerate(draft_order.teams) if t_id == team.team_id),
                    None
                ),
            })

        # Serialize draft order
        draft_order_response = []
        for pick in draft_order.picks:
            draft_order_response.append({
                "overall_pick": pick.overall_pick,
                "round_number": pick.round_number,
                "pick_in_round": pick.pick_in_round,
                "team_id": pick.team_id,
                "is_keeper": pick.is_keeper,
            })

        # Create response
        response_data = DraftStartResponse(
            draft_id=league_id,
            league_id=league_id,
            status="in_progress",
            draft_order=draft_order_response,
            current_pick=timer_status["current_pick"] or {},
            timer_status=timer_status,
            participants=participants,
            settings={
                "pick_time_seconds": request.pick_time_seconds,
                "total_rounds": request.total_rounds,
                "randomize_order": request.randomize_order,
                "randomized_at": draft_order.randomized_at.isoformat() if draft_order.randomized_at else None,
                "seed": draft_order.seed,
            },
            websocket_url=f"/api/v1/real-time/connect?draft_id={league_id}",
            created_at=datetime.utcnow().isoformat(),
        )

        logger.info(
            f"Draft started successfully",
            extra={
                "user_id": str(current_user.user_id),
                "league_id": league_id,
                "draft_id": league_id,
                "teams_count": len(teams),
                "total_picks": len(draft_order.picks),
            }
        )

        return StandardResponse(
            success=True,
            data=response_data,
            message=f"Draft started for league {league.league_name} with {len(teams)} teams"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Failed to start draft",
            extra={
                "user_id": str(current_user.user_id),
                "league_id": league_id,
                "error": str(e),
            }
        )

        raise HTTPException(
            status_code=500,
            detail="Failed to start draft. Please try again later."
        )


@router.get("/draft/{league_id}/status", response_model=StandardResponse[dict])
async def get_draft_status(
    league_id: str = Path(..., description="League ID to get draft status for"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> StandardResponse[dict]:
    """
    Get current draft status for a league.

    Returns information about the current state of the draft including:
    - Current pick details and timer status
    - Draft progress and completed picks
    - Participant information
    - WebSocket connection details

    **Returns:**
    - Draft status and timer information
    - Current pick details
    - Progress statistics
    """
    try:
        logger.info(
            f"Draft status request",
            extra={
                "user_id": str(current_user.user_id),
                "league_id": league_id,
            }
        )

        # Validate league exists and user has access
        league = db.query(League).filter(
            League.league_id == league_id
        ).first()

        if not league:
            raise HTTPException(
                status_code=404,
                detail=f"League {league_id} not found"
            )

        # Check if user is member of the league
        user_team = db.query(Team).filter(
            Team.league_id == league_id,
            Team.owner_id == current_user.user_id
        ).first()

        if not user_team and league.commissioner_id != current_user.user_id:
            raise HTTPException(
                status_code=403,
                detail="You must be a league member to view draft status"
            )

        # Get draft timer
        draft_timer_service = get_draft_timer_service()
        draft_timer = draft_timer_service.get_draft_timer(league_id)

        if not draft_timer:
            # No active draft
            status_data = {
                "status": "not_started",
                "league_status": league.status,
                "message": "No active draft for this league",
            }
        else:
            # Get timer status
            timer_status = draft_timer.get_timer_status()

            status_data = {
                "status": timer_status["status"],
                "current_pick": timer_status["current_pick"],
                "time_remaining": timer_status["time_remaining"],
                "is_paused": timer_status["is_paused"],
                "completed_picks": timer_status["completed_picks"],
                "total_picks": timer_status["total_picks"],
                "progress_percentage": round(
                    (timer_status["completed_picks"] / timer_status["total_picks"]) * 100, 1
                ) if timer_status["total_picks"] > 0 else 0,
                "websocket_url": f"/api/v1/real-time/connect?draft_id={league_id}",
            }

        logger.info(
            f"Draft status retrieved",
            extra={
                "user_id": str(current_user.user_id),
                "league_id": league_id,
                "draft_status": status_data["status"],
            }
        )

        return StandardResponse(
            success=True,
            data=status_data,
            message="Draft status retrieved successfully"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Failed to get draft status",
            extra={
                "user_id": str(current_user.user_id),
                "league_id": league_id,
                "error": str(e),
            }
        )

        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve draft status. Please try again later."
        )


@router.post("/draft/{league_id}/pause", response_model=StandardResponse[dict])
async def pause_draft(
    league_id: str = Path(..., description="League ID to pause draft for"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> StandardResponse[dict]:
    """
    Pause the current draft timer.

    Only the league commissioner can pause a draft.
    The draft can be resumed later with the remaining time.

    **Requirements:**
    - User must be league commissioner
    - Draft must be active (not already paused or completed)

    **Returns:**
    - Updated draft status with pause confirmation
    """
    try:
        logger.info(
            f"Draft pause request",
            extra={
                "user_id": str(current_user.user_id),
                "league_id": league_id,
            }
        )

        # Validate league and permissions
        league = db.query(League).filter(
            League.league_id == league_id
        ).first()

        if not league:
            raise HTTPException(
                status_code=404,
                detail=f"League {league_id} not found"
            )

        if league.commissioner_id != current_user.user_id:
            raise HTTPException(
                status_code=403,
                detail="Only the league commissioner can pause a draft"
            )

        # Get draft timer
        draft_timer_service = get_draft_timer_service()
        draft_timer = draft_timer_service.get_draft_timer(league_id)

        if not draft_timer:
            raise HTTPException(
                status_code=404,
                detail="No active draft found for this league"
            )

        # Pause the draft
        success = await draft_timer.pause_draft()

        if not success:
            raise HTTPException(
                status_code=400,
                detail="Cannot pause draft in its current state"
            )

        # Get updated status
        timer_status = draft_timer.get_timer_status()

        logger.info(
            f"Draft paused successfully",
            extra={
                "user_id": str(current_user.user_id),
                "league_id": league_id,
                "time_remaining": timer_status["time_remaining"],
            }
        )

        return StandardResponse(
            success=True,
            data=timer_status,
            message="Draft paused successfully"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Failed to pause draft",
            extra={
                "user_id": str(current_user.user_id),
                "league_id": league_id,
                "error": str(e),
            }
        )

        raise HTTPException(
            status_code=500,
            detail="Failed to pause draft. Please try again later."
        )


@router.post("/draft/{league_id}/resume", response_model=StandardResponse[dict])
async def resume_draft(
    league_id: str = Path(..., description="League ID to resume draft for"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> StandardResponse[dict]:
    """
    Resume a paused draft.

    Only the league commissioner can resume a draft.
    The timer will continue with the remaining time from when it was paused.

    **Requirements:**
    - User must be league commissioner
    - Draft must be paused

    **Returns:**
    - Updated draft status with resume confirmation
    """
    try:
        logger.info(
            f"Draft resume request",
            extra={
                "user_id": str(current_user.user_id),
                "league_id": league_id,
            }
        )

        # Validate league and permissions
        league = db.query(League).filter(
            League.league_id == league_id
        ).first()

        if not league:
            raise HTTPException(
                status_code=404,
                detail=f"League {league_id} not found"
            )

        if league.commissioner_id != current_user.user_id:
            raise HTTPException(
                status_code=403,
                detail="Only the league commissioner can resume a draft"
            )

        # Get draft timer
        draft_timer_service = get_draft_timer_service()
        draft_timer = draft_timer_service.get_draft_timer(league_id)

        if not draft_timer:
            raise HTTPException(
                status_code=404,
                detail="No active draft found for this league"
            )

        # Resume the draft
        success = await draft_timer.resume_draft()

        if not success:
            raise HTTPException(
                status_code=400,
                detail="Cannot resume draft in its current state"
            )

        # Get updated status
        timer_status = draft_timer.get_timer_status()

        logger.info(
            f"Draft resumed successfully",
            extra={
                "user_id": str(current_user.user_id),
                "league_id": league_id,
                "time_remaining": timer_status["time_remaining"],
            }
        )

        return StandardResponse(
            success=True,
            data=timer_status,
            message="Draft resumed successfully"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Failed to resume draft",
            extra={
                "user_id": str(current_user.user_id),
                "league_id": league_id,
                "error": str(e),
            }
        )

        raise HTTPException(
            status_code=500,
            detail="Failed to resume draft. Please try again later."
        )