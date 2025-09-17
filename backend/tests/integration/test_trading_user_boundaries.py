"""Integration tests for trading-user domain boundaries."""
import pytest
from src.domains.shared.interfaces.trading_service import TradingServiceInterface
from src.domains.shared.interfaces.user_service import UserServiceInterface

class TestTradingUserBoundaries:
    @pytest.fixture
    def trading_service(self) -> TradingServiceInterface:
        from src.domains.trading.services.trading_service import TradingService
        return TradingService()

    @pytest.fixture
    def user_service(self) -> UserServiceInterface:
        from src.domains.users.services.user_service import UserService
        return UserService()

    @pytest.mark.asyncio
    async def test_trade_eligibility_matches_user_permissions(self, trading_service, user_service):
        """Test trade eligibility aligns with user permissions."""
        user_id = "test-user-123"
        league_id = "test-league-456"

        is_eligible = await trading_service.validate_trade_eligibility(user_id, league_id)
        has_permission = await user_service.validate_user_permissions(user_id, f"trading:{league_id}", "write")

        if is_eligible:
            assert has_permission