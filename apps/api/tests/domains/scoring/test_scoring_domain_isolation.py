"""Domain isolation tests for Scoring domain."""

import pytest


class TestScoringDomainIsolation:
    def test_scoring_domain_imports(self):
        try:
            from domains.scoring.services import scoring_service
        except ImportError as e:
            pytest.fail(f"Scoring domain imports failed: {e}")
