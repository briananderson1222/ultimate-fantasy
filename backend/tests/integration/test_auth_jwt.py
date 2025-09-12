from __future__ import annotations

"""
Integration Test — JWT auth (dev mode)

Verifies that protected endpoints reject requests without Authorization when no
legacy x-user-id is provided, and accept with a valid HS256 dev token.
"""

import importlib
import os
import sys
import uuid
from pathlib import Path

import jwt
from fastapi.testclient import TestClient


def backend_src_path() -> Path:
    return Path(__file__).resolve().parents[2] / "src"


def app_client() -> TestClient:
    sys.path.insert(0, str(backend_src_path()))

    # Configure dev auth mode
    os.environ["AUTH_MODE"] = "dev"
    os.environ["AUTH_DEV_SECRET"] = "test-secret"

    # Ensure tables exist for the in-memory DB
    Base = importlib.import_module("models.base").Base
    get_engine = importlib.import_module("services.db").get_engine
    engine = get_engine()
    Base.metadata.create_all(bind=engine)

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

    # No Authorization and no x-user-id -> expect 401
    r = client.post("/leagues", json=payload)
    assert r.status_code in (401, 403)

    # With valid Authorization Bearer token -> expect 201
    uid = str(uuid.uuid4())
    authz = bearer(os.environ["AUTH_DEV_SECRET"], sub=uid)
    r2 = client.post("/leagues", json=payload, headers={"Authorization": authz})
    assert r2.status_code == 201
