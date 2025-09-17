from __future__ import annotations

import uuid as _uuid
from datetime import date

from sqlalchemy import JSON, Date, ForeignKey, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from domains.shared.models.base import Base


class Lineup(Base):
    __tablename__ = "lineups"

    lineup_id: Mapped[_uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=_uuid.uuid4
    )
    team_id: Mapped[_uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("teams.team_id"), nullable=False
    )
    game_day: Mapped[date] = mapped_column(Date, nullable=False)
    # Stores the submitted list of players for the lineup
    players: Mapped[list[dict]] = mapped_column(JSON, nullable=False)
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
