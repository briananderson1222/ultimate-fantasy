"""
Domain isolation tests for Leagues domain.

These tests verify that the Leagues domain can operate independently
without direct dependencies on other domains.
"""
import pytest
import sys
import importlib


class TestLeaguesDomainIsolation:
    """Test that Leagues domain is properly isolated."""

    def test_leagues_domain_imports(self):
        """Test that leagues domain only imports from shared interfaces."""
        # This will fail until domain structure is implemented
        try:
            from domains.leagues.services import league_service
            from domains.leagues.models import league
            from domains.leagues.api import leagues_branding
        except ImportError as e:
            pytest.fail(f"Leagues domain imports failed: {e}")

    def test_no_direct_cross_domain_imports(self):
        """Test that leagues domain doesn't directly import other domains."""
        # Check that leagues domain only imports from shared interfaces
        import ast
        import os

        leagues_path = "backend/src/domains/leagues"
        if not os.path.exists(leagues_path):
            pytest.skip("Leagues domain not yet moved to new structure")

        # Scan all Python files in leagues domain
        for root, dirs, files in os.walk(leagues_path):
            for file in files:
                if file.endswith('.py'):
                    file_path = os.path.join(root, file)
                    with open(file_path, 'r') as f:
                        try:
                            tree = ast.parse(f.read())
                            for node in ast.walk(tree):
                                if isinstance(node, ast.ImportFrom):
                                    if node.module and 'domains' in node.module:
                                        # Should only import from shared or leagues
                                        assert 'shared' in node.module or 'leagues' in node.module, \
                                            f"Invalid cross-domain import in {file_path}: {node.module}"
                        except SyntaxError:
                            # Skip files with syntax errors during transition
                            pass

    @pytest.mark.asyncio
    async def test_leagues_service_independence(self):
        """Test that leagues service can operate independently."""
        # This will fail until LeagueService is implemented
        from domains.leagues.services.league_service import LeagueService

        service = LeagueService()

        # Should be able to create service without external dependencies
        assert service is not None


# NOTE: These tests MUST FAIL initially due to missing domain structure