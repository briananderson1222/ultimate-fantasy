"""
League API endpoints for Ultimate Fantasy Platform
Provides REST API for league CRUD operations, membership management, and settings
"""

from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field, validator
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from api.deps import get_league_service
from api.middleware.auth import get_current_user
from api.models.response import APIResponse
from domains.leagues.services.league_service import LeagueService
from domains.shared.enums import LeagueStatus
from domains.shared.exceptions import (
    AlreadyInLeagueError,
    CommissionerOnlyError,
    InvalidInviteCodeError,
    LeagueFullError,
    LeagueNotFoundError,
    LeagueValidationError,
    UserNotFoundError,
)
from infrastructure.database.session_factory import get_db_session

router = APIRouter(prefix="/api/v1/leagues", tags=["leagues"])


# Pydantic Models for Request/Response
class CreateLeagueRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=100, description="League name")
    sport: str = Field(..., description="Sport type (mlb, nfl, nba, nhl)")
    league_type: str = Field(..., description="League type (standard, keeper, dynasty)")
    season: str = Field(..., description="Season year (e.g., '2024')")
    max_teams: int = Field(default=12, ge=4, le=20, description="Maximum teams allowed")
    custom_settings: dict[str, Any] | None = Field(
        default=None, description="Custom league settings"
    )

    @validator("sport")
    def validate_sport(cls, v):
        valid_sports = ["mlb", "nfl", "nba", "nhl"]
        if v.lower() not in valid_sports:
            raise ValueError(f"Sport must be one of: {valid_sports}")
        return v.lower()

    @validator("league_type")
    def validate_league_type(cls, v):
        valid_types = ["standard", "keeper", "dynasty"]
        if v.lower() not in valid_types:
            raise ValueError(f"League type must be one of: {valid_types}")
        return v.lower()


class UpdateLeagueRequest(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=100)
    max_teams: int | None = Field(None, ge=4, le=20)
    custom_settings: dict[str, Any] | None = None
    scoring_rules: dict[str, Any] | None = None
    roster_settings: dict[str, Any] | None = None


class JoinLeagueRequest(BaseModel):
    invite_code: str = Field(
        ..., min_length=8, max_length=8, description="8-character invite code"
    )
    team_name: str = Field(..., min_length=1, max_length=50, description="Team name")


class UpdateTeamRequest(BaseModel):
    team_name: str | None = Field(None, min_length=1, max_length=50)
    team_logo_url: str | None = None
    team_motto: str | None = Field(None, max_length=200)


class TransferCommissionerRequest(BaseModel):
    new_commissioner_user_id: str = Field(
        ..., description="User ID of new commissioner"
    )


class LeagueResponse(BaseModel):
    league_id: str
    name: str
    sport: str
    league_type: str
    season: str
    status: str
    commissioner_id: str
    max_teams: int
    current_teams: int
    invite_code: str
    created_at: datetime
    draft_date: datetime | None
    season_start_date: datetime | None
    season_end_date: datetime | None
    scoring_rules: dict[str, Any]
    roster_settings: dict[str, Any]

    class Config:
        from_attributes = True


class TeamResponse(BaseModel):
    team_id: str
    league_id: str
    user_id: str
    team_name: str
    team_logo_url: str | None
    team_motto: str | None
    wins: int
    losses: int
    ties: int
    points_for: float
    points_against: float
    draft_position: int | None
    joined_at: datetime

    class Config:
        from_attributes = True


class LeagueStandingsResponse(BaseModel):
    teams: list[TeamResponse]
    season_stats: dict[str, Any]


class LeagueMemberResponse(BaseModel):
    user_id: str
    username: str
    team: TeamResponse
    is_commissioner: bool
    is_active: bool


# League CRUD Endpoints
@router.post("/", response_model=APIResponse[LeagueResponse])
async def create_league(
    request: CreateLeagueRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db_session),
    league_service: LeagueService = Depends(get_league_service),
):
    """Create a new fantasy league with the current user as commissioner"""
    try:
        league = league_service.create_league(
            commissioner_id=current_user["user_id"],
            name=request.name,
            sport=request.sport,
            league_type=request.league_type,
            season=request.season,
            max_teams=request.max_teams,
            custom_settings=request.custom_settings,
            db=db,
        )

        return APIResponse(
            success=True,
            data=LeagueResponse.from_orm(league),
            message="League created successfully",
        )

    except LeagueValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except SQLAlchemyError:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database error occurred",
        )


@router.get("/{league_id}", response_model=APIResponse[LeagueResponse])
async def get_league(
    league_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db_session),
    league_service: LeagueService = Depends(get_league_service),
):
    """Get league details by ID"""
    try:
        league = league_service.get_league(league_id, db)

        # Check if user is a member or if league is public
        if not league_service.is_user_in_league(
            league_id=league_id, user_id=current_user["user_id"], db=db
        ):
            if league.status != LeagueStatus.RECRUITING:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Access denied to private league",
                )

        return APIResponse(
            success=True,
            data=LeagueResponse.from_orm(league),
            message="League retrieved successfully",
        )

    except LeagueNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="League not found"
        )


@router.put("/{league_id}", response_model=APIResponse[LeagueResponse])
async def update_league(
    league_id: str,
    request: UpdateLeagueRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db_session),
    league_service: LeagueService = Depends(get_league_service),
):
    """Update league settings (commissioner only)"""
    try:
        # Verify commissioner permissions
        if not league_service.is_commissioner(
            league_id=league_id, user_id=current_user["user_id"], db=db
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only commissioners can update league settings",
            )

        update_data = request.dict(exclude_unset=True)
        league = league_service.update_league_settings(
            league_id=league_id,
            user_id=current_user["user_id"],
            updates=update_data,
            db=db,
        )

        return APIResponse(
            success=True,
            data=LeagueResponse.from_orm(league),
            message="League updated successfully",
        )

    except LeagueNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="League not found"
        )
    except CommissionerOnlyError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only commissioners can perform this action",
        )
    except LeagueValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.delete("/{league_id}")
async def delete_league(
    league_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db_session),
    league_service: LeagueService = Depends(get_league_service),
):
    """Delete a league (commissioner only, before draft)"""
    try:
        if not league_service.is_commissioner(
            league_id=league_id, user_id=current_user["user_id"], db=db
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only commissioners can delete leagues",
            )

        league_service.delete_league(
            league_id=league_id, user_id=current_user["user_id"], db=db
        )

        return APIResponse(
            success=True, data=None, message="League deleted successfully"
        )

    except LeagueNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="League not found"
        )
    except CommissionerOnlyError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot delete league after draft has started",
        )


# League Membership Endpoints
@router.post("/{league_id}/join", response_model=APIResponse[TeamResponse])
async def join_league(
    league_id: str,
    request: JoinLeagueRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db_session),
    league_service: LeagueService = Depends(get_league_service),
):
    """Join a league using invite code"""
    try:
        team = league_service.join_league(
            league_id=league_id,
            user_id=current_user["user_id"],
            invite_code=request.invite_code,
            team_name=request.team_name,
            db=db,
        )

        return APIResponse(
            success=True,
            data=TeamResponse.from_orm(team),
            message="Successfully joined league",
        )

    except LeagueNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="League not found"
        )
    except InvalidInviteCodeError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid invite code"
        )
    except LeagueFullError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="League is full"
        )
    except AlreadyInLeagueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Already a member of this league",
        )


@router.post("/{league_id}/leave")
async def leave_league(
    league_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db_session),
    league_service: LeagueService = Depends(get_league_service),
):
    """Leave a league (not allowed after draft starts)"""
    try:
        league_service.leave_league(
            league_id=league_id, user_id=current_user["user_id"], db=db
        )

        return APIResponse(success=True, data=None, message="Successfully left league")

    except LeagueNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="League not found"
        )
    except CommissionerOnlyError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot leave league after draft has started",
        )


@router.get(
    "/{league_id}/members", response_model=APIResponse[list[LeagueMemberResponse]]
)
async def get_league_members(
    league_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db_session),
    league_service: LeagueService = Depends(get_league_service),
):
    """Get all league members and their teams"""
    try:
        # Verify user is in league
        if not league_service.is_user_in_league(
            league_id=league_id, user_id=current_user["user_id"], db=db
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied - not a league member",
            )

        members = league_service.get_league_members(league_id=league_id, db=db)

        return APIResponse(
            success=True,
            data=[LeagueMemberResponse.from_orm(member) for member in members],
            message="League members retrieved successfully",
        )

    except LeagueNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="League not found"
        )


@router.delete("/{league_id}/members/{user_id}")
async def remove_member(
    league_id: str,
    user_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db_session),
    league_service: LeagueService = Depends(get_league_service),
):
    """Remove a member from league (commissioner only, before draft)"""
    try:
        if not league_service.is_commissioner(
            league_id=league_id, user_id=current_user["user_id"], db=db
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only commissioners can remove members",
            )

        league_service.remove_member(
            league_id=league_id,
            requester_id=current_user["user_id"],
            user_id=user_id,
            db=db,
        )

        return APIResponse(
            success=True, data=None, message="Member removed successfully"
        )

    except LeagueNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="League not found"
        )
    except UserNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found in league"
        )
    except CommissionerOnlyError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot remove members after draft has started",
        )


# Team Management Endpoints
@router.put("/{league_id}/team", response_model=APIResponse[TeamResponse])
async def update_team(
    league_id: str,
    request: UpdateTeamRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db_session),
    league_service: LeagueService = Depends(get_league_service),
):
    """Update user's team in the league"""
    try:
        team = league_service.get_user_team_in_league(
            league_id=league_id, user_id=current_user["user_id"], db=db
        )

        update_data = request.dict(exclude_unset=True)
        updated_team = league_service.update_team(
            team_id=str(team.team_id), updates=update_data, db=db
        )

        return APIResponse(
            success=True,
            data=TeamResponse.from_orm(updated_team),
            message="Team updated successfully",
        )

    except LeagueNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="League not found"
        )
    except UserNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Team not found in league"
        )


@router.get(
    "/{league_id}/standings", response_model=APIResponse[LeagueStandingsResponse]
)
async def get_league_standings(
    league_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db_session),
    league_service: LeagueService = Depends(get_league_service),
):
    """Get league standings and season statistics"""
    try:
        # Verify user is in league
        if not league_service.is_user_in_league(
            league_id=league_id, user_id=current_user["user_id"], db=db
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied - not a league member",
            )

        standings = league_service.get_league_standings(league_id=league_id, db=db)

        return APIResponse(
            success=True,
            data=standings,
            message="League standings retrieved successfully",
        )

    except LeagueNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="League not found"
        )


# Commissioner Actions
@router.post("/{league_id}/transfer-commissioner")
async def transfer_commissioner(
    league_id: str,
    request: TransferCommissionerRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db_session),
    league_service: LeagueService = Depends(get_league_service),
):
    """Transfer commissioner role to another league member"""
    try:
        if not league_service.is_commissioner(
            league_id=league_id, user_id=current_user["user_id"], db=db
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only commissioners can transfer commissioner role",
            )

        league_service.transfer_commissioner(
            league_id=league_id,
            current_commissioner_id=current_user["user_id"],
            new_commissioner_user_id=request.new_commissioner_user_id,
            db=db,
        )

        return APIResponse(
            success=True,
            data=None,
            message="Commissioner role transferred successfully",
        )

    except LeagueNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="League not found"
        )
    except UserNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="New commissioner not found in league",
        )
    except CommissionerOnlyError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only commissioners can perform this action",
        )


@router.post("/{league_id}/regenerate-invite-code")
async def regenerate_invite_code(
    league_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db_session),
    league_service: LeagueService = Depends(get_league_service),
):
    """Regenerate league invite code (commissioner only)"""
    try:
        if not league_service.is_commissioner(
            league_id=league_id, user_id=current_user["user_id"], db=db
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only commissioners can regenerate invite codes",
            )

        new_code = league_service.regenerate_invite_code(
            league_id=league_id, user_id=current_user["user_id"], db=db
        )

        return APIResponse(
            success=True,
            data={"invite_code": new_code},
            message="Invite code regenerated successfully",
        )

    except LeagueNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="League not found"
        )
    except CommissionerOnlyError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only commissioners can perform this action",
        )


# League Discovery
@router.get("/", response_model=APIResponse[list[LeagueResponse]])
async def get_user_leagues(
    current_user: dict = Depends(get_current_user),
    sport: str | None = Query(None, description="Filter by sport"),
    status: str | None = Query(None, description="Filter by league status"),
    db: Session = Depends(get_db_session),
    league_service: LeagueService = Depends(get_league_service),
):
    """Get all leagues the current user is a member of"""
    try:
        leagues = league_service.get_user_leagues(
            user_id=current_user["user_id"],
            sport=sport,
            status=status,
            db=db,
        )

        return APIResponse(
            success=True,
            data=[LeagueResponse.from_orm(league) for league in leagues],
            message="User leagues retrieved successfully",
        )

    except SQLAlchemyError:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database error occurred",
        )


@router.get("/public", response_model=APIResponse[list[LeagueResponse]])
async def get_public_leagues(
    sport: str | None = Query(None, description="Filter by sport"),
    league_type: str | None = Query(None, description="Filter by league type"),
    limit: int = Query(default=20, le=100, description="Maximum number of results"),
    offset: int = Query(default=0, ge=0, description="Number of results to skip"),
    db: Session = Depends(get_db_session),
    league_service: LeagueService = Depends(get_league_service),
):
    """Get public leagues available for joining"""
    try:
        leagues = league_service.get_public_leagues(
            sport=sport,
            league_type=league_type,
            limit=limit,
            offset=offset,
            db=db,
        )

        return APIResponse(
            success=True,
            data=[LeagueResponse.from_orm(league) for league in leagues],
            message="Public leagues retrieved successfully",
        )

    except SQLAlchemyError:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database error occurred",
        )
