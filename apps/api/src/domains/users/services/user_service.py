from __future__ import annotations

import uuid as _uuid
from typing import Any

from sqlalchemy.orm import Session

from domains.shared.events.publisher import DomainEventPublisher
from domains.shared.interfaces.user_service import UserServiceInterface
from domains.users.models.user import User
from infrastructure.events.dispatcher import get_event_dispatcher


class UserService(UserServiceInterface):
    def __init__(self, session: Session) -> None:
        self.session = session

        # Initialize event publishing
        try:
            dispatcher = get_event_dispatcher()
            self.event_publisher: DomainEventPublisher | None = DomainEventPublisher(
                dispatcher, "users"
            )
        except RuntimeError:
            # Event dispatcher not initialized, disable events
            self.event_publisher = None

    def ensure_user_from_claims(self, claims: dict[str, Any]) -> User:
        """Upsert a User based on JWT claims.

        - Uses `sub` as both user_id and cognito_sub for consistency.
        - Uses `email` and `name` claims when available.
        """
        import uuid as _uuid

        sub = str(claims.get("sub", ""))
        if not sub:
            raise ValueError("missing sub in claims")

        try:
            user_id = _uuid.UUID(sub)
        except ValueError:
            raise ValueError(f"sub must be a valid UUID, got: {sub}")

        email = str(claims.get("email") or "").strip() or f"{sub}@example.dev"
        preferred_username = claims.get("preferred_username") or claims.get("nickname")
        display_name = str(preferred_username or claims.get("name") or email or f"User-{sub[:8]}")
        username = str(preferred_username or display_name or f"user_{sub[:8]}").strip() or f"user_{sub[:8]}"
        username = username.replace(" ", "_")[:50]

        existing = (
            self.session.query(User).filter(User.user_id == user_id).one_or_none()
        )
        if existing:
            # Update basic fields if changed
            changed = False
            if not existing.username:
                existing.username = username
                changed = True
            if existing.email != email:
                existing.email = email
                changed = True
            if existing.display_name != display_name:
                existing.display_name = display_name
                changed = True
            if changed:
                self.session.add(existing)
                self.session.flush()

                # Publish user updated event
                if self.event_publisher:
                    try:
                        import asyncio

                        task = asyncio.create_task(
                            self.event_publisher.publish_event(
                                "user_updated",
                                str(user_id),
                                {
                                    "user_id": str(user_id),
                                    "email": email,
                                    "display_name": display_name,
                                    "changes": (
                                        ["email", "display_name"] if changed else []
                                    ),
                                },
                            )
                        )
                        task.add_done_callback(lambda t: t.exception())
                    except Exception as e:
                        import logging

                        logging.getLogger(__name__).debug(
                            f"Event publishing failed: {e}"
                        )

            return existing

        user = User(
            user_id=user_id,
            username=username,
            email=email,
            display_name=display_name,
            cognito_sub=sub,
            password_hash="",  # placeholder until legacy auth merged
        )
        self.session.add(user)
        self.session.flush()

        # Publish user created event
        if self.event_publisher:
            try:
                import asyncio

                task = asyncio.create_task(
                    self.event_publisher.publish_event(
                        "user_created",
                        str(user_id),
                        {
                            "user_id": str(user_id),
                            "email": email,
                            "display_name": display_name,
                            "cognito_sub": sub,
                        },
                    )
                )
                task.add_done_callback(lambda t: t.exception())

                # Publish integration event for other domains
                task = asyncio.create_task(
                    self.event_publisher.publish_integration_event(
                        "user_created",
                        str(user_id),
                        {
                            "user_id": str(user_id),
                            "email": email,
                            "display_name": display_name,
                        },
                        target_domains=["leagues", "lineups", "trading", "waitlist"],
                    )
                )
                task.add_done_callback(lambda t: t.exception())
            except Exception as e:
                import logging

                logging.getLogger(__name__).debug(f"Event publishing failed: {e}")

        return user

    # Interface implementation methods
    async def get_user(self, user_id: str) -> User:
        """Get user by ID."""
        user_uuid = _uuid.UUID(user_id)
        user = self.session.query(User).filter(User.user_id == user_uuid).first()
        if not user:
            raise ValueError(f"User with ID {user_id} not found")
        return user

    async def validate_user_permissions(
        self, user_id: str, resource: str, action: str = "read"
    ) -> bool:
        """Validate user permissions for a specific resource and action."""
        # Basic implementation - check if user exists and is active
        user_uuid = _uuid.UUID(user_id)
        user = self.session.query(User).filter(User.user_id == user_uuid).first()
        if not user:
            return False

        # For now, all active users have read permissions
        # More complex permission logic can be added later
        return action == "read"

    async def get_user_preferences(self, user_id: str) -> User:
        """Get user preferences and settings."""
        # For now, return the user object which includes preferences
        # In the future, this could return a separate UserPreferences object
        return await self.get_user(user_id)

    async def get_user_by_email(self, email: str) -> User | None:
        """Get user by email address."""
        user = self.session.query(User).filter(User.email == email).first()
        return user

    async def is_user_active(self, user_id: str) -> bool:
        """Check if user account is active."""
        try:
            await self.get_user(user_id)
            # Assume all users are active for now
            # In the future, add an 'active' field to the User model
            return True
        except ValueError:
            return False
