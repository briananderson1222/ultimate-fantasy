"""
Waiver API endpoints for Ultimate Fantasy Platform
Provides REST API for waiver wire claims, drops, and priority management
"""

from datetime import datetime, date
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field, validator
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from ...infrastructure.database.session_factory import get_db_session
from ...domains.trading.services.trading_service import TradingService
from ...domains.leagues.services.league_service import LeagueService
from ...domains.shared.exceptions import (
    WaiverNotFoundError, LeagueNotFoundError, UserNotFoundError,
    PlayerNotFoundError, InsufficientPermissionsError, InvalidWaiverError,
    WaiverExpiredError, WaiverAlreadyProcessedError, InsufficientFundsError,
    RosterFullError, PlayerNotAvailableError, WaiverPeriodClosedError
)
from ..middleware.auth import get_current_user
from ..models.response import APIResponse, ErrorResponse
from ...models.trade import WaiverClaim, WaiverStatus, WaiverType
from ..deps import get_trading_service, get_league_service


router = APIRouter(prefix="/api/v1/waivers", tags=["waivers"])


# Pydantic Models for Request/Response
class WaiverClaimRequest(BaseModel):
    league_id: str = Field(..., description="League ID")
    add_player_id: str = Field(..., description="Player to add")
    drop_player_id: Optional[str] = Field(None, description="Player to drop (if roster full)")
    waiver_type: str = Field(default="standard", description="Type of waiver claim")
    bid_amount: Optional[float] = Field(None, ge=0, description="Bid amount for FAAB leagues")
    priority: int = Field(default=1, ge=1, le=10, description="Claim priority (1=highest)")

    @validator('waiver_type')
    def validate_waiver_type(cls, v):
        valid_types = ['standard', 'faab', 'free_agent']
        if v.lower() not in valid_types:
            raise ValueError(f"Waiver type must be one of: {valid_types}")
        return v.lower()


class UpdateWaiverRequest(BaseModel):
    drop_player_id: Optional[str] = Field(None, description="Update drop player")
    bid_amount: Optional[float] = Field(None, ge=0, description="Update bid amount")
    priority: Optional[int] = Field(None, ge=1, le=10, description="Update priority")


class BulkWaiverRequest(BaseModel):
    claims: List[WaiverClaimRequest] = Field(..., description="Multiple waiver claims")

    @validator('claims')
    def validate_claims_not_empty(cls, v):
        if not v or len(v) == 0:
            raise ValueError("At least one claim must be provided")
        if len(v) > 10:
            raise ValueError("Maximum 10 claims allowed per request")
        return v


class WaiverPlayerResponse(BaseModel):
    player_id: str
    player_name: str
    team: str
    position: str
    projected_points: float
    ownership_percentage: float
    waiver_status: str
    available_at: Optional[datetime]
    injury_status: Optional[str]

    class Config:
        from_attributes = True


class WaiverClaimResponse(BaseModel):
    claim_id: str
    league_id: str
    team_id: str
    add_player: WaiverPlayerResponse
    drop_player: Optional[WaiverPlayerResponse]
    waiver_type: str
    bid_amount: Optional[float]
    priority: int
    status: str
    submitted_at: datetime
    processed_at: Optional[datetime]
    process_order: Optional[int]
    success: Optional[bool]
    failure_reason: Optional[str]

    class Config:
        from_attributes = True


class WaiverPriorityResponse(BaseModel):
    team_id: str
    team_name: str
    owner_name: str
    priority_order: int
    waiver_budget: Optional[float]
    claims_this_week: int
    successful_claims: int

    class Config:
        from_attributes = True


class WaiverPeriodResponse(BaseModel):
    league_id: str
    current_week: int
    waiver_period_start: datetime
    waiver_period_end: datetime
    is_waiver_period_active: bool
    next_process_time: Optional[datetime]
    total_claims: int
    processed_claims: int

    class Config:
        from_attributes = True


class WaiverReportResponse(BaseModel):
    week: int
    process_date: datetime
    total_claims: int
    successful_claims: int
    failed_claims: int
    total_faab_spent: Optional[float]
    claims_by_team: List[Dict[str, Any]]
    player_movements: List[Dict[str, Any]]

    class Config:
        from_attributes = True


# Waiver Claim Endpoints
@router.post("/claims", response_model=APIResponse[WaiverClaimResponse])
async def submit_waiver_claim(
    request: WaiverClaimRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db_session),
    trading_service: TradingService = Depends(get_trading_service),
    league_service: LeagueService = Depends(get_league_service),
):
    """Submit a waiver claim for a player"""
    try:
        # Verify user is in the league and get their team
        team = league_service.get_user_team_in_league(
            request.league_id, current_user["user_id"], db
        )

        claim = trading_service.submit_waiver_claim(
            league_id=request.league_id,
            team_id=str(team.team_id),
            add_player_id=request.add_player_id,
            drop_player_id=request.drop_player_id,
            waiver_type=request.waiver_type,
            bid_amount=request.bid_amount,
            priority=request.priority,
            db=db
        )

        return APIResponse(
            success=True,
            data=WaiverClaimResponse.from_orm(claim),
            message="Waiver claim submitted successfully"
        )

    except LeagueNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="League not found"
        )
    except UserNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Team not found in league"
        )
    except PlayerNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except PlayerNotAvailableError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except InvalidWaiverError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except InsufficientFundsError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except WaiverPeriodClosedError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Waiver period is currently closed"
        )


@router.post("/claims/bulk", response_model=APIResponse[List[WaiverClaimResponse]])
async def submit_bulk_waiver_claims(
    request: BulkWaiverRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db_session),
    trading_service: TradingService = Depends(get_trading_service),
    league_service: LeagueService = Depends(get_league_service),
):
    """Submit multiple waiver claims at once"""
    try:
        claims = []

        for claim_request in request.claims:
            # Verify user is in the league and get their team
            team = league_service.get_user_team_in_league(
                claim_request.league_id, current_user["user_id"], db
            )

            claim = trading_service.submit_waiver_claim(
                league_id=claim_request.league_id,
                team_id=str(team.team_id),
                add_player_id=claim_request.add_player_id,
                drop_player_id=claim_request.drop_player_id,
                waiver_type=claim_request.waiver_type,
                bid_amount=claim_request.bid_amount,
                priority=claim_request.priority,
                db=db
            )
            claims.append(claim)

        return APIResponse(
            success=True,
            data=[WaiverClaimResponse.from_orm(claim) for claim in claims],
            message=f"{len(claims)} waiver claims submitted successfully"
        )

    except (LeagueNotFoundError, UserNotFoundError, PlayerNotFoundError,
            PlayerNotAvailableError, InvalidWaiverError, InsufficientFundsError,
            WaiverPeriodClosedError) as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/claims/{claim_id}", response_model=APIResponse[WaiverClaimResponse])
async def get_waiver_claim(
    claim_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db_session),
    trading_service: TradingService = Depends(get_trading_service),
    league_service: LeagueService = Depends(get_league_service),
):
    """Get waiver claim details by ID"""
    try:
        claim = trading_service.get_waiver_claim(claim_id, db)

        # Verify user has access (own claim or league member)
        team = trading_service.get_team(claim.team_id, db)
        if team.user_id != current_user["user_id"]:
            if not league_service.is_user_in_league(claim.league_id, current_user["user_id"], db):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Access denied"
                )

        return APIResponse(
            success=True,
            data=WaiverClaimResponse.from_orm(claim),
            message="Waiver claim retrieved successfully"
        )

    except WaiverNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Waiver claim not found"
        )


@router.put("/claims/{claim_id}", response_model=APIResponse[WaiverClaimResponse])
async def update_waiver_claim(
    claim_id: str,
    request: UpdateWaiverRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db_session),
    trading_service: TradingService = Depends(get_trading_service),
    league_service: LeagueService = Depends(get_league_service),
):
    """Update a pending waiver claim"""
    try:
        claim = trading_service.get_waiver_claim(claim_id, db)

        # Verify user owns this claim
        team = trading_service.get_team(claim.team_id, db)
        if team.user_id != current_user["user_id"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only update your own waiver claims"
            )

        update_data = request.dict(exclude_unset=True)
        updated_claim = trading_service.update_waiver_claim(claim_id, update_data, db)

        return APIResponse(
            success=True,
            data=WaiverClaimResponse.from_orm(updated_claim),
            message="Waiver claim updated successfully"
        )

    except WaiverNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Waiver claim not found"
        )
    except WaiverAlreadyProcessedError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot update processed waiver claim"
        )
    except InvalidWaiverError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.delete("/claims/{claim_id}")
async def cancel_waiver_claim(
    claim_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db_session),
    trading_service: TradingService = Depends(get_trading_service),
    league_service: LeagueService = Depends(get_league_service),
):
    """Cancel a pending waiver claim"""
    try:
        claim = trading_service.get_waiver_claim(claim_id, db)

        # Verify user owns this claim
        team = trading_service.get_team(claim.team_id, db)
        if team.user_id != current_user["user_id"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only cancel your own waiver claims"
            )

        trading_service.cancel_waiver_claim(claim_id, db)

        return APIResponse(
            success=True,
            data=None,
            message="Waiver claim cancelled successfully"
        )

    except WaiverNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Waiver claim not found"
        )
    except WaiverAlreadyProcessedError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot cancel processed waiver claim"
        )


# Waiver Wire and Available Players
@router.get("/league/{league_id}/available", response_model=APIResponse[List[WaiverPlayerResponse]])
async def get_available_players(
    league_id: str,
    position: Optional[str] = Query(None, description="Filter by position"),
    search: Optional[str] = Query(None, description="Search player names"),
    sort_by: str = Query(default="projected_points", description="Sort criteria"),
    limit: int = Query(default=50, le=200, description="Maximum number of results"),
    offset: int = Query(default=0, ge=0, description="Number of results to skip"),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db_session),
    trading_service: TradingService = Depends(get_trading_service),
    league_service: LeagueService = Depends(get_league_service),
):
    """Get available players on the waiver wire"""
    try:
        # Verify user is in the league
        if not league_service.is_user_in_league(league_id, current_user["user_id"], db):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied - not a league member"
            )

        players = trading_service.get_available_players(
            league_id=league_id,
            position=position,
            search=search,
            sort_by=sort_by,
            limit=limit,
            offset=offset,
            db=db
        )

        return APIResponse(
            success=True,
            data=[WaiverPlayerResponse.from_orm(player) for player in players],
            message="Available players retrieved successfully"
        )

    except LeagueNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="League not found"
        )


@router.get("/league/{league_id}/claims", response_model=APIResponse[List[WaiverClaimResponse]])
async def get_league_waiver_claims(
    league_id: str,
    status_filter: Optional[str] = Query(None, description="Filter by claim status"),
    team_id: Optional[str] = Query(None, description="Filter by team"),
    week: Optional[int] = Query(None, description="Filter by week"),
    limit: int = Query(default=50, le=200, description="Maximum number of results"),
    offset: int = Query(default=0, ge=0, description="Number of results to skip"),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db_session),
    trading_service: TradingService = Depends(get_trading_service),
    league_service: LeagueService = Depends(get_league_service),
):
    """Get waiver claims for a league"""
    try:
        # Verify user is in the league
        if not league_service.is_user_in_league(league_id, current_user["user_id"], db):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied - not a league member"
            )

        claims = trading_service.get_league_waiver_claims(
            league_id=league_id,
            status_filter=status_filter,
            team_id=team_id,
            week=week,
            limit=limit,
            offset=offset,
            db=db
        )

        return APIResponse(
            success=True,
            data=[WaiverClaimResponse.from_orm(claim) for claim in claims],
            message="League waiver claims retrieved successfully"
        )

    except LeagueNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="League not found"
        )


@router.get("/user/claims", response_model=APIResponse[List[WaiverClaimResponse]])
async def get_user_waiver_claims(
    league_id: Optional[str] = Query(None, description="Filter by league"),
    status_filter: Optional[str] = Query(None, description="Filter by claim status"),
    limit: int = Query(default=50, le=200, description="Maximum number of results"),
    offset: int = Query(default=0, ge=0, description="Number of results to skip"),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db_session),
    trading_service: TradingService = Depends(get_trading_service),
):
    """Get all waiver claims for the current user"""
    try:
        claims = trading_service.get_user_waiver_claims(
            user_id=current_user["user_id"],
            league_id=league_id,
            status_filter=status_filter,
            limit=limit,
            offset=offset,
            db=db
        )

        return APIResponse(
            success=True,
            data=[WaiverClaimResponse.from_orm(claim) for claim in claims],
            message="User waiver claims retrieved successfully"
        )

    except SQLAlchemyError:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database error occurred"
        )


# Waiver Priority and Budget Management
@router.get("/league/{league_id}/priority", response_model=APIResponse[List[WaiverPriorityResponse]])
async def get_waiver_priority_order(
    league_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db_session),
    trading_service: TradingService = Depends(get_trading_service),
    league_service: LeagueService = Depends(get_league_service),
):
    """Get waiver priority order for the league"""
    try:
        # Verify user is in the league
        if not league_service.is_user_in_league(league_id, current_user["user_id"], db):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied - not a league member"
            )

        priority_order = trading_service.get_waiver_priority_order(league_id, db)

        return APIResponse(
            success=True,
            data=[WaiverPriorityResponse.from_orm(team) for team in priority_order],
            message="Waiver priority order retrieved successfully"
        )

    except LeagueNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="League not found"
        )


@router.get("/league/{league_id}/period", response_model=APIResponse[WaiverPeriodResponse])
async def get_waiver_period_info(
    league_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db_session),
    trading_service: TradingService = Depends(get_trading_service),
    league_service: LeagueService = Depends(get_league_service),
):
    """Get current waiver period information"""
    try:
        # Verify user is in the league
        if not league_service.is_user_in_league(league_id, current_user["user_id"], db):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied - not a league member"
            )

        period_info = trading_service.get_waiver_period_info(league_id, db)

        return APIResponse(
            success=True,
            data=WaiverPeriodResponse.from_orm(period_info),
            message="Waiver period information retrieved successfully"
        )

    except LeagueNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="League not found"
        )


# Commissioner Waiver Management
@router.post("/league/{league_id}/process")
async def process_waivers(
    league_id: str,
    week: Optional[int] = Query(None, description="Week to process (defaults to current)"),
    force: bool = Query(default=False, description="Force process outside normal schedule"),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db_session),
    trading_service: TradingService = Depends(get_trading_service),
    league_service: LeagueService = Depends(get_league_service),
):
    """Process pending waiver claims (commissioner only)"""
    try:
        # Verify user is commissioner
        if not league_service.is_commissioner(league_id, current_user["user_id"], db):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only commissioners can manually process waivers"
            )

        results = trading_service.process_waiver_claims(
            league_id=league_id,
            week=week,
            force=force,
            db=db
        )

        return APIResponse(
            success=True,
            data=results,
            message="Waiver claims processed successfully"
        )

    except LeagueNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="League not found"
        )
    except InsufficientPermissionsError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only commissioners can process waivers"
        )
    except WaiverPeriodClosedError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot process waivers outside the waiver period"
        )


@router.post("/league/{league_id}/reset-priority")
async def reset_waiver_priority(
    league_id: str,
    method: str = Query(..., description="reset method: reverse_standings, random, manual"),
    manual_order: Optional[List[str]] = Query(None, description="Manual team order for manual method"),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db_session),
    trading_service: TradingService = Depends(get_trading_service),
    league_service: LeagueService = Depends(get_league_service),
):
    """Reset waiver priority order (commissioner only)"""
    try:
        # Verify user is commissioner
        if not league_service.is_commissioner(league_id, current_user["user_id"], db):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only commissioners can reset waiver priority"
            )

        trading_service.reset_waiver_priority(
            league_id=league_id,
            method=method,
            manual_order=manual_order,
            db=db
        )

        return APIResponse(
            success=True,
            data=None,
            message="Waiver priority reset successfully"
        )

    except LeagueNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="League not found"
        )
    except InsufficientPermissionsError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only commissioners can reset waiver priority"
        )


@router.get("/league/{league_id}/reports", response_model=APIResponse[List[WaiverReportResponse]])
async def get_waiver_reports(
    league_id: str,
    start_week: Optional[int] = Query(None, description="Start week for reports"),
    end_week: Optional[int] = Query(None, description="End week for reports"),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db_session),
    trading_service: TradingService = Depends(get_trading_service),
    league_service: LeagueService = Depends(get_league_service),
):
    """Get waiver activity reports (commissioner only)"""
    try:
        # Verify user is commissioner
        if not league_service.is_commissioner(league_id, current_user["user_id"], db):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only commissioners can view waiver reports"
            )

        reports = trading_service.get_waiver_reports(
            league_id=league_id,
            start_week=start_week,
            end_week=end_week,
            db=db
        )

        return APIResponse(
            success=True,
            data=[WaiverReportResponse.from_orm(report) for report in reports],
            message="Waiver reports retrieved successfully"
        )

    except LeagueNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="League not found"
        )
    except InsufficientPermissionsError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only commissioners can view waiver reports"
        )
