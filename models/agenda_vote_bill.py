from pydantic import BaseModel
from typing import Optional

from .agenda_vote_action import AgendaVoteAction
from .committee_id import CommitteeId
from .bill_vote import BillVote
from .bill_id import BillId

class AgendaVoteBill(BaseModel):
    vote_action: Optional[AgendaVoteAction] = None
    refer_committee: Optional[CommitteeId] = None
    is_with_amendment: bool = False
    bill_vote: Optional[BillVote] = None

    def with_bill_vote(self, bill_vote: BillVote) -> 'AgendaVoteBill':
        return AgendaVoteBill(
            vote_action=self.vote_action,
            refer_committee=self.refer_committee,
            is_with_amendment=self.is_with_amendment,
            bill_vote=bill_vote
        )

    # Functional Getters/Setters
    def get_bill_id(self) -> Optional[BillId]:
        return self.bill_vote.get_bill_id() if self.bill_vote else None