from pydantic import BaseModel
from typing import Dict, List, Optional, Set
from datetime import date, datetime
from collections import OrderedDict
import uuid

from .agenda_id import AgendaId
from .base_legislative_content import BaseLegislativeContent
from .session_year import SessionYear
from .committee_id import CommitteeId
from .version import Version
from .agenda_info_addendum import AgendaInfoAddendum
from .agenda_vote_addendum import AgendaVoteAddendum
from .committee_agenda_addendum_id import CommitteeAgendaAddendumId
from .agenda_vote_committee import AgendaVoteCommittee

class Agenda(BaseLegislativeContent):
    id: Optional[AgendaId] = None
    agenda_info_addenda: Dict[str, AgendaInfoAddendum] = {}
    agenda_vote_addenda: Dict[str, AgendaVoteAddendum] = {}

    def __init__(self, **data):
        super().__init__(**data)
        if not self.agenda_info_addenda:
            self.agenda_info_addenda = OrderedDict()
        if not self.agenda_vote_addenda:
            self.agenda_vote_addenda = OrderedDict()

    def __str__(self):
        return f"Agenda {self.id}"

    def __eq__(self, other):
        if not isinstance(other, Agenda):
            return False
        return (self.year == other.year and
                self.id == other.id and
                self.agenda_info_addenda == other.agenda_info_addenda and
                self.agenda_vote_addenda == other.agenda_vote_addenda and
                self.published_date_time == other.published_date_time)

    def __hash__(self):
        return hash((self.year, self.id, tuple(sorted(self.agenda_info_addenda.items())),
                    tuple(sorted(self.agenda_vote_addenda.items())), self.published_date_time))

    # Functional Getters/Setters
    def get_agenda_info_addendum(self, addendum_id: str) -> Optional[AgendaInfoAddendum]:
        return self.agenda_info_addenda.get(addendum_id)

    def put_agenda_info_addendum(self, addendum: AgendaInfoAddendum):
        self.agenda_info_addenda[addendum.get_id()] = addendum

    def get_agenda_vote_addendum(self, addendum_id: str) -> Optional[AgendaVoteAddendum]:
        return self.agenda_vote_addenda.get(addendum_id)

    def put_agenda_vote_addendum(self, addendum: AgendaVoteAddendum):
        self.agenda_vote_addenda[addendum.get_id()] = addendum

    def get_week_of(self) -> Optional[date]:
        return next((addendum.get_week_of() for addendum in self.agenda_info_addenda.values()
                    if addendum.get_week_of() is not None), None)

    def total_bills_considered(self, committee_id: Optional[CommitteeId] = None) -> int:
        return sum(
            len(ic.get_items()) for ia in self.agenda_info_addenda.values()
            for ic in (ia.get_committee_info_map().values() if committee_id is None
                      else [ia.get_committee_info_map().get(committee_id)] if ia.get_committee_info_map().get(committee_id) else [])
        )

    def total_bills_voted(self, committee_id: Optional[CommitteeId] = None) -> int:
        return sum(
            len(ic.get_voted_bills()) for ia in self.agenda_vote_addenda.values()
            for ic in (ia.get_committee_vote_map().values() if committee_id is None
                      else [ia.get_committee_vote_map().get(committee_id)] if ia.get_committee_vote_map().get(committee_id) else [])
        )

    def total_committees(self) -> int:
        return len({committee_id for ia in self.agenda_info_addenda.values()
                   for committee_id in ia.get_committee_info_map().keys()})

    def has_committee(self, committee_id: CommitteeId) -> bool:
        return any(committee_id in ia.get_committee_info_map() for ia in self.agenda_info_addenda.values())

    def get_committees(self) -> Set[CommitteeId]:
        return {committee_id for ia in self.agenda_info_addenda.values()
               for committee_id in ia.get_committee_info_map().keys()}

    def get_addenda(self) -> Set[str]:
        return set(self.agenda_info_addenda.keys()) | set(self.agenda_vote_addenda.keys())

    def set_id(self, agenda_id: AgendaId):
        self.id = agenda_id
        self.set_year(agenda_id.get_year())

    # Basic Getters/Setters
    def get_id(self) -> Optional[AgendaId]:
        return self.id

    def get_agenda_info_addenda(self) -> Dict[str, AgendaInfoAddendum]:
        return self.agenda_info_addenda

    def set_agenda_info_addenda(self, agenda_info_addenda: Dict[str, AgendaInfoAddendum]):
        self.agenda_info_addenda = agenda_info_addenda

    def get_agenda_vote_addenda(self) -> Dict[str, AgendaVoteAddendum]:
        return self.agenda_vote_addenda

    def set_agenda_vote_addenda(self, agenda_vote_addenda: Dict[str, AgendaVoteAddendum]):
        self.agenda_vote_addenda = agenda_vote_addenda

    # Functional Getters
    def get_committee_agenda_addendum_ids(self) -> List[CommitteeAgendaAddendumId]:
        return [
            CommitteeAgendaAddendumId(
                agenda_info_committee.get_agenda_id(),
                agenda_info_committee.get_committee_id(),
                agenda_info_committee.get_addendum()
            )
            for agenda_info_addendum in self.agenda_info_addenda.values()
            for agenda_info_committee in agenda_info_addendum.get_committee_info_map().values()
        ]

    def get_votes(self) -> Dict[CommitteeAgendaAddendumId, AgendaVoteCommittee]:
        votes = {}
        for addendum in self.agenda_vote_addenda.values():
            for vote_comm in addendum.get_committee_vote_map().values():
                vote_id = CommitteeAgendaAddendumId(
                    self.id, vote_comm.get_committee_id(), Version.of(addendum.get_id())
                )
                votes[vote_id] = vote_comm
        return votes

    def get_votes_for_committee(self, committee_id: CommitteeId) -> List[AgendaVoteCommittee]:
        return [
            vote_comm for addendum in self.agenda_vote_addenda.values()
            for vote_comm in [addendum.get_committee_vote_map().get(committee_id)]
            if vote_comm is not None
        ]