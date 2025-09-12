from __future__ import annotations

import uuid as _uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Header, HTTPException, Path, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from models.rule import Rule
from api.deps import get_db


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
    x_user_id: Annotated[str | None, Header(alias="x-user-id")] = None,
):
    # Auth header expected by quickstart; this endpoint doesn't need to use it yet
    if not x_user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="missing user")

    try:
        league_uuid = _uuid.UUID(leagueId)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="invalid league id")

    # Minimal behavior: persist/append a rule entry. Dedup/upsert can be added later.
    rule = Rule(league_id=league_uuid, name=payload.name, value=payload.value)
    db.add(rule)
    db.flush()
    return RuleOut(rule_id=rule.rule_id, league_id=rule.league_id, name=rule.name, value=rule.value)
