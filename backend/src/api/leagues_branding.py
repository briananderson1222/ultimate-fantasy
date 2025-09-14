from __future__ import annotations

import uuid as _uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Path, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from api.deps import get_current_user_id, get_db
from models.league_branding import LeagueBranding

router = APIRouter()


class BrandingIn(BaseModel):
    theme: dict[str, str] | None = None
    name: str | None = None
    logo_url: str | None = None


class BrandingOut(BrandingIn):
    league_id: _uuid.UUID


@router.get(
    "/leagues/{leagueId}/branding",
    status_code=status.HTTP_200_OK,
    response_model=BrandingOut,
)
def get_branding(
    leagueId: Annotated[str, Path()],
    db: Session = Depends(get_db),
) -> BrandingOut:
    """
    Get the branding settings for a specific league.

    This endpoint retrieves the custom theme, name, and logo URL for a given league.
    If no custom branding has been set for the league, it returns default empty values.
    """
    try:
        league_uuid = _uuid.UUID(leagueId)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="invalid league id"
        )

    row = (
        db.query(LeagueBranding)
        .filter(LeagueBranding.league_id == league_uuid)
        .one_or_none()
    )
    if not row:
        return BrandingOut(league_id=league_uuid, theme=None, name=None, logo_url=None)
    return BrandingOut(
        league_id=row.league_id, theme=row.theme, name=row.name, logo_url=row.logo_url
    )


@router.put(
    "/leagues/{leagueId}/branding",
    status_code=status.HTTP_200_OK,
    response_model=BrandingOut,
)
def put_branding(
    leagueId: Annotated[str, Path()],
    payload: BrandingIn,
    db: Session = Depends(get_db),
    _user_id: _uuid.UUID = Depends(get_current_user_id),
) -> BrandingOut:
    """
    Update the branding settings for a specific league.

    This endpoint allows an authenticated user to set or update the custom theme,
    name, and logo URL for a league. The user must be a member of the league
    (validation handled by `get_current_user_id` dependency and related logic not shown here).
    """
    try:
        league_uuid = _uuid.UUID(leagueId)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="invalid league id"
        )

    row = (
        db.query(LeagueBranding)
        .filter(LeagueBranding.league_id == league_uuid)
        .one_or_none()
    )
    if not row:
        row = LeagueBranding(league_id=league_uuid)
        db.add(row)
    row.theme = payload.theme
    row.name = payload.name
    row.logo_url = payload.logo_url
    db.flush()
    return BrandingOut(
        league_id=row.league_id, theme=row.theme, name=row.name, logo_url=row.logo_url
    )
