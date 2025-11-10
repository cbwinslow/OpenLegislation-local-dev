"""GovInfo bulk data package models."""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import Field

from .base import TimestampedModel


class GovInfoPackage(TimestampedModel):
    package_id: str = Field(..., description="Unique package identifier.")
    title: Optional[str] = None
    collection_code: Optional[str] = Field(None, description="GovInfo collection code (e.g., BILLS, STATUTE).")
    summary: Optional[str] = None
    congress: Optional[str] = None
    download: Optional[str] = Field(None, description="URL for the primary download link.")
    last_modified: Optional[datetime] = None


class GovInfoDownload(TimestampedModel):
    package_id: str
    format: str
    url: str
    size: Optional[int] = Field(None, description="Content length in bytes.")

