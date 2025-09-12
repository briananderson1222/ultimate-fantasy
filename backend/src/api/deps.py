from __future__ import annotations

import os
from typing import Generator

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
