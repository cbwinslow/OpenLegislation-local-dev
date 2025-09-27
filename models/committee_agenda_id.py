from pydantic import BaseModel
from typing import Optional

from .agenda_id import AgendaId
from .committee_id import CommitteeId
from .version import Version

class CommitteeAgendaId(BaseModel):
    agenda_id: Optional[AgendaId] = None
    committee_id: Optional[CommitteeId] = None

    def __str__(self):
        return f"{self.agenda_id}-{self.committee_id}"

    def __eq__(self, other):
        if self is other:
            return True
        if not isinstance(other, CommitteeAgendaId):
            return False
        return self.agenda_id == other.agenda_id and self.committee_id == other.committee_id

    def __hash__(self):
        return hash((self.agenda_id, self.committee_id))

    def __lt__(self, other: 'CommitteeAgendaId'):
        if self.agenda_id != other.agenda_id:
            return self.agenda_id < other.agenda_id
        return self.committee_id < other.committee_id

    # Basic Getters/Setters
    def get_agenda_id(self) -> Optional[AgendaId]:
        return self.agenda_id

    def get_committee_id(self) -> Optional[CommitteeId]:
        return self.committee_id