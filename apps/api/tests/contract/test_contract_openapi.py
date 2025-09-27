from __future__ import annotations

import importlib
import json
import sys
from pathlib import Path

import yaml
from fastapi.testclient import TestClient


def repo_root() -> Path:
    # apps/api/tests/contract/test_*.py -> up four to repo root
    return Path(__file__).resolve().parents[4]


def load_openapi_spec() -> dict:
    spec_path = (
        repo_root() / "specs/001-ultimate-fantasy-platform/contracts/openapi.yml"
    )
    assert spec_path.exists(), f"Missing OpenAPI file at {spec_path}"
    return yaml.safe_load(spec_path.read_text(encoding="utf-8"))


def expected_paths_methods() -> set[tuple[str, str]]:
    # method names are lowercase as per OpenAPI spec
    return {
        ("/api/leagues", "post"),
        ("/api/leagues/{leagueId}/settings", "patch"),
        ("/api/leagues/{leagueId}/join", "post"),
        ("/api/lineups", "put"),
        ("/api/leagues/{leagueId}/scoreboard", "get"),
        ("/api/waivers/bids", "post"),
        ("/api/leagues/{leagueId}/public", "get"),
    }


def test_contract_spec_contains_required_paths():
    spec = load_openapi_spec()
    assert "paths" in spec, "OpenAPI spec missing 'paths' section"
    paths = spec["paths"]
    for path, method in expected_paths_methods():
        assert path in paths, f"Missing path in contract: {path}"
        assert method in paths[path], f"Missing method in contract for {path}: {method}"


def test_app_openapi_matches_contract_paths():
    # Ensure we can import the app and compare its generated OpenAPI doc to the contract
    # Add api/src to import path for module imports
    backend_src = Path(__file__).resolve().parents[2] / "src"
    sys.path.insert(0, str(backend_src))

    # Import must succeed once T027 is implemented
    app_module = importlib.import_module("main")
    assert hasattr(app_module, "app"), "Expected 'app' FastAPI instance in main.py"

    client = TestClient(app_module.app)
    resp = client.get("/openapi.json")
    assert resp.status_code == 200, "App must expose /openapi.json"
    app_openapi = resp.json()

    app_paths = set()
    for p, methods in app_openapi.get("paths", {}).items():
        for m in methods.keys():
            app_paths.add((p, m.lower()))

    missing = sorted(expected_paths_methods() - app_paths)
    assert not missing, f"App missing contract endpoints: {json.dumps(missing)}"
