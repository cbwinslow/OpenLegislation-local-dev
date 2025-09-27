from __future__ import annotations

from datetime import datetime, time
from typing import List, Optional

from pydantic import BaseModel

from .bill import SessionMemberSchema


class CommitteeVersionSchema(BaseModel):
    id: int
    session_year: int
    created: datetime
    reformed: datetime
    location: Optional[str]
    meetday: Optional[str]
    meettime: Optional[time]
    meetaltweek: bool
    meetaltweektext: Optional[str]

    class Config:
        orm_mode = True


class CommitteeMemberSchema(BaseModel):
    id: int
    session_year: int
    sequence_no: int
    title: str
    majority: bool
    session_member: SessionMemberSchema

    class Config:
        orm_mode = True


class CommitteeSchema(BaseModel):
    name: str
    chamber: str
    id: int
    full_name: Optional[str]
    current_session: int
    current_version: datetime
    versions: List[CommitteeVersionSchema] = []
    members: List[CommitteeMemberSchema] = []

    class Config:
        orm_mode = True
