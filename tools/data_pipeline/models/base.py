"""Shared base utilities for Pydantic models."""
from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, Mapping, Optional

from pydantic import BaseModel, Field, root_validator


class TimestampedModel(BaseModel):
    """Base model that normalizes timestamps and keeps raw payloads."""

    source_updated: Optional[datetime] = Field(
        None, description="Timestamp when the source data was last updated."
    )
    retrieved_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="Timestamp when the payload was retrieved from the API.",
    )
    raw_payload: Optional[Mapping[str, Any]] = Field(
        None,
        description="Original payload as returned by the external API for auditing.",
    )

    class Config:
        arbitrary_types_allowed = True
        orm_mode = True

    @root_validator(pre=True)
    def _capture_raw_payload(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        if "raw_payload" not in values:
            values["raw_payload"] = values.copy()
        return values

