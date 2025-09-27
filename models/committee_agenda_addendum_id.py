from pydantic import BaseModel
from typing import Optional

from .committee_agenda_id import CommitteeAgendaId
from .agenda_id import AgendaId
from .committee_id import CommitteeId
from .version import Version

class CommitteeAgendaAddendumId(CommitteeAgendaId):
    addendum: Optional[Version] = None

    def __init__(self, agenda_id: Optional[AgendaId] = None,
                 committee_id: Optional[CommitteeId] = None,
                 addendum: Optional[Version] = None, **data):
        super().__init__(agenda_id=agenda_id, committee_id=committee_id, **data)
        self.addendum = addendum

    def __eq__(self, other):
        if self is other:
            return True
        if not isinstance(other, CommitteeAgendaAddendumId):
            return False
        if not super().__eq__(other):
            return False
        return self.addendum == other.addendum

    def __hash__(self):
        return hash((super().__hash__(), self.addendum))

    def __str__(self):
        return f"{super().__str__()}-{self.addendum.name() if self.addendum else ''}"

    def __lt__(self, other: 'CommitteeAgendaId'):
        super_result = super().__lt__(other)
        if super_result == 0 and isinstance(other, CommitteeAgendaAddendumId):
            return self.addendum < other.addendum if self.addendum and other.addendum else False
        return super_result

    # Getters
    def get_addendum(self) -> Optional[Version]:
        return self.addendum