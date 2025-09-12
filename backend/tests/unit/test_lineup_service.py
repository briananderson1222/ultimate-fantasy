from __future__ import annotations

import importlib
import sys
import uuid as _uuid
from datetime import date
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


def create_user(session: Session, user_id: _uuid.UUID | None = None):
    User = importlib.import_module("models.user").User
    uid = user_id or _uuid.uuid4()
    user = User(user_id=uid, email=f"{uid}@example.com", display_name="User", cognito_sub=str(uid))
    session.add(user)
    session.flush()
    return user


def create_league_and_team(session: Session):
    LeagueService = importlib.import_module("services.league_service").LeagueService

    commissioner_id = _uuid.uuid4()
    create_user(session, commissioner_id)
    svc = LeagueService(session)
    league = svc.create(
        commissioner_id=commissioner_id,
        name="Lineup League",
        sport="basketball",
        league_type="head_to_head",
        season="2025",
    )
    # Commissioner team created by service; return it for convenience
    Team = importlib.import_module("models.team").Team
    team = session.query(Team).filter(Team.league_id == league.league_id, Team.user_id == commissioner_id).one()
    return league, team


def test_set_lineup_persists_players_and_version():
    sys.path.insert(0, str(backend_src_path()))
    LineupService = importlib.import_module("services.lineup_service").LineupService
    Lineup = importlib.import_module("models.lineup").Lineup

    with make_session() as session:
        league, team = create_league_and_team(session)  # noqa: F841 - league unused here

        svc = LineupService(session)
        payload_players = [
            {"player_id": str(_uuid.uuid4()), "position": "G"},
            {"player_id": str(_uuid.uuid4()), "position": "F"},
        ]
        lineup = svc.set_lineup(team_id=str(team.team_id), game_day=date.today(), players=payload_players)

        assert lineup.lineup_id is not None
        assert lineup.team_id == team.team_id
        assert lineup.version == 1
        assert isinstance(lineup.players, list)
        assert len(lineup.players) == 2

        # Ensure persisted
        fetched = session.get(Lineup, lineup.lineup_id)
        assert fetched is not None
        assert fetched.version == 1

