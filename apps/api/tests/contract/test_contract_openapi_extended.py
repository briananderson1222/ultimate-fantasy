from __future__ import annotations

from pathlib import Path

import yaml


def repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def load_openapi_spec() -> dict:
    spec_path = (
        repo_root() / "specs/001-ultimate-fantasy-platform/contracts/openapi.yml"
    )
    assert spec_path.exists(), f"Missing OpenAPI file at {spec_path}"
    return yaml.safe_load(spec_path.read_text(encoding="utf-8"))


def test_contract_has_read_endpoints_for_ui():
    spec = load_openapi_spec()
    paths = spec.get("paths", {})
    required = [
        ("/me/leagues", "get"),
        ("/leagues/{leagueId}/members", "get"),
        ("/waivers", "get"),
        ("/lineups", "get"),
    ]
    for path, method in required:
        assert path in paths, f"Missing path in contract: {path}"
        assert method in paths[path], f"Missing method {method} for path {path}"
