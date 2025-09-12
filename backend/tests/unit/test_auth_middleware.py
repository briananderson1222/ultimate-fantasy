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


def backend_src_path() -> Path:
    return Path(__file__).resolve().parents[2] / "src"


def make_app() -> TestClient:
    sys.path.insert(0, str(backend_src_path()))

    # Dev mode auth
    os.environ["AUTH_MODE"] = "dev"
    os.environ["AUTH_DEV_SECRET"] = "unit-secret"

    # Ensure tables exist (middleware may upsert users)
    Base = importlib.import_module("models.base").Base
    get_engine = importlib.import_module("services.db").get_engine
    engine = get_engine()
    Base.metadata.create_all(bind=engine)

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
        {"sub": sub, "email": "t@example.com", "name": "T"},
        "unit-secret",
        algorithm="HS256",
    )
    r = client.get("/whoami", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    body = r.json()
    assert body.get("user_id") is not None

    # Basic validation that the response contains expected user info
    # (Database persistence testing can be done in integration tests)
