"""Domain isolation tests for Waitlist domain."""
import pytest

class TestWaitlistDomainIsolation:
    def test_waitlist_domain_imports(self):
        try:
            from backend.src.domains.waitlist.services import waitlist_service
        except ImportError as e:
            pytest.fail(f"Waitlist domain imports failed: {e}")
