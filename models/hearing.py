from __future__ import annotations
from typing import Optional, Set, List
from datetime import date, time
from enum import Enum
from pydantic import BaseModel, Field

# --- Enums and Value Objects ---

class HearingHostType(str, Enum):
    COMMITTEE = "COMMITTEE"
    LEGISLATIVE_COMMISSION = "LEGISLATIVE_COMMISSION"
    TASK_FORCE = "TASK_FORCE"
    MAJORITY_COALITION = "MAJORITY_COALITION"
    WHOLE_CHAMBER = "WHOLE_CHAMBER"

    @staticmethod
    def to_type(type_str: str) -> "HearingHostType":
        return HearingHostType(type_str.strip().replace(" ", "_").upper())

class HearingId(BaseModel):
    id: int
    def __str__(self):
        return str(self.id)
    def __eq__(self, other):
        return self.id == other.id
    def __lt__(self, other):
        return self.id < other.id

class HearingHost(BaseModel):
    chamber: str  # Should match Chamber enum from committee domain
    type: HearingHostType
    name: str
    @staticmethod
    def standardize_name(name: str) -> str:
        import re
        IRRELEVANT_TEXT = r"^(\s?(ON|FOR|THE|AND|,))+|((,|THE|AND|;)\s?)+$"
        return (
            name.upper().replace("  ", " ").replace(", AND", " AND")
            .replace(" &", " AND").strip()
            .replace("\n", " ")
        )
    @staticmethod
    def get_hosts(type_str: str, raw_name: str, chamber: Optional[str]) -> List["HearingHost"]:
        hosts = []
        if chamber is None:
            hosts.extend(HearingHost.get_hosts(type_str, raw_name, "SENATE"))
            hosts.extend(HearingHost.get_hosts(type_str, raw_name, "ASSEMBLY"))
            return hosts
        type_enum = HearingHostType.to_type(type_str)
        standardized_text = HearingHost.standardize_name(raw_name)
        for host_text in standardized_text.split(";"):
            hosts.append(HearingHost(chamber=chamber, type=type_enum, name=host_text.strip()))
        return hosts

# --- Main Model ---

class Hearing(BaseModel):
    id: Optional[HearingId] = None
    filename: str
    text: str
    title: str
    address: str
    date: date
    start_time: Optional[time] = None
    end_time: Optional[time] = None
    hosts: Optional[Set[HearingHost]] = None
    session_year: int = Field(..., description="Year of the hearing")

    def __eq__(self, other):
        if not isinstance(other, Hearing):
            return False
        return (
            self.id == other.id and
            self.filename == other.filename and
            self.text == other.text and
            self.title == other.title and
            self.address == other.address and
            self.date == other.date and
            self.start_time == other.start_time and
            self.end_time == other.end_time and
            self.hosts == other.hosts
        )
    def __hash__(self):
        return hash((self.id, self.filename, self.text, self.title, self.address, self.date, self.start_time, self.end_time, tuple(self.hosts) if self.hosts else None))

# --- Exceptions ---

class HearingNotFoundEx(Exception):
    def __init__(self, id: Optional[HearingId] = None, filename: Optional[str] = None, ex: Optional[Exception] = None):
        msg = f"Hearing {(id if id is not None else filename)} could not be retrieved."
        super().__init__(msg)
        self.id = id
        self.filename = filename
        self.__cause__ = ex
