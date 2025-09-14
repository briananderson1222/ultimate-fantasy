from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from models.user import User


class UserService:
    def __init__(self, session: Session) -> None:
        self.session = session

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
        display_name = str(
            claims.get("name")
            or claims.get("preferred_username")
            or email
            or f"User-{sub[:8]}"
        )

        existing = (
            self.session.query(User).filter(User.user_id == user_id).one_or_none()
        )
        if existing:
            # Update basic fields if changed
            changed = False
            if existing.email != email:
                existing.email = email
                changed = True
            if existing.display_name != display_name:
                existing.display_name = display_name
                changed = True
            if changed:
                self.session.add(existing)
                self.session.flush()
            return existing

        user = User(
            user_id=user_id, email=email, display_name=display_name, cognito_sub=sub
        )
        self.session.add(user)
        self.session.flush()
        return user
