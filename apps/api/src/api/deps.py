from __future__ import annotations

import os
import uuid as _uuid
from collections.abc import Generator

from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from domains.drafts.services.draft_service import DraftService
from domains.leagues.services.league_service import LeagueService
from domains.lineups.services.lineup_service import LineupService
from domains.scoring.services.scoring_service import ScoringService
from domains.trading.services.trading_service import TradingService
from domains.users.services.user_service import UserService
from domains.waitlist.services.waitlist_service import WaitlistService
from services.player_service import PlayerService
from domains.sports.services.sports_data_service import SportsDataService
from domains.shared.models.base import Base as DomainBase
from infrastructure.database.session_factory import get_session_factory
from models.base import Base as LegacyBase


def _ensure_sqlite_schema() -> None:
    """Create tables automatically when running against SQLite.

    This mirrors the legacy behaviour that kept ad-hoc dev/test runs working
    without migrations while the new infrastructure manager is still being
    wired in.
    """

    url = os.getenv("DATABASE_URL", "sqlite+pysqlite:///:memory:")
    if not url.startswith("sqlite"):
        return

    # The infrastructure database manager is responsible for metadata, but
    # the declarative base still needs to be registered once for SQLite.
    factory = get_session_factory()
    session = factory.get_sync_session()
    try:
        engine = session.get_bind()
        DomainBase.metadata.create_all(bind=engine)
        LegacyBase.metadata.create_all(bind=engine)
    finally:
        session.close()


def get_db() -> Generator[Session, None, None]:
    _ensure_sqlite_schema()

    factory = get_session_factory()
    session = factory.get_sync_session()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def get_league_service(db: Session = Depends(get_db)) -> LeagueService:
    """FastAPI dependency that returns a per-request league service."""

    return LeagueService(db)


def get_user_service(db: Session = Depends(get_db)) -> UserService:
    """FastAPI dependency that returns a per-request user service."""

    return UserService(db)


def get_lineup_service(db: Session = Depends(get_db)) -> LineupService:
    """FastAPI dependency that returns a per-request lineup service."""

    return LineupService(db)


def get_draft_service(db: Session = Depends(get_db)) -> DraftService:
    """FastAPI dependency that returns a per-request draft service."""

    return DraftService(db)


def get_trading_service(db: Session = Depends(get_db)) -> TradingService:
    """FastAPI dependency that returns a per-request trading service."""

    return TradingService(db)


def get_scoring_service(db: Session = Depends(get_db)) -> ScoringService:
    """FastAPI dependency that returns a per-request scoring service."""

    return ScoringService(db)


def get_waitlist_service(db: Session = Depends(get_db)) -> WaitlistService:
    """FastAPI dependency that returns a per-request waitlist service."""

    return WaitlistService(db)


_sports_data_service: SportsDataService | None = None
_player_service: PlayerService | None = None


def get_sports_data_service() -> SportsDataService:
    """Lazy-initialize the consolidated sports data service."""

    global _sports_data_service
    if _sports_data_service is None:
        # Create service directly since the async factory is for Redis initialization
        # The routes will handle async operations within the service methods
        _sports_data_service = SportsDataService()
    return _sports_data_service


def get_player_service() -> PlayerService:
    """Lazy-initialize the player service with consolidated sports data provider."""

    global _player_service
    if _player_service is None:
        # Note: PlayerService will need to be updated to work with async sports service
        # For now, create a basic instance
        _player_service = PlayerService()
    return _player_service


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
