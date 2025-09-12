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
    Base = importlib.import_module("models.base").Base
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
    User = importlib.import_module("models.user").User
    uid = user_id or _uuid.uuid4()
    user = User(user_id=uid, email=f"{uid}@example.com", display_name="User", cognito_sub=str(uid))
    session.add(user)
    session.flush()
    return uid


def seed_player(session: Session, player_id: _uuid.UUID | None = None):
    Player = importlib.import_module("models.player").Player
    pid = player_id or _uuid.uuid4()
    player = Player(player_id=pid, external_id=str(pid)[:12], full_name="Unit Test", sport="basketball", position="G")
    session.add(player)
    session.flush()
    return pid


def create_league_with_team(session: Session):
    LeagueService = importlib.import_module("services.league_service").LeagueService
    Team = importlib.import_module("models.team").Team

    commissioner_id = seed_user(session)
    svc = LeagueService(session)
    league = svc.create(
        commissioner_id=commissioner_id,
        name="Waiver League",
        sport="basketball",
        league_type="head_to_head",
        season="2025",
    )
    team = session.query(Team).filter(Team.league_id == league.league_id, Team.user_id == commissioner_id).one()
    return league, team


def test_place_bid_persists_waiver_row():
    sys.path.insert(0, str(backend_src_path()))
    WaiverService = importlib.import_module("services.waiver_service").WaiverService
    Waiver = importlib.import_module("models.waiver").Waiver

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

