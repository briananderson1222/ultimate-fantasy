"""Integration tests for trading-user domain boundaries."""

import pytest

from domains.shared.interfaces.trading_service import TradingServiceInterface
from domains.shared.interfaces.user_service import UserServiceInterface


class TestTradingUserBoundaries:
    # Use the trading_service and user_service fixtures from conftest.py

    @pytest.mark.asyncio
    async def test_trade_eligibility_matches_user_permissions(
        self, trading_service, user_service
    ):
        """Test trade eligibility aligns with user permissions."""
        user_id = "550e8400-e29b-41d4-a716-446655440000"
        league_id = "6ba7b810-9dad-11d1-80b4-00c04fd430c8"

        is_eligible = await trading_service.validate_trade_eligibility(
            user_id, league_id
        )
        has_permission = await user_service.validate_user_permissions(
            user_id, f"trading:{league_id}", "write"
        )

        if is_eligible:
            assert has_permission
