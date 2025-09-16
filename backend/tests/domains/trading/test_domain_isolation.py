"""Domain isolation tests for Trading domain."""
import pytest

class TestTradingDomainIsolation:
    def test_trading_domain_imports(self):
        try:
            from backend.src.domains.trading.services import trading_service
        except ImportError as e:
            pytest.fail(f"Trading domain imports failed: {e}")
