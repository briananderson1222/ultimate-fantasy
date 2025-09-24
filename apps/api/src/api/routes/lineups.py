"""Lineup API endpoints powered by the consolidated domain service."""

from __future__ import annotations

import uuid as _uuid
from datetime import date
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field

from api.deps import get_current_user_id, get_lineup_service
from domains.lineups.models.lineup import Lineup
from domains.lineups.services.lineup_service import LineupPlayer, LineupService
from domains.shared.exceptions import (
    DeadlinePassedError,
    InsufficientPermissionsError,
    InvalidRosterError,
    LeagueNotFoundError,
    LineupLockedError,
    LineupNotFoundError,
    LineupValidationError,
    OptimisticLockError,
)

router = APIRouter(prefix="/api/v1/lineups", tags=["lineups"])


class LineupPlayerPayload(BaseModel):
    player_id: _uuid.UUID
    position: str = Field(..., max_length=20)


class SetLineupRequest(BaseModel):
    team_id: _uuid.UUID
    game_day: date
    players: list[LineupPlayerPayload]
    expected_version: int | None = Field(
        None, description="Optimistic locking version"
    )


class ValidateLineupRequest(BaseModel):
    team_id: _uuid.UUID
    players: list[LineupPlayerPayload]


class CopyLineupRequest(BaseModel):
    target_week: int = Field(..., ge=1)
    target_game_day: date | None = None


class AutoSetRequest(BaseModel):
    team_id: _uuid.UUID
    week: int = Field(..., ge=1)


class LineupPlayerOut(BaseModel):
    player_id: str
    position: str


class LineupOut(BaseModel):
    lineup_id: str
    team_id: str
    week: int
    game_day: date | None
    version: int
    is_locked: bool
    points_scored: float
    players: list[LineupPlayerOut]


class LineupListResponse(BaseModel):
    items: list[LineupOut]


class ValidationResult(BaseModel):
    is_valid: bool
    errors: list[str]
    warnings: list[str]
    missing_positions: list[str]
    invalid_players: list[str]


class LineupAnalysisResponse(BaseModel):
    lineup_id: str
    team_name: str | None
    week: int
    is_locked: bool
    version: int
    total_projected_points: float
    player_count: int
    players: list[dict[str, Any]]
    position_distribution: dict[str, int]
    validation: ValidationResult


class LineupOptimizationResponse(BaseModel):
    current_projected_points: float
    optimized_projected_points: float
    suggested_changes: list[dict[str, str]]
    improvement_percentage: float


def _serialize_players(lineup: Lineup) -> list[LineupPlayerOut]:
    players: list[dict[str, Any]] = lineup.players or []
    return [
        LineupPlayerOut(
            player_id=str(player.get("player_id")),
            position=str(player.get("position", "")),
        )
        for player in players
    ]


def _to_lineup_out(lineup: Lineup) -> LineupOut:
    return LineupOut(
        lineup_id=str(lineup.lineup_id),
        team_id=str(lineup.team_id),
        week=lineup.week,
        game_day=lineup.game_day,
        version=lineup.version,
        is_locked=lineup.is_locked,
        points_scored=lineup.points_scored,
        players=_serialize_players(lineup),
    )


def _handle_lineup_exception(exc: Exception) -> None:
    if isinstance(exc, LineupNotFoundError):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    if isinstance(exc, InsufficientPermissionsError):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc))
    if isinstance(exc, LineupLockedError):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))
    if isinstance(exc, OptimisticLockError):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))
    if isinstance(
        exc, (LineupValidationError, InvalidRosterError, LeagueNotFoundError)
    ):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    if isinstance(exc, DeadlinePassedError):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail="Lineup service error",
    )


@router.put("", response_model=LineupOut)
def set_lineup(
    payload: SetLineupRequest,
    lineup_service: LineupService = Depends(get_lineup_service),
    current_user_id: _uuid.UUID = Depends(get_current_user_id),
) -> LineupOut:
    try:
        lineup = lineup_service.set_lineup(
            team_id=str(payload.team_id),
            game_day=payload.game_day,
            players=[player.model_dump() for player in payload.players],
            user_id=str(current_user_id),
            expected_version=payload.expected_version,
        )
        return _to_lineup_out(lineup)
    except Exception as exc:  # noqa: BLE001 - mapped to HTTP error
        _handle_lineup_exception(exc)


@router.get("", response_model=LineupListResponse)
def list_lineups(
    team_id: _uuid.UUID = Query(..., description="Team identifier"),
    game_day: date | None = Query(None, description="Filter by game day"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    lineup_service: LineupService = Depends(get_lineup_service),
) -> LineupListResponse:
    try:
        items = lineup_service.list(
            team_id=str(team_id),
            game_day=game_day,
            limit=limit,
            offset=offset,
        )
        return LineupListResponse(items=[_to_lineup_out(lineup) for lineup in items])
    except Exception as exc:  # noqa: BLE001
        _handle_lineup_exception(exc)


@router.get("/{lineup_id}", response_model=LineupOut)
async def get_lineup(
    lineup_id: _uuid.UUID,
    lineup_service: LineupService = Depends(get_lineup_service),
    current_user_id: _uuid.UUID = Depends(get_current_user_id),
) -> LineupOut:
    lineup = lineup_service.get_lineup_by_id(str(lineup_id))
    if not lineup:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Lineup not found"
        )
    owns_lineup = await lineup_service.validate_lineup_ownership(
        str(lineup_id), str(current_user_id)
    )
    if not owns_lineup:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Access denied"
        )
    return _to_lineup_out(lineup)


@router.get("/{lineup_id}/analysis", response_model=LineupAnalysisResponse)
async def get_lineup_analysis(
    lineup_id: _uuid.UUID,
    lineup_service: LineupService = Depends(get_lineup_service),
    current_user_id: _uuid.UUID = Depends(get_current_user_id),
) -> LineupAnalysisResponse:
    owns_lineup = await lineup_service.validate_lineup_ownership(
        str(lineup_id), str(current_user_id)
    )
    if not owns_lineup:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Access denied"
        )
    try:
        analysis = lineup_service.get_lineup_analysis(lineup_id=str(lineup_id))
        return LineupAnalysisResponse(
            lineup_id=analysis["lineup_id"],
            team_name=analysis.get("team_name"),
            week=analysis["week"],
            is_locked=analysis["is_locked"],
            version=analysis["version"],
            total_projected_points=analysis["total_projected_points"],
            player_count=analysis["player_count"],
            players=analysis["players"],
            position_distribution=analysis["position_distribution"],
            validation=ValidationResult(**analysis["validation"].__dict__),
        )
    except Exception as exc:  # noqa: BLE001
        _handle_lineup_exception(exc)


@router.post("/validate", response_model=ValidationResult)
def validate_lineup(
    payload: ValidateLineupRequest,
    lineup_service: LineupService = Depends(get_lineup_service),
    current_user_id: _uuid.UUID = Depends(get_current_user_id),
) -> ValidationResult:
    team = lineup_service.get_team(str(payload.team_id))
    if not team:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Team not found"
        )
    if str(team.user_id) != str(current_user_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="You do not own this team"
        )

    lineup_players = [
        LineupPlayer(player_id=str(player.player_id), position=player.position)
        for player in payload.players
    ]
    try:
        validation = lineup_service.validate_lineup(
            team_id=str(payload.team_id), lineup_players=lineup_players
        )
        return ValidationResult(**validation.__dict__)
    except Exception as exc:  # noqa: BLE001
        _handle_lineup_exception(exc)


@router.post("/{lineup_id}/optimize", response_model=LineupOptimizationResponse)
async def optimize_lineup(
    lineup_id: _uuid.UUID,
    lineup_service: LineupService = Depends(get_lineup_service),
    current_user_id: _uuid.UUID = Depends(get_current_user_id),
) -> LineupOptimizationResponse:
    owns_lineup = await lineup_service.validate_lineup_ownership(
        str(lineup_id), str(current_user_id)
    )
    if not owns_lineup:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Access denied"
        )
    try:
        optimization = lineup_service.suggest_lineup_optimization(
            lineup_id=str(lineup_id)
        )
        return LineupOptimizationResponse(**optimization.__dict__)
    except Exception as exc:  # noqa: BLE001
        _handle_lineup_exception(exc)


@router.post("/{lineup_id}/lock", response_model=LineupOut)
async def lock_lineup(
    lineup_id: _uuid.UUID,
    lineup_service: LineupService = Depends(get_lineup_service),
    current_user_id: _uuid.UUID = Depends(get_current_user_id),
) -> LineupOut:
    owns_lineup = await lineup_service.validate_lineup_ownership(
        str(lineup_id), str(current_user_id)
    )
    if not owns_lineup:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Access denied"
        )
    try:
        lineup = lineup_service.lock_lineup(lineup_id=str(lineup_id))
        return _to_lineup_out(lineup)
    except Exception as exc:  # noqa: BLE001
        _handle_lineup_exception(exc)


@router.post("/{lineup_id}/unlock", response_model=LineupOut)
async def unlock_lineup(
    lineup_id: _uuid.UUID,
    lineup_service: LineupService = Depends(get_lineup_service),
    current_user_id: _uuid.UUID = Depends(get_current_user_id),
) -> LineupOut:
    try:
        lineup = lineup_service.unlock_lineup(
            lineup_id=str(lineup_id), commissioner_id=str(current_user_id)
        )
        return _to_lineup_out(lineup)
    except Exception as exc:  # noqa: BLE001
        _handle_lineup_exception(exc)


@router.post("/{lineup_id}/copy", response_model=LineupOut)
async def copy_lineup(
    lineup_id: _uuid.UUID,
    payload: CopyLineupRequest,
    lineup_service: LineupService = Depends(get_lineup_service),
    current_user_id: _uuid.UUID = Depends(get_current_user_id),
) -> LineupOut:
    owns_lineup = await lineup_service.validate_lineup_ownership(
        str(lineup_id), str(current_user_id)
    )
    if not owns_lineup:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Access denied"
        )
    try:
        lineup = lineup_service.copy_lineup(
            source_lineup_id=str(lineup_id),
            target_week=payload.target_week,
            target_game_day=payload.target_game_day,
            user_id=str(current_user_id),
        )
        return _to_lineup_out(lineup)
    except Exception as exc:  # noqa: BLE001
        _handle_lineup_exception(exc)


@router.post("/auto-set", response_model=LineupOut)
def auto_set_lineup(
    payload: AutoSetRequest,
    lineup_service: LineupService = Depends(get_lineup_service),
    current_user_id: _uuid.UUID = Depends(get_current_user_id),
) -> LineupOut:
    team = lineup_service.get_team(str(payload.team_id))
    if not team:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Team not found"
        )
    if str(team.user_id) != str(current_user_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="You do not own this team"
        )
    try:
        lineup = lineup_service.auto_set_lineup(
            team_id=str(payload.team_id),
            week=payload.week,
        )
        return _to_lineup_out(lineup)
    except Exception as exc:  # noqa: BLE001
        _handle_lineup_exception(exc)
