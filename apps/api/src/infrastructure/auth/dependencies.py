"""Simplified authentication dependencies for local/testing use."""

from __future__ import annotations

from typing import Optional

from fastapi import Depends, Header, HTTPException, status


async def get_current_user(x_user_id: Optional[str] = Header(None)) -> dict[str, str]:
    """Minimal dependency that extracts a user id from the `X-User-Id` header.

    This keeps draft and league routes working during the consolidation refactor
    where full authentication has not been re-integrated yet.
    """
    if not x_user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")

    return {"user_id": x_user_id}


__all__ = ["get_current_user"]
