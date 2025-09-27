from pydantic import BaseModel
from typing import Dict, Optional
from datetime import date, datetime

from .agenda_id import AgendaId
from .base_legislative_content import BaseLegislativeContent
from .session_year import SessionYear
from .committee_id import CommitteeId
from .agenda_info_committee import AgendaInfoCommittee

class AgendaInfoAddendum(BaseLegislativeContent):
    agenda_id: Optional[AgendaId] = None
    id: Optional[str] = None
    week_of: Optional[date] = None
    committee_info_map: Dict[CommitteeId, AgendaInfoCommittee] = {}

    def __init__(self, **data):
        super().__init__(**data)
        if not self.committee_info_map:
            self.committee_info_map = {}

    # Functional Getters/Setters
    def put_committee(self, info_committee: AgendaInfoCommittee):
        self.committee_info_map[info_committee.get_committee_id()] = info_committee

    def get_committee(self, committee_id: CommitteeId) -> Optional[AgendaInfoCommittee]:
        return self.committee_info_map.get(committee_id)

    def remove_committee(self, committee_id: CommitteeId):
        self.committee_info_map.pop(committee_id, None)

    def __eq__(self, other):
        if not isinstance(other, AgendaInfoAddendum):
            return False
        return (self.year == other.year and
                self.agenda_id == other.agenda_id and
                self.id == other.id and
                self.week_of == other.week_of and
                self.committee_info_map == other.committee_info_map)

    def __hash__(self):
        return hash((self.year, self.agenda_id, self.id, self.week_of,
                    tuple(sorted(self.committee_info_map.items()))))

    # Basic Getters/Setters
    def get_agenda_id(self) -> Optional[AgendaId]:
        return self.agenda_id

    def set_agenda_id(self, agenda_id: AgendaId):
        self.agenda_id = agenda_id
        self.set_year(agenda_id.get_year())
        self.set_session(SessionYear.of(self.get_year()))

    def get_id(self) -> Optional[str]:
        return self.id

    def set_id(self, id: str):
        self.id = id

    def get_week_of(self) -> Optional[date]:
        return self.week_of

    def set_week_of(self, week_of: date):
        self.week_of = week_of

    def get_committee_info_map(self) -> Dict[CommitteeId, AgendaInfoCommittee]:
        return self.committee_info_map

    def set_committee_info_map(self, committee_info_map: Dict[CommitteeId, AgendaInfoCommittee]):
        self.committee_info_map = committee_info_map