from pydantic import BaseModel
from typing import Dict, List, Optional
from datetime import datetime

from .committee_id import CommitteeId
from .bill_id import BillId
from .agenda_vote_attendance import AgendaVoteAttendance
from .agenda_vote_bill import AgendaVoteBill

class AgendaVoteCommittee(BaseModel):
    committee_id: Optional[CommitteeId] = None
    chair: Optional[str] = None
    meeting_date_time: Optional[datetime] = None
    attendance: List[AgendaVoteAttendance] = []
    voted_bills: Dict[BillId, AgendaVoteBill] = {}

    def __init__(self, **data):
        super().__init__(**data)
        if not self.attendance:
            self.attendance = []
        if not self.voted_bills:
            self.voted_bills = {}

    # Functional Getters/Setters
    def add_vote_bill(self, agenda_vote_bill: AgendaVoteBill):
        self.voted_bills[agenda_vote_bill.get_bill_id()] = agenda_vote_bill

    def remove_vote_bill(self, bill_id: BillId):
        self.voted_bills.pop(bill_id, None)

    def __eq__(self, other):
        if not isinstance(other, AgendaVoteCommittee):
            return False
        return (self.committee_id == other.committee_id and
                self.chair == other.chair and
                self.meeting_date_time == other.meeting_date_time and
                self.attendance == other.attendance and
                self.voted_bills == other.voted_bills)

    def __hash__(self):
        return hash((self.committee_id, self.chair, self.meeting_date_time,
                    tuple(self.attendance), tuple(sorted(self.voted_bills.items()))))

    def __str__(self):
        return f"{self.committee_id} meetingDateTime: {self.meeting_date_time}"

    # Basic Getters/Setters
    def get_committee_id(self) -> Optional[CommitteeId]:
        return self.committee_id

    def set_committee_id(self, committee_id: CommitteeId):
        self.committee_id = committee_id

    def get_chair(self) -> Optional[str]:
        return self.chair

    def set_chair(self, chair: str):
        self.chair = chair

    def get_meeting_date_time(self) -> Optional[datetime]:
        return self.meeting_date_time

    def set_meeting_date_time(self, meeting_date_time: datetime):
        self.meeting_date_time = meeting_date_time

    def get_voted_bills(self) -> Dict[BillId, AgendaVoteBill]:
        return self.voted_bills

    def set_voted_bills(self, voted_bills: Dict[BillId, AgendaVoteBill]):
        self.voted_bills = voted_bills

    def get_attendance(self) -> List[AgendaVoteAttendance]:
        return self.attendance

    def set_attendance(self, attendance: List[AgendaVoteAttendance]):
        self.attendance = attendance

    def add_attendance(self, attendance: AgendaVoteAttendance):
        self.attendance.append(attendance)