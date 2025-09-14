from __future__ import annotations

import uuid as _uuid

from sqlalchemy import JSON, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, TimestampMixin


class LeagueBranding(TimestampMixin, Base):
    __tablename__ = "league_branding"

    league_id: Mapped[_uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("leagues.league_id"), primary_key=True
    )
    # Map of CSS variables to values
    theme: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    logo_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
