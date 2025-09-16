from __future__ import annotations

import uuid as _uuid

from sqlalchemy import JSON, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from src.domains.shared.models.base import Base, TimestampMixin


class UserPreference(TimestampMixin, Base):
    __tablename__ = "user_preferences"

    user_id: Mapped[_uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.user_id"), primary_key=True
    )
    theme: Mapped[str] = mapped_column(String(20), default="light", nullable=False)
    density: Mapped[str] = mapped_column(
        String(20), default="comfortable", nullable=False
    )
    locale: Mapped[str] = mapped_column(String(20), default="en-US", nullable=False)
    layouts: Mapped[dict | None] = mapped_column(JSON, nullable=True)
