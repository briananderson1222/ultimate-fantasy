"""Domain isolation tests for Users domain."""
import pytest

class TestUsersDomainIsolation:
    def test_users_domain_imports(self):
        try:
            from backend.src.domains.users.services import users_service
        except ImportError as e:
            pytest.fail(f"Users domain imports failed: {e}")
