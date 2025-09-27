from __future__ import annotations

from datetime import date
from typing import Optional

from pydantic import BaseModel, field_validator

from .bill_status_type import BillStatusType
from .committee_id import CommitteeId


class BillStatus(BaseModel):
    status_type: BillStatusType
    action_sequence_no: int = 0
    action_date: Optional[date] = None
    committee_id: Optional[CommitteeId] = None
    calendar_no: Optional[int] = None

    model_config = {
        "validate_assignment": True,
    }

    @field_validator("action_sequence_no")
    @classmethod
    def _validate_sequence(cls, value: int) -> int:
        if value is None:
            raise ValueError("action_sequence_no cannot be None")
        return value

    def __str__(self) -> str:
        committee = f" {self.committee_id}" if self.committee_id else ""
        calendar = f" Cal No: {self.calendar_no}" if self.calendar_no is not None else ""
        date_str = self.action_date.isoformat() if self.action_date else ""
        return f"{self.status_type} ({date_str}){committee}{calendar}"
