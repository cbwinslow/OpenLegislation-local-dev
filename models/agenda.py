from functools import total_ordering
from pydantic import BaseModel
from models.committee import CommitteeId

@total_ordering
class AgendaId(BaseModel):
    """
    AgendaId is a simple wrapper used to uniquely identify an Agenda instance.
    """
    number: int
    year: int

    def __str__(self):
        return f"{self.year}-{self.number}"

    def __eq__(self, other):
        if not isinstance(other, AgendaId):
            return NotImplemented
        return self.year == other.year and self.number == other.number

    def __hash__(self):
        return hash((self.year, self.number))

    def __lt__(self, other):
        if not isinstance(other, AgendaId):
            return NotImplemented
        if self.year != other.year:
            return self.year < other.year
        return self.number < other.number

    class Config:
        frozen = True
        arbitrary_types_allowed = True

@total_ordering
class CommitteeAgendaId(BaseModel):
    """
    Identifies a specific committee within an agenda.
    """
    agenda_id: AgendaId
    committee_id: CommitteeId

    def __str__(self):
        return f"{self.agenda_id}-{self.committee_id}"

    def __eq__(self, other):
        if not isinstance(other, CommitteeAgendaId):
            return NotImplemented
        return self.agenda_id == other.agenda_id and self.committee_id == other.committee_id

    def __hash__(self):
        return hash((self.agenda_id, self.committee_id))

    def __lt__(self, other):
        if not isinstance(other, CommitteeAgendaId):
            return NotImplemented
        if self.agenda_id != other.agenda_id:
            return self.agenda_id < other.agenda_id
        return self.committee_id < other.committee_id

    class Config:
        frozen = True
        arbitrary_types_allowed = True