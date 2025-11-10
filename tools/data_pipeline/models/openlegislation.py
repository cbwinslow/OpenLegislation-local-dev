"""New York OpenLegislation data models."""
from __future__ import annotations

from datetime import date, datetime
from typing import List, Optional

from pydantic import Field

from .base import TimestampedModel


class OpenLegislationBill(TimestampedModel):
    print_no: str = Field(..., description="Bill print number (e.g., S1234).")
    session: str = Field(..., description="Legislative session year.")
    title: Optional[str] = None
    sponsor_member_id: Optional[int] = None
    summary: Optional[str] = None
    law_section: Optional[str] = None
    last_status: Optional[str] = None
    last_status_date: Optional[date] = None
    committee_name: Optional[str] = None
    cosponsors: List[str] = Field(default_factory=list)


class OpenLegislationAgenda(TimestampedModel):
    agenda_id: str
    meeting_date: Optional[date] = None
    committee_name: Optional[str] = None
    location: Optional[str] = None
    notes: Optional[str] = None
    bills: List[str] = Field(default_factory=list)
    published_at: Optional[datetime] = None

