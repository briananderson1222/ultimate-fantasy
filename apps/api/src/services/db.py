from __future__ import annotations

import os
from collections.abc import Iterator
from contextlib import contextmanager

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker


def _database_url() -> str:
    url = os.getenv("DATABASE_URL")
    if url:
        return url
    # Fallback for local/dev without Postgres — not recommended for prod
    return "sqlite+pysqlite:///test.db"  # file-based for persistence


# For tests, use a shared connection to avoid isolation issues
_TEST_ENGINE = None


def get_engine() -> Engine:
    global _TEST_ENGINE
    url = _database_url()

    # For SQLite, use a shared connection to avoid isolation
    if url.startswith("sqlite"):
        if _TEST_ENGINE is None:
            _TEST_ENGINE = create_engine(
                url,
                future=True,
                pool_pre_ping=True,
                connect_args={"check_same_thread": False},
            )
        return _TEST_ENGINE
    else:
        return create_engine(url, future=True, pool_pre_ping=True)


_ENGINE = get_engine()
SessionLocal = sessionmaker(bind=_ENGINE, future=True, expire_on_commit=False)


@contextmanager
def session_scope() -> Iterator[Session]:
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
