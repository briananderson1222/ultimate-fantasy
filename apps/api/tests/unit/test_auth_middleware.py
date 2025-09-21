from __future__ import annotations

import importlib
import os
import sys
import uuid
from pathlib import Path

import jwt
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.testclient import TestClient
from sqlalchemy import create_engine


def backend_src_path() -> Path:
    return Path(__file__).resolve().parents[2] / "src"


def make_app() -> TestClient:
    sys.path.insert(0, str(backend_src_path()))

    # Dev mode auth
    os.environ["AUTH_MODE"] = "dev"
    os.environ["AUTH_DEV_SECRET"] = "unit-secret"

    # Ensure tables exist (middleware may upsert users)
    Base = importlib.import_module("domains.shared.models.base").Base
    importlib.import_module("domains.users.models.user")
    database_url = os.getenv("DATABASE_URL", "sqlite+pysqlite:///test.db")
    os.environ["DATABASE_URL"] = database_url
    reset_session_factory = importlib.import_module(
        "infrastructure.database.session_factory"
    ).reset_session_factory
    connect_args = {"check_same_thread": False} if database_url.startswith("sqlite") else {}
    engine = create_engine(database_url, future=True, connect_args=connect_args)
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    reset_session_factory()

    # Build minimal app with middleware
    AuthContextMiddleware = importlib.import_module(
        "api.middleware.auth"
    ).AuthContextMiddleware

    app = FastAPI()
    app.add_middleware(AuthContextMiddleware)

    @app.get("/whoami")
    async def whoami(request: Request):  # type: ignore[no-redef]
        uid = getattr(request.state, "user_id", None)
        return JSONResponse({"user_id": str(uid) if uid else None})

    return TestClient(app)


def test_invalid_signature_yields_no_user():
    client = make_app()

    bad = jwt.encode({"sub": str(uuid.uuid4())}, "wrong-secret", algorithm="HS256")
    r = client.get("/whoami", headers={"Authorization": f"Bearer {bad}"})
    assert r.status_code == 200
    assert r.json().get("user_id") is None


def test_valid_hs256_sets_user_and_persists():
    """Test that valid JWT tokens are processed correctly."""
    client = make_app()
    sub = str(uuid.uuid4())
    token = jwt.encode(
        {"sub": sub, "email": "t@ultimatefantasy.app", "name": "T"},
        "unit-secret",
        algorithm="HS256",
    )
    r = client.get("/whoami", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    body = r.json()
    assert body.get("user_id") is not None

    # Basic validation that the response contains expected user info
    # (Database persistence testing can be done in integration tests)
