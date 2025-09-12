from __future__ import annotations

import uuid as _uuid
from datetime import datetime

from sqlalchemy import ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class Roster(Base):
    __tablename__ = "rosters"

    roster_id: Mapped[_uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=_uuid.uuid4
    )
    team_id: Mapped[_uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("teams.team_id"), nullable=False
    )
    player_id: Mapped[_uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("players.player_id"), nullable=False
    )
    acquisition_date: Mapped[datetime] = mapped_column(nullable=False)
    acquisition_method: Mapped[str] = mapped_column(String(20), nullable=False)

