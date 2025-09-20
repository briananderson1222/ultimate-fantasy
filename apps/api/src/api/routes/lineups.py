"""
Lineup API endpoints for Ultimate Fantasy Platform
Provides REST API for lineup management, optimization, and validation
"""

from datetime import datetime, date
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field, validator
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from ...infrastructure.database.session_factory import get_db_session
from ...domains.lineups.services.lineup_service import LineupService
from ...domains.leagues.services.league_service import LeagueService
from ...domains.shared.exceptions import (
    LineupNotFoundError, LeagueNotFoundError, UserNotFoundError,
    LineupValidationError, OptimisticLockError, PlayerNotFoundError,
    InsufficientPermissionsError, InvalidRosterError, DeadlinePassedError
)
from ..middleware.auth import get_current_user
from ..models.response import APIResponse, ErrorResponse
from ...models.lineup import Lineup, LineupPlayer, LineupStatus


router = APIRouter(prefix="/api/v1/lineups", tags=["lineups"])

lineup_service = LineupService()
league_service = LeagueService()


# Pydantic Models for Request/Response
class LineupPlayerRequest(BaseModel):
    player_id: str = Field(..., description="Player ID")
    position: str = Field(..., description="Position in lineup (QB, RB1, WR2, etc.)")
    is_starter: bool = Field(default=True, description="Whether player is starting")
    bench_position: Optional[int] = Field(None, description="Bench position if not starting")


class UpdateLineupRequest(BaseModel):
    players: List[LineupPlayerRequest] = Field(..., description="Complete lineup configuration")
    expected_version: Optional[int] = Field(None, description="Expected version for optimistic locking")

    @validator('players')
    def validate_players_not_empty(cls, v):
        if not v or len(v) == 0:
            raise ValueError("Lineup must contain at least one player")
        return v


class OptimizeLineupRequest(BaseModel):
    criteria: str = Field(default="projected_points", description="Optimization criteria")
    constraints: Optional[Dict[str, Any]] = Field(None, description="Additional constraints")
    preserve_starters: bool = Field(default=False, description="Keep current starters if possible")

    @validator('criteria')
    def validate_criteria(cls, v):
        valid_criteria = ['projected_points', 'consistency', 'upside', 'value']
        if v not in valid_criteria:
            raise ValueError(f"Criteria must be one of: {valid_criteria}")
        return v


class LineupPlayerResponse(BaseModel):
    player_id: str
    player_name: str
    team: str
    position: str
    lineup_position: str
    is_starter: bool
    bench_position: Optional[int]
    projected_points: float
    actual_points: Optional[float]
    game_status: str
    injury_status: Optional[str]
    opponent: Optional[str]
    game_time: Optional[datetime]

    class Config:
        from_attributes = True


class LineupResponse(BaseModel):
    lineup_id: str
    team_id: str
    league_id: str
    week: int
    season: str
    status: str
    players: List[LineupPlayerResponse]
    projected_total: float
    actual_total: Optional[float]
    version: int
    lineup_deadline: datetime
    last_updated: datetime
    is_locked: bool
    is_optimal: bool
    validation_errors: List[str]

    class Config:
        from_attributes = True


class LineupValidationResponse(BaseModel):
    is_valid: bool
    errors: List[str]
    warnings: List[str]
    missing_positions: List[str]
    invalid_positions: List[str]
    bench_violations: List[str]
    salary_cap_issues: Optional[Dict[str, Any]]

    class Config:
        from_attributes = True


class LineupOptimizationResponse(BaseModel):
    original_lineup: LineupResponse
    optimized_lineup: LineupResponse
    improvements: Dict[str, Any]
    changes_made: List[Dict[str, Any]]
    projected_gain: float

    class Config:
        from_attributes = True


class LineupHistoryResponse(BaseModel):
    lineup_id: str
    version: int
    changes: List[Dict[str, Any]]
    changed_by: str
    changed_at: datetime
    reason: Optional[str]

    class Config:
        from_attributes = True


# Lineup Management Endpoints
@router.get("/team/{team_id}/week/{week}", response_model=APIResponse[LineupResponse])
async def get_lineup(
    team_id: str,
    week: int,
    season: Optional[str] = Query(None, description="Season year (defaults to current)"),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    """Get lineup for a specific team and week"""
    try:
        # Verify user has access to this team
        team = lineup_service.get_team(team_id, db)
        if team.user_id != current_user["user_id"]:
            # Check if user is in the league (for viewing other lineups)
            if not league_service.is_user_in_league(team.league_id, current_user["user_id"], db):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Access denied"
                )

        lineup = lineup_service.get_lineup(
            team_id=team_id,
            week=week,
            season=season,
            db=db
        )

        return APIResponse(
            success=True,
            data=LineupResponse.from_orm(lineup),
            message="Lineup retrieved successfully"
        )

    except LineupNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lineup not found"
        )
    except UserNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Team not found"
        )


@router.put("/team/{team_id}/week/{week}", response_model=APIResponse[LineupResponse])
async def update_lineup(
    team_id: str,
    week: int,
    request: UpdateLineupRequest,
    season: Optional[str] = Query(None, description="Season year (defaults to current)"),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    """Update lineup for a specific team and week"""
    try:
        # Verify user owns this team
        team = lineup_service.get_team(team_id, db)
        if team.user_id != current_user["user_id"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only update your own lineups"
            )

        # Get or create lineup
        try:
            lineup = lineup_service.get_lineup(team_id, week, season, db)
        except LineupNotFoundError:
            lineup = lineup_service.create_lineup(team_id, week, season, db)

        # Convert request to lineup players
        lineup_players = [
            {
                "player_id": p.player_id,
                "position": p.position,
                "is_starter": p.is_starter,
                "bench_position": p.bench_position
            }
            for p in request.players
        ]

        updated_lineup = lineup_service.update_lineup(
            lineup_id=str(lineup.lineup_id),
            lineup_players=lineup_players,
            user_id=current_user["user_id"],
            expected_version=request.expected_version,
            db=db
        )

        return APIResponse(
            success=True,
            data=LineupResponse.from_orm(updated_lineup),
            message="Lineup updated successfully"
        )

    except UserNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Team not found"
        )
    except OptimisticLockError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e)
        )
    except LineupValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except DeadlinePassedError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Lineup deadline has passed"
        )
    except PlayerNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.post("/team/{team_id}/week/{week}/optimize", response_model=APIResponse[LineupOptimizationResponse])
async def optimize_lineup(
    team_id: str,
    week: int,
    request: OptimizeLineupRequest,
    season: Optional[str] = Query(None, description="Season year (defaults to current)"),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    """Generate optimized lineup suggestions based on projections and constraints"""
    try:
        # Verify user owns this team
        team = lineup_service.get_team(team_id, db)
        if team.user_id != current_user["user_id"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only optimize your own lineups"
            )

        optimization = lineup_service.optimize_lineup(
            team_id=team_id,
            week=week,
            season=season,
            criteria=request.criteria,
            constraints=request.constraints,
            preserve_starters=request.preserve_starters,
            db=db
        )

        return APIResponse(
            success=True,
            data=LineupOptimizationResponse.from_orm(optimization),
            message="Lineup optimization completed"
        )

    except UserNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Team not found"
        )
    except LineupNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No lineup found to optimize"
        )
    except InvalidRosterError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/team/{team_id}/week/{week}/validate", response_model=APIResponse[LineupValidationResponse])
async def validate_lineup(
    team_id: str,
    week: int,
    players: List[LineupPlayerRequest],
    season: Optional[str] = Query(None, description="Season year (defaults to current)"),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    """Validate a lineup configuration without saving"""
    try:
        # Verify user has access to this team
        team = lineup_service.get_team(team_id, db)
        if team.user_id != current_user["user_id"]:
            if not league_service.is_user_in_league(team.league_id, current_user["user_id"], db):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Access denied"
                )

        # Convert request to lineup players
        lineup_players = [
            {
                "player_id": p.player_id,
                "position": p.position,
                "is_starter": p.is_starter,
                "bench_position": p.bench_position
            }
            for p in players
        ]

        validation = lineup_service.validate_lineup(team_id, lineup_players, db)

        return APIResponse(
            success=True,
            data=LineupValidationResponse.from_orm(validation),
            message="Lineup validation completed"
        )

    except UserNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Team not found"
        )
    except PlayerNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


# Lineup History and Analytics
@router.get("/team/{team_id}/history", response_model=APIResponse[List[LineupHistoryResponse]])
async def get_lineup_history(
    team_id: str,
    week: Optional[int] = Query(None, description="Filter by specific week"),
    season: Optional[str] = Query(None, description="Filter by season"),
    limit: int = Query(default=50, le=100, description="Maximum number of results"),
    offset: int = Query(default=0, ge=0, description="Number of results to skip"),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    """Get lineup change history for a team"""
    try:
        # Verify user owns this team
        team = lineup_service.get_team(team_id, db)
        if team.user_id != current_user["user_id"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only view your own lineup history"
            )

        history = lineup_service.get_lineup_history(
            team_id=team_id,
            week=week,
            season=season,
            limit=limit,
            offset=offset,
            db=db
        )

        return APIResponse(
            success=True,
            data=[LineupHistoryResponse.from_orm(entry) for entry in history],
            message="Lineup history retrieved successfully"
        )

    except UserNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Team not found"
        )


@router.get("/league/{league_id}/week/{week}", response_model=APIResponse[List[LineupResponse]])
async def get_league_lineups(
    league_id: str,
    week: int,
    season: Optional[str] = Query(None, description="Season year (defaults to current)"),
    include_bench: bool = Query(default=False, description="Include bench players"),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    """Get all lineups for a league and week"""
    try:
        # Verify user is in the league
        if not league_service.is_user_in_league(league_id, current_user["user_id"], db):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied - not a league member"
            )

        lineups = lineup_service.get_league_lineups(
            league_id=league_id,
            week=week,
            season=season,
            include_bench=include_bench,
            db=db
        )

        return APIResponse(
            success=True,
            data=[LineupResponse.from_orm(lineup) for lineup in lineups],
            message="League lineups retrieved successfully"
        )

    except LeagueNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="League not found"
        )


@router.get("/team/{team_id}/analytics", response_model=APIResponse[Dict[str, Any]])
async def get_lineup_analytics(
    team_id: str,
    season: Optional[str] = Query(None, description="Season year (defaults to current)"),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    """Get comprehensive lineup analytics for a team"""
    try:
        # Verify user owns this team
        team = lineup_service.get_team(team_id, db)
        if team.user_id != current_user["user_id"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only view your own analytics"
            )

        analytics = lineup_service.get_team_lineup_analytics(
            team_id=team_id,
            season=season,
            db=db
        )

        return APIResponse(
            success=True,
            data=analytics,
            message="Lineup analytics retrieved successfully"
        )

    except UserNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Team not found"
        )


# Bulk Operations
@router.post("/team/{team_id}/copy-lineup")
async def copy_lineup(
    team_id: str,
    from_week: int = Query(..., description="Source week"),
    to_week: int = Query(..., description="Target week"),
    season: Optional[str] = Query(None, description="Season year"),
    overwrite: bool = Query(default=False, description="Overwrite existing lineup"),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    """Copy lineup from one week to another"""
    try:
        # Verify user owns this team
        team = lineup_service.get_team(team_id, db)
        if team.user_id != current_user["user_id"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only copy your own lineups"
            )

        copied_lineup = lineup_service.copy_lineup(
            team_id=team_id,
            from_week=from_week,
            to_week=to_week,
            season=season,
            overwrite=overwrite,
            db=db
        )

        return APIResponse(
            success=True,
            data=LineupResponse.from_orm(copied_lineup),
            message="Lineup copied successfully"
        )

    except UserNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Team not found"
        )
    except LineupNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Source lineup not found"
        )
    except LineupValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/team/{team_id}/auto-set")
async def auto_set_lineup(
    team_id: str,
    week: int,
    criteria: str = Query(default="projected_points", description="Auto-set criteria"),
    season: Optional[str] = Query(None, description="Season year"),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    """Automatically set lineup based on projections and availability"""
    try:
        # Verify user owns this team
        team = lineup_service.get_team(team_id, db)
        if team.user_id != current_user["user_id"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only auto-set your own lineups"
            )

        lineup = lineup_service.auto_set_lineup(
            team_id=team_id,
            week=week,
            season=season,
            criteria=criteria,
            db=db
        )

        return APIResponse(
            success=True,
            data=LineupResponse.from_orm(lineup),
            message="Lineup auto-set successfully"
        )

    except UserNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Team not found"
        )
    except DeadlinePassedError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Lineup deadline has passed"
        )
    except InvalidRosterError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


# Lineup Locking and Status
@router.post("/team/{team_id}/week/{week}/lock")
async def lock_lineup(
    team_id: str,
    week: int,
    season: Optional[str] = Query(None, description="Season year"),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    """Manually lock lineup before deadline (prevents further changes)"""
    try:
        # Verify user owns this team
        team = lineup_service.get_team(team_id, db)
        if team.user_id != current_user["user_id"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only lock your own lineups"
            )

        lineup = lineup_service.lock_lineup(team_id, week, season, db)

        return APIResponse(
            success=True,
            data=LineupResponse.from_orm(lineup),
            message="Lineup locked successfully"
        )

    except UserNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Team not found"
        )
    except LineupNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lineup not found"
        )
    except LineupValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/league/{league_id}/deadlines", response_model=APIResponse[Dict[str, Any]])
async def get_lineup_deadlines(
    league_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    """Get lineup deadlines for current and upcoming weeks"""
    try:
        # Verify user is in the league
        if not league_service.is_user_in_league(league_id, current_user["user_id"], db):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied - not a league member"
            )

        deadlines = lineup_service.get_lineup_deadlines(league_id, db)

        return APIResponse(
            success=True,
            data=deadlines,
            message="Lineup deadlines retrieved successfully"
        )

    except LeagueNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="League not found"
        )