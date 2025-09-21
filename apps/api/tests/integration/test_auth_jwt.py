from __future__ import annotations

"""
Integration Test — JWT auth (dev mode)

Verifies that protected endpoints reject requests without Authorization and
accept with a valid HS256 dev token.
"""

import importlib
import os
import sys
import uuid
from pathlib import Path

import jwt
from fastapi.testclient import TestClient
from sqlalchemy import create_engine


def backend_src_path() -> Path:
    return Path(__file__).resolve().parents[2] / "src"


def app_client() -> TestClient:
    sys.path.insert(0, str(backend_src_path()))

    # Configure dev auth mode
    os.environ["AUTH_MODE"] = "dev"
    os.environ["AUTH_DEV_SECRET"] = "test-secret"

    # Ensure tables exist for the in-memory DB
    Base = importlib.import_module("domains.shared.models.base").Base
    # Ensure core models are registered before metadata reflection
    importlib.import_module("domains.users.models.user")
    importlib.import_module("domains.leagues.models.league")
    importlib.import_module("domains.leagues.models.team")
    database_url = os.getenv("DATABASE_URL", "sqlite+pysqlite:///test.db")
    os.environ["DATABASE_URL"] = database_url
    reset_session_factory = importlib.import_module(
        "infrastructure.database.session_factory"
    ).reset_session_factory
    connect_args = {"check_same_thread": False} if str(database_url).startswith("sqlite") else {}
    engine = create_engine(database_url, future=True, connect_args=connect_args)
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    reset_session_factory()

    app_module = importlib.import_module("main")
    assert hasattr(
        app_module, "app"
    ), "Expected FastAPI instance named 'app' in main.py"
    return TestClient(app_module.app)


def bearer(secret: str, *, sub: str) -> str:
    token = jwt.encode({"sub": sub}, secret, algorithm="HS256")
    return f"Bearer {token}"


def test_post_leagues_requires_auth_or_dev_header():
    client = app_client()

    payload = {
        "name": "JWT League",
        "sport": "basketball",
        "league_type": "head_to_head",
        "season": "2025",
    }

    # No Authorization -> expect 401
    r = client.post("/leagues", json=payload)
    assert r.status_code in (401, 403)

    # With valid Authorization Bearer token -> expect 201
    uid = str(uuid.uuid4())
    authz = bearer(os.environ["AUTH_DEV_SECRET"], sub=uid)
    r2 = client.post("/leagues", json=payload, headers={"Authorization": authz})
    assert r2.status_code == 201
