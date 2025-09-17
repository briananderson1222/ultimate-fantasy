from __future__ import annotations

"""
Unit Test — Scoring aggregation

Ensures ScoringService.compute_league_scoreboard aggregates per-team totals
by summing stats.points for players present in a team's lineups.
"""

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


def seed_user(session: Session, user_id: _uuid.UUID | None = None) -> _uuid.UUID:
    User = importlib.import_module("models.user").User
    uid = user_id or _uuid.uuid4()
    user = User(
        user_id=uid,
        email=f"{uid}@ultimatefantasy.app",
        display_name="User",
        cognito_sub=str(uid),
    )
    session.add(user)
    session.flush()
    return uid


def seed_player(session: Session, player_id: _uuid.UUID | None = None) -> _uuid.UUID:
    Player = importlib.import_module("models.player").Player
    pid = player_id or _uuid.uuid4()
    player = Player(
        player_id=pid,
        external_id=str(pid)[:12],
        full_name="Unit Test",
        sport="basketball",
        position="G",
    )
    session.add(player)
    session.flush()
    return pid


def seed_lineup(
    session: Session, *, team_id: _uuid.UUID, game_day: date, players: list[dict]
):
    Lineup = importlib.import_module("models.lineup").Lineup
    lu = Lineup(team_id=team_id, game_day=game_day, players=players, version=1)
    session.add(lu)
    session.flush()
    return lu


def seed_score(session: Session, *, player_id: _uuid.UUID, game_day: date, points: int):
    Score = importlib.import_module("models.score").Score
    sc = Score(player_id=player_id, game_day=game_day, stats={"points": points})
    session.add(sc)
    session.flush()
    return sc


def create_league_with_two_teams(session: Session):
    LeagueService = importlib.import_module("services.league_service").LeagueService
    Team = importlib.import_module("models.team").Team
    commissioner_id = seed_user(session)
    svc = LeagueService(session)
    league = svc.create(
        commissioner_id=commissioner_id,
        name="Aggregate League",
        sport="basketball",
        league_type="head_to_head",
        season="2025",
    )
    # Commissioner team exists
    team_commish = (
        session.query(Team)
        .filter(Team.league_id == league.league_id, Team.user_id == commissioner_id)
        .one()
    )
    # Second team
    user2 = seed_user(session)
    team2 = svc.join(user_id=user2, league_id=league.league_id)
    return league, team_commish, team2


def test_compute_league_scoreboard_sums_points_and_sorts():
    sys.path.insert(0, str(backend_src_path()))
    ScoringService = importlib.import_module("services.scoring_service").ScoringService

    with make_session() as session:
        league, team_a, team_b = create_league_with_two_teams(session)

        # Seed players and lineups for a single day
        day = date(2025, 1, 1)
        p1, p2, p3, p4 = (seed_player(session) for _ in range(4))

        seed_lineup(
            session,
            team_id=team_a.team_id,
            game_day=day,
            players=[
                {"player_id": str(p1), "position": "G"},
                {"player_id": str(p2), "position": "F"},
            ],
        )
        seed_lineup(
            session,
            team_id=team_b.team_id,
            game_day=day,
            players=[
                {"player_id": str(p3), "position": "G"},
                {"player_id": str(p4), "position": "F"},
            ],
        )

        # Scores for that day
        seed_score(session, player_id=p1, game_day=day, points=10)
        seed_score(session, player_id=p2, game_day=day, points=5)
        seed_score(session, player_id=p3, game_day=day, points=20)
        seed_score(session, player_id=p4, game_day=day, points=3)

        svc = ScoringService(session)

        # compute for specific day
        items = svc.compute_league_scoreboard(league_id=league.league_id, game_day=day)

        # Expect team_b first (20+3=23) then team_a (10+5=15)
        assert len(items) == 2
        assert items[0]["team_id"] == team_b.team_id
        assert items[0]["total_points"] == 23
        assert items[1]["team_id"] == team_a.team_id
        assert items[1]["total_points"] == 15

        # compute across all days (same result here)
        all_items = svc.compute_league_scoreboard(
            league_id=league.league_id, game_day=None
        )
        assert all_items[0]["team_id"] == team_b.team_id
        assert all_items[0]["total_points"] == 23
