from __future__ import annotations

import uuid
from datetime import datetime, timedelta
from typing import List

from sqlalchemy.orm import Session

from src.domains.trading.models.waiver import Waiver
from src.domains.shared.interfaces.trading_service import TradingServiceInterface
from src.domains.shared.events.publisher import DomainEventPublisher
from src.infrastructure.events.dispatcher import get_event_dispatcher


class TradingService(TradingServiceInterface):
    def __init__(self, session: Session) -> None:
        self.session = session

        # Initialize event publishing
        try:
            dispatcher = get_event_dispatcher()
            self.event_publisher = DomainEventPublisher(dispatcher, "trading")
        except RuntimeError:
            # Event dispatcher not initialized, disable events
            self.event_publisher = None

    async def validate_trade_eligibility(self, user_id: str, league_id: str) -> bool:
        """Validate if a user is eligible to make trades in a league."""
        from src.domains.leagues.models.team import Team

        user_uuid = uuid.UUID(user_id)
        league_uuid = uuid.UUID(league_id)

        # Check if user has a team in the league
        team = (
            self.session.query(Team)
            .filter(Team.user_id == user_uuid, Team.league_id == league_uuid)
            .first()
        )
        if not team:
            return False

        # For now, all team members are eligible to trade
        # In the future, this could check trade deadlines, league settings, etc.
        return True

    async def process_waiver_claim(self, waiver_id: str, user_id: str) -> dict:
        """Process a waiver claim for a user."""
        waiver_uuid = uuid.UUID(waiver_id)
        user_uuid = uuid.UUID(user_id)

        # Get the waiver
        waiver = self.session.query(Waiver).filter(Waiver.waiver_id == waiver_uuid).first()
        if not waiver:
            raise ValueError(f"Waiver with ID {waiver_id} not found")

        # For now, return a simple transaction representation
        # In the future, this would create an actual Transaction object
        transaction = {
            "transaction_id": str(uuid.uuid4()),
            "waiver_id": waiver_id,
            "user_id": user_id,
            "type": "waiver_claim",
            "status": "processed",
            "timestamp": datetime.now().isoformat(),
        }

        # Publish waiver claim processed event
        if self.event_publisher:
            try:
                import asyncio
                asyncio.create_task(self.event_publisher.publish_event(
                    "waiver_claim_processed",
                    waiver_id,
                    {
                        "transaction_id": transaction["transaction_id"],
                        "waiver_id": waiver_id,
                        "user_id": user_id,
                        "player_id": str(waiver.player_id),
                        "bid": waiver.bid,
                        "status": "processed",
                    }
                ))

                # Publish integration event for other domains
                asyncio.create_task(self.event_publisher.publish_integration_event(
                    "player_acquired",
                    waiver_id,
                    {
                        "user_id": user_id,
                        "player_id": str(waiver.player_id),
                        "acquisition_type": "waiver",
                        "league_id": str(waiver.league_id),
                    },
                    target_domains=["lineups", "scoring"]
                ))
            except Exception as e:
                print(f"Warning: Failed to publish waiver claim event: {e}")

        return transaction

    async def get_active_waivers(self, league_id: str) -> List[Waiver]:
        """Get all active waivers for a league."""
        league_uuid = uuid.UUID(league_id)

        # Get all waivers for the league, ordered by bid amount (descending)
        waivers = (
            self.session.query(Waiver)
            .filter(Waiver.league_id == league_uuid)
            .order_by(Waiver.bid.desc())
            .all()
        )

        return waivers

    async def get_user_transactions(self, user_id: str, league_id: str) -> List[dict]:
        """Get all transactions for a user in a specific league."""
        from src.domains.leagues.models.team import Team

        user_uuid = uuid.UUID(user_id)
        league_uuid = uuid.UUID(league_id)

        # Find the user's team in the league
        team = (
            self.session.query(Team)
            .filter(Team.user_id == user_uuid, Team.league_id == league_uuid)
            .first()
        )
        if not team:
            return []

        # For now, return waiver transactions
        # In the future, this would include actual Transaction objects
        waivers = (
            self.session.query(Waiver)
            .filter(Waiver.team_id == team.team_id)
            .all()
        )

        transactions = []
        for waiver in waivers:
            transactions.append(
                {
                    "transaction_id": str(waiver.waiver_id),
                    "type": "waiver_bid",
                    "player_id": str(waiver.player_id),
                    "bid": waiver.bid,
                    "status": "pending",
                    "created_at": waiver.created_at.isoformat() if waiver.created_at else None,
                }
            )

        return transactions

    async def validate_waiver_claim(self, waiver_id: str, user_id: str) -> bool:
        """Validate if a user can claim a specific waiver."""
        waiver_uuid = uuid.UUID(waiver_id)
        user_uuid = uuid.UUID(user_id)

        # Get the waiver
        waiver = self.session.query(Waiver).filter(Waiver.waiver_id == waiver_uuid).first()
        if not waiver:
            return False

        # Check if user is eligible to trade in this league
        league_id = str(waiver.league_id)
        return await self.validate_trade_eligibility(user_id, league_id)

    async def get_trade_deadline(self, league_id: str) -> datetime:
        """Get the trade deadline for a league."""
        # For now, return a default trade deadline (end of current year)
        # In the future, this would be configurable per league
        return datetime(datetime.now().year, 12, 31)