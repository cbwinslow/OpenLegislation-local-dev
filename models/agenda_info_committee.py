from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

from .agenda_id import AgendaId
from .committee_id import CommitteeId
from .version import Version
from .agenda_info_committee_item import AgendaInfoCommitteeItem

class AgendaInfoCommittee(BaseModel):
    committee_id: Optional[CommitteeId] = None
    agenda_id: Optional[AgendaId] = None
    addendum: Optional[Version] = None
    chair: Optional[str] = None
    location: Optional[str] = None
    meeting_date_time: Optional[datetime] = None
    notes: Optional[str] = None
    items: List[AgendaInfoCommitteeItem] = []

    # Functional Getters/Setters
    def add_committee_item(self, item: AgendaInfoCommitteeItem):
        self.items.append(item)

    def __eq__(self, other):
        if not isinstance(other, AgendaInfoCommittee):
            return False
        return (self.committee_id == other.committee_id and
                self.chair == other.chair and
                self.location == other.location and
                self.meeting_date_time == other.meeting_date_time and
                self.notes == other.notes and
                self.items == other.items)

    def __hash__(self):
        return hash((self.committee_id, self.chair, self.location,
                    self.meeting_date_time, self.notes, tuple(self.items)))

    def __str__(self):
        return f"{self.committee_id} meetingDateTime: {self.meeting_date_time}"

    # Basic Getters/Setters
    def get_committee_id(self) -> Optional[CommitteeId]:
        return self.committee_id

    def set_committee_id(self, committee_id: CommitteeId):
        self.committee_id = committee_id

    def get_agenda_id(self) -> Optional[AgendaId]:
        return self.agenda_id

    def set_agenda_id(self, agenda_id: AgendaId):
        self.agenda_id = agenda_id

    def get_addendum(self) -> Optional[Version]:
        return self.addendum

    def set_addendum(self, addendum: Version):
        self.addendum = addendum

    def get_chair(self) -> Optional[str]:
        return self.chair

    def set_chair(self, chair: str):
        self.chair = chair

    def get_location(self) -> Optional[str]:
        return self.location

    def set_location(self, location: str):
        self.location = location

    def get_meeting_date_time(self) -> Optional[datetime]:
        return self.meeting_date_time

    def set_meeting_date_time(self, meeting_date_time: datetime):
        self.meeting_date_time = meeting_date_time

    def get_notes(self) -> Optional[str]:
        return self.notes

    def set_notes(self, notes: str):
        self.notes = notes

    def get_items(self) -> List[AgendaInfoCommitteeItem]:
        return self.items

    def set_items(self, items: List[AgendaInfoCommitteeItem]):
        self.items = items