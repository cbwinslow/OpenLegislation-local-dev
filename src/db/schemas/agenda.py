from __future__ import annotations

from datetime import date, datetime
from typing import List, Optional

from pydantic import BaseModel

from .bill import SessionMemberSchema


class AgendaInfoCommitteeItemSchema(BaseModel):
    id: int
    bill_print_no: str
    bill_session_year: int
    bill_amend_version: str
    message: Optional[str]

    class Config:
        orm_mode = True


class AgendaInfoCommitteeSchema(BaseModel):
    id: int
    committee_name: str
    committee_chamber: str
    chair: Optional[str]
    location: Optional[str]
    meeting_date_time: datetime
    notes: Optional[str]
    items: List[AgendaInfoCommitteeItemSchema] = []

    class Config:
        orm_mode = True


class AgendaInfoAddendumSchema(BaseModel):
    addendum_id: str
    modified_date_time: Optional[datetime]
    published_date_time: Optional[datetime]
    created_date_time: datetime
    week_of: Optional[date]
    committees: List[AgendaInfoCommitteeSchema] = []

    class Config:
        orm_mode = True


class AgendaVoteCommitteeAttendSchema(BaseModel):
    id: int
    session_year: int
    lbdc_short_name: str
    rank: int
    party: Optional[str]
    attend_status: Optional[str]
    session_member: SessionMemberSchema

    class Config:
        orm_mode = True


class AgendaVoteCommitteeVoteSchema(BaseModel):
    id: int
    vote_action: str
    vote_info_id: Optional[int]
    refer_committee_name: Optional[str]
    refer_committee_chamber: Optional[str]
    with_amendment: bool

    class Config:
        orm_mode = True


class AgendaVoteCommitteeSchema(BaseModel):
    id: int
    committee_name: str
    committee_chamber: str
    chair: Optional[str]
    meeting_date_time: Optional[datetime]
    attendance: List[AgendaVoteCommitteeAttendSchema] = []
    votes: List[AgendaVoteCommitteeVoteSchema] = []

    class Config:
        orm_mode = True


class AgendaVoteAddendumSchema(BaseModel):
    addendum_id: str
    modified_date_time: Optional[datetime]
    published_date_time: Optional[datetime]
    created_date_time: datetime
    committees: List[AgendaVoteCommitteeSchema] = []

    class Config:
        orm_mode = True


class AgendaSchema(BaseModel):
    agenda_no: int
    year: int
    published_date_time: Optional[datetime]
    modified_date_time: Optional[datetime]
    created_date_time: datetime
    info_addenda: List[AgendaInfoAddendumSchema] = []
    vote_addenda: List[AgendaVoteAddendumSchema] = []

    class Config:
        orm_mode = True
