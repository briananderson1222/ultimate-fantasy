from __future__ import annotations

import os
import uuid as _uuid
from collections.abc import Generator

from fastapi import HTTPException, Request, status
from sqlalchemy.orm import Session

from services.db import SessionLocal


def get_db() -> Generator[Session, None, None]:
    # Ensure tables exist for SQLite (test environments)
    url = os.getenv("DATABASE_URL", "sqlite+pysqlite:///:memory:")
    if url.startswith("sqlite"):
        from models.base import Base
        from services.db import get_engine

        engine = get_engine()
        Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def get_current_user_id(request: Request) -> _uuid.UUID:
    """Return the authenticated user's UUID or raise 401.

    - If middleware populated request.state.user_id, use it.
    - In dev mode, allow fallback to x-user-id header for compatibility.
    """
    user_id = getattr(request.state, "user_id", None)
    if user_id:
        return user_id  # type: ignore[no-any-return]

    import os

    mode = os.getenv("AUTH_MODE", "dev").lower()
    if mode.startswith("dev"):
        # Fallback: allow x-user-id header in dev mode only
        header = request.headers.get("x-user-id")
        if header:
            try:
                return _uuid.UUID(header)
            except ValueError:
                pass

    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")
