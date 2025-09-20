"""Domain isolation tests for Lineups domain."""

import pytest


class TestLineupsDomainIsolation:
    def test_lineups_domain_imports(self):
        try:
            from domains.lineups.services import lineup_service
        except ImportError as e:
            pytest.fail(f"Lineups domain imports failed: {e}")
