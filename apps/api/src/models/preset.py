from __future__ import annotations

import uuid as _uuid

from sqlalchemy import JSON, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class Preset(Base):
    __tablename__ = "presets"

    preset_id: Mapped[_uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=_uuid.uuid4
    )
    sport: Mapped[str] = mapped_column(String(50), nullable=False)
    league_type: Mapped[str] = mapped_column(String(50), nullable=False)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    rules: Mapped[dict] = mapped_column(JSON, nullable=False)
