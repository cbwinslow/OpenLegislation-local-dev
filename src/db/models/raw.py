from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import Integer, PrimaryKeyConstraint, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from ..base import Base


class GovInfoRawPayload(Base):
    __tablename__ = "govinfo_raw_payload"
    __table_args__ = (
        PrimaryKeyConstraint("id"),
        {"schema": "master"},
    )

    id: Mapped[int] = mapped_column(Integer)
    ingestion_type: Mapped[str] = mapped_column(String(64))
    record_id: Mapped[str] = mapped_column(String)
    source_path: Mapped[Optional[str]] = mapped_column(String)
    payload: Mapped[dict] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)

