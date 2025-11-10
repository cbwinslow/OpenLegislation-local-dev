"""OpenStates data models."""
from __future__ import annotations

from datetime import date, datetime
from typing import List, Optional

from pydantic import Field

from .base import TimestampedModel


class OpenStatesPerson(TimestampedModel):
    id: str
    name: str
    given_name: Optional[str] = None
    family_name: Optional[str] = None
    party: Optional[str] = None
    chamber: Optional[str] = Field(None, description="Legislative chamber.")
    state: Optional[str] = None
    district: Optional[str] = None
    email: Optional[str] = None


class OpenStatesBill(TimestampedModel):
    id: str
    identifier: str
    legislative_session: str
    title: str
    classification: List[str] = Field(default_factory=list)
    subject: List[str] = Field(default_factory=list)
    first_action_date: Optional[date] = None
    last_action_date: Optional[date] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    primary_sponsor: Optional[str] = None


class OpenStatesVoteEvent(TimestampedModel):
    id: str
    bill_id: str
    organization: Optional[str] = None
    motion_text: Optional[str] = None
    motion_classification: List[str] = Field(default_factory=list)
    result: Optional[str] = None
    start_date: Optional[datetime] = None
    counts: List[dict] = Field(default_factory=list)

