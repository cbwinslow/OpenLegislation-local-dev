from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime, time
from sortedcontainers import SortedList
from enum import Enum

from .base_legislative_content import BaseLegislativeContent
from .chamber import Chamber
from .committee_id import CommitteeId
from .committee_session_id import CommitteeSessionId
from .committee_version_id import CommitteeVersionId
from .committee_member import CommitteeMember

class DayOfWeek(Enum):
    MONDAY = "MONDAY"
    TUESDAY = "TUESDAY"
    WEDNESDAY = "WEDNESDAY"
    THURSDAY = "THURSDAY"
    FRIDAY = "FRIDAY"
    SATURDAY = "SATURDAY"
    SUNDAY = "SUNDAY"

class Committee(BaseLegislativeContent):
    name: Optional[str] = None
    chamber: Optional[Chamber] = None
    reformed: Optional[datetime] = None
    location: Optional[str] = None
    meet_day: Optional[DayOfWeek] = None
    meet_time: Optional[time] = None
    meet_alt_week: bool = False
    meet_alt_week_text: Optional[str] = None
    members: SortedList = SortedList()  # TreeMultiset equivalent

    def __init__(self, **data):
        super().__init__(**data)
        if not isinstance(self.members, SortedList):
            self.members = SortedList(self.members or [])

    def __eq__(self, other):
        if not isinstance(other, Committee):
            return False
        return (self.name == other.name and
                self.chamber == other.chamber and
                self.reformed == other.reformed and
                self.location == other.location and
                self.meet_day == other.meet_day and
                self.meet_time == other.meet_time and
                self.meet_alt_week == other.meet_alt_week and
                self.meet_alt_week_text == other.meet_alt_week_text and
                self.members == other.members)

    def __hash__(self):
        return hash((self.name, self.chamber, self.reformed, self.location,
                    self.meet_day, self.meet_time, self.meet_alt_week,
                    self.meet_alt_week_text, tuple(self.members)))

    def members_equals(self, other: 'Committee') -> bool:
        return (other is not None and
                self.name == other.name and
                self.session == other.session and
                len(self.members) == len(other.members) and
                all(member in other.members for member in self.members))

    def meeting_equals(self, other: 'Committee') -> bool:
        return (other is not None and
                self.name == other.name and
                self.session == other.session and
                self.location == other.location and
                self.meet_day == other.meet_day and
                self.meet_time == other.meet_time and
                self.meet_alt_week == other.meet_alt_week and
                self.meet_alt_week_text == other.meet_alt_week_text)

    # Helper functions
    def is_current(self) -> bool:
        # The current Committee should have a reformed date of 'infinity'
        return self.reformed is None or self.reformed > datetime.now()

    def update_meeting_info(self, updated_committee: 'Committee'):
        self.location = updated_committee.location
        self.meet_day = updated_committee.meet_day
        self.meet_time = updated_committee.meet_time
        self.meet_alt_week = updated_committee.meet_alt_week
        self.meet_alt_week_text = updated_committee.meet_alt_week_text

    # Functional Getters/Setters
    def get_id(self) -> CommitteeId:
        return CommitteeId(self.chamber, self.name)

    def get_session_id(self) -> CommitteeSessionId:
        return CommitteeSessionId(self.chamber, self.name, self.session)

    def get_version_id(self) -> CommitteeVersionId:
        return CommitteeVersionId(self.chamber, self.name, self.session, self.published_date_time)

    def add_member(self, member: CommitteeMember):
        self.members.add(member)

    def get_created(self) -> Optional[datetime]:
        return self.published_date_time

    # Basic Getters/Setters
    def get_name(self) -> Optional[str]:
        return self.name

    def set_name(self, name: str):
        self.name = name

    def get_chamber(self) -> Optional[Chamber]:
        return self.chamber

    def set_chamber(self, chamber: Chamber):
        self.chamber = chamber

    def get_reformed(self) -> Optional[datetime]:
        return self.reformed

    def set_reformed(self, reformed: datetime):
        self.reformed = reformed

    def get_location(self) -> Optional[str]:
        return self.location

    def set_location(self, location: str):
        self.location = location

    def get_meet_day(self) -> Optional[DayOfWeek]:
        return self.meet_day

    def set_meet_day(self, meet_day: DayOfWeek):
        self.meet_day = meet_day

    def get_meet_time(self) -> Optional[time]:
        return self.meet_time

    def set_meet_time(self, meet_time: time):
        self.meet_time = meet_time

    def is_meet_alt_week(self) -> bool:
        return self.meet_alt_week

    def set_meet_alt_week(self, meet_alt_week: bool):
        self.meet_alt_week = meet_alt_week

    def get_meet_alt_week_text(self) -> Optional[str]:
        return self.meet_alt_week_text

    def set_meet_alt_week_text(self, meet_alt_week_text: str):
        self.meet_alt_week_text = meet_alt_week_text

    def get_members(self) -> List[CommitteeMember]:
        return list(self.members)

    def set_members(self, members: List[CommitteeMember]):
        self.members = SortedList(members)