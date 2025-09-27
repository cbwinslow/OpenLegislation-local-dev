from pydantic import BaseModel
from typing import Optional

from .session_member import SessionMember

class AgendaVoteAttendance(BaseModel):
    member: Optional[SessionMember] = None
    rank: int = 0
    party: Optional[str] = None
    attend_status: Optional[str] = None

    def __eq__(self, other):
        if not isinstance(other, AgendaVoteAttendance):
            return False
        return (self.member == other.member and
                self.rank == other.rank and
                self.party == other.party and
                self.attend_status == other.attend_status)

    def __hash__(self):
        return hash((self.member, self.rank, self.party, self.attend_status))

    def __lt__(self, other: 'AgendaVoteAttendance'):
        return self.rank < other.rank

    # Basic Getters/Setters
    def get_member(self) -> Optional[SessionMember]:
        return self.member

    def set_member(self, member: SessionMember):
        self.member = member

    def get_rank(self) -> int:
        return self.rank

    def set_rank(self, rank: int):
        self.rank = rank

    def get_party(self) -> Optional[str]:
        return self.party

    def set_party(self, party: str):
        self.party = party

    def get_attend_status(self) -> Optional[str]:
        return self.attend_status

    def set_attend_status(self, attend_status: str):
        self.attend_status = attend_status