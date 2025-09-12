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
    models_base = importlib.import_module("models.base")
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        future=True,
        pool_pre_ping=True,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    models_base.Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(bind=engine, future=True, expire_on_commit=False)
    return SessionLocal()


def create_user(session: Session, user_id: _uuid.UUID | None = None) -> object:
    User = importlib.import_module("models.user").User
    uid = user_id or _uuid.uuid4()
    user = User(
        user_id=uid,
        email=f"{uid}@example.com",
        display_name="Test",
        cognito_sub=str(uid),
    )
    session.add(user)
    session.flush()
    return user


def test_create_league_adds_commissioner_team():
    sys.path.insert(0, str(backend_src_path()))
    services = importlib.import_module("services.league_service")
    Team = importlib.import_module("models.team").Team

    with make_session() as session:
        commissioner_id = _uuid.uuid4()
        create_user(session, commissioner_id)

        svc = services.LeagueService(session)
        league = svc.create(
            commissioner_id=commissioner_id,
            name="UnitTest League",
            sport="basketball",
            league_type="head_to_head",
            season="2025",
        )

        assert league.league_id is not None
        # Commissioner team should be created for the league
        team = (
            session.query(Team)
            .filter(Team.league_id == league.league_id, Team.user_id == commissioner_id)
            .one()
        )
        assert str(commissioner_id) in team.team_name


def test_join_creates_team_for_user():
    sys.path.insert(0, str(backend_src_path()))
    services = importlib.import_module("services.league_service")
    Team = importlib.import_module("models.team").Team

    with make_session() as session:
        # Seed commissioner and league
        commissioner_id = _uuid.uuid4()
        create_user(session, commissioner_id)
        svc = services.LeagueService(session)
        league = svc.create(
            commissioner_id=commissioner_id,
            name="Join League",
            sport="soccer",
            league_type="head_to_head",
            season="2025",
        )

        # New user joins
        user_id = _uuid.uuid4()
        create_user(session, user_id)
        team = svc.join(user_id=user_id, league_id=league.league_id)

        assert team.team_id is not None
        assert team.league_id == league.league_id
        assert team.user_id == user_id
        # Ensure team persisted
        assert session.get(Team, team.team_id) is not None
