from __future__ import annotations

import uuid as _uuid
from datetime import date

from sqlalchemy import JSON, Date, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class Score(Base):
    __tablename__ = "scores"

    score_id: Mapped[_uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=_uuid.uuid4
    )
    player_id: Mapped[_uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("players.player_id"), nullable=False
    )
    game_day: Mapped[date] = mapped_column(Date, nullable=False)
    stats: Mapped[dict] = mapped_column(JSON, nullable=False)
