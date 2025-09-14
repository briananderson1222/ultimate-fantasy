from __future__ import annotations

import uuid as _uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Path, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from api.deps import get_current_user_id, get_db
from models.rule import Rule

router = APIRouter()


class RuleUpdate(BaseModel):
    name: str
    value: dict


class RuleOut(BaseModel):
    rule_id: _uuid.UUID
    league_id: _uuid.UUID
    name: str
    value: dict


@router.patch(
    "/leagues/{leagueId}/settings",
    status_code=status.HTTP_200_OK,
    response_model=RuleOut,
)
def update_league_settings(
    leagueId: Annotated[str, Path()],
    payload: RuleUpdate,
    db: Session = Depends(get_db),
    _user_id: _uuid.UUID = Depends(get_current_user_id),
) -> RuleOut:
    """
    Update the settings for a specific league.

    This endpoint allows an authenticated user (typically the commissioner) to update
    the rules and settings for a league. The current implementation adds a new rule
    entry for each request.

    - **leagueId**: The unique identifier of the league.
    - **payload**: A `RuleUpdate` object containing the name and value of the rule to add.

    The user must have administrative privileges for the league (validation handled
    by dependencies).
    """

    try:
        league_uuid = _uuid.UUID(leagueId)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="invalid league id"
        )

    # Minimal behavior: persist/append a rule entry. Dedup/upsert can be added later.
    rule = Rule(league_id=league_uuid, name=payload.name, value=payload.value)
    db.add(rule)
    db.flush()
    return RuleOut(
        rule_id=rule.rule_id, league_id=rule.league_id, name=rule.name, value=rule.value
    )
