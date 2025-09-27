from pydantic import BaseModel
from typing import Dict, Optional
from datetime import datetime

from .agenda_id import AgendaId
from .base_legislative_content import BaseLegislativeContent
from .session_year import SessionYear
from .committee_id import CommitteeId
from .agenda_vote_committee import AgendaVoteCommittee

class AgendaVoteAddendum(BaseLegislativeContent):
    agenda_id: Optional[AgendaId] = None
    id: Optional[str] = None
    committee_vote_map: Dict[CommitteeId, AgendaVoteCommittee] = {}

    def __init__(self, **data):
        super().__init__(**data)
        if not self.committee_vote_map:
            self.committee_vote_map = {}

    # Functional Getters/Setters
    def get_committee(self, committee_id: CommitteeId) -> Optional[AgendaVoteCommittee]:
        return self.committee_vote_map.get(committee_id)

    def put_committee(self, committee: AgendaVoteCommittee):
        self.committee_vote_map[committee.get_committee_id()] = committee

    def remove_committee(self, committee_id: CommitteeId):
        self.committee_vote_map.pop(committee_id, None)

    def __eq__(self, other):
        if not isinstance(other, AgendaVoteAddendum):
            return False
        return (self.agenda_id == other.agenda_id and
                self.id == other.id and
                self.committee_vote_map == other.committee_vote_map)

    def __hash__(self):
        return hash((self.agenda_id, self.id, tuple(sorted(self.committee_vote_map.items()))))

    # Basic Getters/Setters
    def get_agenda_id(self) -> Optional[AgendaId]:
        return self.agenda_id

    def set_agenda_id(self, agenda_id: AgendaId):
        self.agenda_id = agenda_id

    def get_id(self) -> Optional[str]:
        return self.id

    def set_id(self, id: str):
        self.id = id

    def get_committee_vote_map(self) -> Dict[CommitteeId, AgendaVoteCommittee]:
        return self.committee_vote_map

    def set_committee_vote_map(self, committee_vote_map: Dict[CommitteeId, AgendaVoteCommittee]):
        self.committee_vote_map = committee_vote_map