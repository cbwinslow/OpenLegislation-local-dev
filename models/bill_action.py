from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from functools import total_ordering
from typing import Optional

from .bill_id import BillId
from .chamber import Chamber


@total_ordering
@dataclass(frozen=True)
class BillAction:
    bill_id: BillId
    date: Optional[date]
    chamber: Optional[Chamber]
    sequence_no: int
    text: str
    action_type: Optional[str] = None

    def __post_init__(self):
        if self.bill_id is None:
            raise ValueError("BillAction requires bill_id")
        if self.text is None:
            object.__setattr__(self, "text", "")
        if self.sequence_no is None:
            object.__setattr__(self, "sequence_no", 0)

    def __str__(self) -> str:
        chamber = self.chamber.name if self.chamber else ""
        date_str = self.date.isoformat() if self.date else ""
        return f"{date_str} ({chamber}) {self.text}".strip()

    def __lt__(self, other: "BillAction") -> bool:
        if not isinstance(other, BillAction):
            return NotImplemented
        return self.sequence_no < other.sequence_no

    def equals_base(self, other: "BillAction") -> bool:
        return (
            isinstance(other, BillAction)
            and self.bill_id.equals_base(other.bill_id)
            and self.sequence_no == other.sequence_no
            and (self.date or date.min) == (other.date or date.min)
            and (self.chamber or Chamber.SENATE) == (other.chamber or Chamber.SENATE)
            and self.text.lower() == other.text.lower()
        )
