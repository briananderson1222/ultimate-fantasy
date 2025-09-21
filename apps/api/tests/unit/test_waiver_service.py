from __future__ import annotations

import importlib
import sys
import uuid as _uuid
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool


def backend_src_path() -> Path:
    return Path(__file__).resolve().parents[2] / "src"


def make_session() -> Session:
    sys.path.insert(0, str(backend_src_path()))
    Base = importlib.import_module("domains.shared.models.base").Base

    # Import all domain models to ensure they're registered with Base.metadata
    importlib.import_module("domains.users.models.user")
    importlib.import_module("domains.leagues.models.league")
    importlib.import_module("domains.leagues.models.team")
    importlib.import_module("domains.lineups.models.lineup")
    importlib.import_module("domains.trading.models.waiver")
    importlib.import_module("domains.scoring.models.score")
    importlib.import_module("domains.shared.models.achievement")
    importlib.import_module("domains.sports.models.player")
    importlib.import_module("models.notification")  # Central models still exist
    importlib.import_module("models.preset")
    importlib.import_module("models.roster")
    importlib.import_module("models.rule")
    importlib.import_module("models.schedule")

    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        future=True,
        pool_pre_ping=True,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(bind=engine, future=True, expire_on_commit=False)
    return SessionLocal()


def seed_user(session: Session, user_id: _uuid.UUID | None = None):
    User = importlib.import_module("domains.users.models.user").User
    uid = user_id or _uuid.uuid4()
    user = User(
        user_id=uid,
        username=f"testuser_{str(uid)[:8]}",  # Required field
        email=f"{uid}@ultimatefantasy.app",
        password_hash="$2b$12$test_hash_for_testing_purposes",  # Required field
        display_name="User",
        cognito_sub=str(uid),
    )
    session.add(user)
    session.flush()
    return uid


def seed_player(session: Session, player_id: _uuid.UUID | None = None):
    Player = importlib.import_module("domains.sports.models.player").Player
    pid = player_id or _uuid.uuid4()
    player = Player(
        player_id=pid,
        external_id=str(pid)[:12],
        name="Unit Test",
        sport="wnba",
        position="PG",
    )
    session.add(player)
    session.flush()
    return pid


def create_league_with_team(session: Session):
    LeagueService = importlib.import_module(
        "domains.leagues.services.league_service"
    ).LeagueService
    Team = importlib.import_module("domains.leagues.models.team").Team

    commissioner_id = seed_user(session)
    svc = LeagueService(session)
    league = svc.create(
        commissioner_id=commissioner_id,
        name="Waiver League",
        sport="wnba",
        league_type="head_to_head",
        season="2025",
    )
    team = (
        session.query(Team)
        .filter(Team.league_id == league.league_id, Team.user_id == commissioner_id)
        .one()
    )
    return league, team


def test_place_bid_persists_waiver_row():
    sys.path.insert(0, str(backend_src_path()))
    WaiverService = importlib.import_module(
        "domains.trading.services.waiver_service"
    ).WaiverService
    Waiver = importlib.import_module("domains.trading.models.waiver").Waiver

    with make_session() as session:
        league, team = create_league_with_team(session)
        player_id = seed_player(session)

        svc = WaiverService(session)
        w = svc.place_bid(
            league_id=str(league.league_id),
            team_id=str(team.team_id),
            player_id=str(player_id),
            bid=37,
        )

        assert w.waiver_id is not None
        assert w.league_id == league.league_id
        assert w.team_id == team.team_id
        assert w.player_id == player_id
        assert w.bid == 37
        assert w.status in ("pending", "open", "placed")

        # Ensure persisted
        assert session.get(Waiver, w.waiver_id) is not None
