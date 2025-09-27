from __future__ import annotations

from functools import total_ordering
from typing import Optional

from pydantic import BaseModel, field_validator

from .chamber import Chamber


@total_ordering
class CommitteeId(BaseModel):
    chamber: Chamber
    name: str

    model_config = {
        "validate_assignment": True,
        "frozen": True,
    }

    @field_validator("name")
    @classmethod
    def _validate_name(cls, value: str) -> str:
        if value is None:
            raise ValueError("Committee name cannot be None")
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("Committee name cannot be empty")
        return cleaned

    @field_validator("chamber")
    @classmethod
    def _validate_chamber(cls, value: Optional[Chamber]) -> Chamber:
        if value is None:
            raise ValueError("Committee chamber cannot be None")
        return value

    def __str__(self) -> str:
        return f"{self.chamber}-{self.name}"

    def __repr__(self) -> str:
        return f"CommitteeId(chamber={self.chamber!r}, name={self.name!r})"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, CommitteeId):
            return NotImplemented
        return (
            self.chamber == other.chamber
            and self.name.lower() == other.name.lower()
        )

    def __hash__(self) -> int:
        return hash((self.chamber, self.name.lower()))

    def __lt__(self, other: "CommitteeId") -> bool:
        if not isinstance(other, CommitteeId):
            return NotImplemented
        if self.chamber.name != other.chamber.name:
            return self.chamber.name < other.chamber.name
        return self.name.lower() < other.name.lower()
