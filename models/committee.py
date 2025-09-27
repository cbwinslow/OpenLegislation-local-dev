from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime, time
from enum import Enum

from .chamber import Chamber

class DayOfWeek(str, Enum):
    MONDAY = "MONDAY"
    TUESDAY = "TUESDAY"
    WEDNESDAY = "WEDNESDAY"
    THURSDAY = "THURSDAY"
    FRIDAY = "FRIDAY"
    SATURDAY = "SATURDAY"
    SUNDAY = "SUNDAY"

class Committee(BaseModel):
    name: str
    chamber: Chamber
    reformed: Optional[datetime] = None
    location: Optional[str] = None
    meet_day: Optional[DayOfWeek] = None
    meet_time: Optional[time] = None
    meet_alt_week: bool = False
    meet_alt_week_text: Optional[str] = None
    members: List[str] = []  # List[CommitteeMember]

    def __init__(self, name: str = None, chamber: Chamber = None, **data):
        super().__init__(name=name, chamber=chamber, **data)

    def members_equals(self, other: 'Committee') -> bool:
        return other is not None and self.name == other.name and self.session == other.session and len(self.members) == len(other.members) and all(m in other.members for m in self.members)

    def meeting_equals(self, other: 'Committee') -> bool:
        return other is not None and self.name == other.name and self.session == other.session and self.location == other.location and self.meet_day == other.meet_day and self.meet_time == other.meet_time and self.meet_alt_week == other.meet_alt_week and self.meet_alt_week_text == other.meet_alt_week_text

    def __str__(self):
        return f"{self.chamber} Committee {self.name}"