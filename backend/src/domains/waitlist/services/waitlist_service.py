import uuid
from typing import List, Optional, Dict, Any
from datetime import datetime

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ..models import Waitlist
from src.domains.shared.interfaces.waitlist_service import WaitlistServiceInterface
from src.domains.shared.events.publisher import DomainEventPublisher
from src.infrastructure.events.dispatcher import get_event_dispatcher


class WaitlistService(WaitlistServiceInterface):
    def __init__(self, db_session: Session):
        self.db = db_session

        # Initialize event publishing
        try:
            dispatcher = get_event_dispatcher()
            self.event_publisher = DomainEventPublisher(dispatcher, "waitlist")
        except RuntimeError:
            # Event dispatcher not initialized, disable events
            self.event_publisher = None

    def add_to_waitlist_by_email(self, email: str) -> Waitlist:
        """Adds a new email to the waitlist.

        Args:
            email: The email address to add.

        Returns:
            The created Waitlist object.

        Raises:
            IntegrityError: If the email already exists.
        """
        try:
            waitlist_entry = Waitlist(email=email)
            self.db.add(waitlist_entry)
            self.db.commit()
            self.db.refresh(waitlist_entry)

            # Publish waitlist signup event
            if self.event_publisher:
                try:
                    import asyncio
                    asyncio.create_task(self.event_publisher.publish_event(
                        "user_added_to_waitlist",
                        str(waitlist_entry.id),
                        {
                            "waitlist_id": str(waitlist_entry.id),
                            "email": email,
                            "created_at": waitlist_entry.created_at.isoformat(),
                        }
                    ))

                    # Publish integration event for marketing/notification
                    asyncio.create_task(self.event_publisher.publish_integration_event(
                        "waitlist_signup",
                        str(waitlist_entry.id),
                        {
                            "email": email,
                            "signup_date": waitlist_entry.created_at.isoformat(),
                        }
                    ))
                except Exception as e:
                    print(f"Warning: Failed to publish waitlist signup event: {e}")

            return waitlist_entry
        except IntegrityError:
            self.db.rollback()
            raise

    # Interface implementation methods
    async def add_to_waitlist(self, user_id: str, league_id: str) -> Dict[str, Any]:
        """Add a user to a league's waitlist."""
        # For now, create a simple waitlist entry representation
        # In the future, this would handle league-specific waitlists
        entry = {
            "entry_id": str(uuid.uuid4()),
            "user_id": user_id,
            "league_id": league_id,
            "position": 1,  # Placeholder position
            "created_at": datetime.now().isoformat(),
            "status": "waiting",
        }
        return entry

    async def process_waitlist_invite(self, invite_id: str) -> bool:
        """Process a waitlist invitation (accept/decline)."""
        # For now, return True as a placeholder
        # In the future, this would handle actual invite processing
        return True

    async def get_waitlist_position(self, entry_id: str) -> int:
        """Get the current position of a waitlist entry."""
        # For now, return position 1 as placeholder
        # In the future, this would calculate actual position
        return 1

    async def get_league_waitlist(self, league_id: str) -> List[Dict[str, Any]]:
        """Get all waitlist entries for a league, ordered by position."""
        # For now, return empty list
        # In the future, this would query league-specific waitlist entries
        return []

    async def remove_from_waitlist(self, entry_id: str) -> bool:
        """Remove an entry from the waitlist."""
        # For now, return True as placeholder
        # In the future, this would handle actual removal
        return True

    async def send_waitlist_invite(self, entry_id: str) -> Dict[str, Any]:
        """Send an invitation to a waitlisted user."""
        # For now, return a placeholder invite
        invite = {
            "invite_id": str(uuid.uuid4()),
            "entry_id": entry_id,
            "sent_at": datetime.now().isoformat(),
            "expires_at": datetime.now().isoformat(),
            "status": "sent",
        }
        return invite

    async def get_user_waitlist_status(
        self, user_id: str, league_id: str
    ) -> Optional[Dict[str, Any]]:
        """Get user's waitlist status for a specific league."""
        # For now, return None (user not on waitlist)
        # In the future, this would check actual waitlist status
        return None
