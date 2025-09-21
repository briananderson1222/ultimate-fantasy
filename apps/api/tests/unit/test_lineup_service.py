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


def create_user(session: Session, user_id: _uuid.UUID | None = None):
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
    return user


def create_league_and_team(session: Session):
    LeagueService = importlib.import_module(
        "domains.leagues.services.league_service"
    ).LeagueService

    commissioner_id = _uuid.uuid4()
    create_user(session, commissioner_id)
    svc = LeagueService(session)
    league = svc.create(
        commissioner_id=commissioner_id,
        name="Lineup League",
        sport="wnba",
        league_type="head_to_head",
        season="2025",
    )
    # Commissioner team created by service; return it for convenience
    Team = importlib.import_module("domains.leagues.models.team").Team
    team = (
        session.query(Team)
        .filter(Team.league_id == league.league_id, Team.user_id == commissioner_id)
        .one()
    )
    return league, team


def test_set_lineup_persists_players_and_version():
    sys.path.insert(0, str(backend_src_path()))
    LineupService = importlib.import_module(
        "domains.lineups.services.lineup_service"
    ).LineupService
    Lineup = importlib.import_module("domains.lineups.models.lineup").Lineup

    with make_session() as session:
        league, team = create_league_and_team(session)

        # Create players for complete WNBA lineup
        Player = importlib.import_module("domains.sports.models.player").Player
        player_ids = []
        players = []
        positions = ["PG", "SG", "SF", "PF", "C", "FLEX", "FLEX"]

        for i, pos in enumerate(positions):
            pid = _uuid.uuid4()
            player_ids.append(pid)
            player = Player(
                player_id=pid,
                external_id=str(pid)[:12],
                name=f"Test Player {i+1}",
                sport="wnba",
                position=pos if pos != "FLEX" else "PG",  # FLEX can be any position
            )
            players.append(player)
            session.add(player)

        session.flush()

        # Add players to team roster
        team.roster = [str(pid) for pid in player_ids]
        session.flush()

        svc = LineupService(session)
        payload_players = [
            {"player_id": str(pid), "position": pos}
            for pid, pos in zip(player_ids, positions)
        ]
        lineup = svc.set_lineup(
            team_id=str(team.team_id), game_day=date.today(), players=payload_players
        )

        assert lineup.lineup_id is not None
        assert lineup.team_id == team.team_id
        assert lineup.version == 1
        assert isinstance(lineup.players, list)
        assert len(lineup.players) == 7

        # Ensure persisted
        fetched = session.get(Lineup, lineup.lineup_id)
        assert fetched is not None
        assert fetched.version == 1
