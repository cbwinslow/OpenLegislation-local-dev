from pydantic import BaseModel
from typing import Dict, Optional
from datetime import date

from .agenda_id import AgendaId

class Agenda(BaseModel):
    id: AgendaId
    agenda_info_addenda: Dict[str, str] = {}  # Map<String, AgendaInfoAddendum>
    agenda_vote_addenda: Dict[str, str] = {}  # Map<String, AgendaVoteAddendum>

    def get_agenda_info_addendum(self, addendum_id: str) -> Optional[str]:
        return self.agenda_info_addenda.get(addendum_id)

    def put_agenda_info_addendum(self, addendum: str, addendum_id: str):
        self.agenda_info_addenda[addendum_id] = addendum

    def get_agenda_vote_addendum(self, addendum_id: str) -> Optional[str]:
        return self.agenda_vote_addenda.get(addendum_id)

    def put_agenda_vote_addendum(self, addendum: str, addendum_id: str):
        self.agenda_vote_addenda[addendum_id] = addendum

    def get_week_of(self) -> Optional[date]:
        # Simplified - in real implementation, extract from addenda
        for addendum in self.agenda_info_addenda.values():
            return date.today()  # placeholder
        return None

    def __str__(self):
        return f"Agenda {self.id}"