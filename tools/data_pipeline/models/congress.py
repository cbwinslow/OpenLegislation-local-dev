"""Data models for api.congress.gov responses."""
from __future__ import annotations

from datetime import date, datetime
from typing import List, Optional

from pydantic import Field

from .base import TimestampedModel


class CongressMember(TimestampedModel):
    bioguide_id: str = Field(..., description="Bioguide identifier for the member.")
    first_name: str
    last_name: str
    party: Optional[str] = Field(None, description="Political party abbreviation.")
    chamber: Optional[str] = Field(None, description="House or Senate.")
    state: Optional[str] = Field(None, description="Two-letter state abbreviation.")
    district: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None


class CongressBill(TimestampedModel):
    congress: str = Field(..., description="Congress session number.")
    bill_type: str = Field(..., description="Type of bill (hr, s, hjres, etc.).")
    bill_number: str = Field(..., description="Numeric portion of the bill identifier.")
    title: Optional[str] = None
    sponsor_bioguide_id: Optional[str] = None
    introduced_date: Optional[date] = None
    latest_action_date: Optional[date] = None
    latest_action_text: Optional[str] = None
    subjects: List[str] = Field(default_factory=list)

    @property
    def bill_id(self) -> str:
        return f"{self.bill_type.upper()}{self.bill_number}-{self.congress}"


class CongressVote(TimestampedModel):
    chamber: str
    congress: str
    session: Optional[str] = None
    roll_call: str
    vote_date: datetime
    question: Optional[str] = None
    description: Optional[str] = None
    result: Optional[str] = None
    yeas: int = 0
    nays: int = 0
    present: int = 0
    not_voting: int = 0

