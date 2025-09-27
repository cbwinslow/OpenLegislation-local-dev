from pydantic import BaseModel, Field
from typing import List
from models.base import BaseLegislativeContent
from models.member import SessionMember

class SenateVoteAttendance(BaseLegislativeContent):
    remote_members: List[SessionMember] = Field(default_factory=list)

    def __eq__(self, other):
        if not isinstance(other, SenateVoteAttendance):
            return NotImplemented
        return super().__eq__(other) and self.remote_members == other.remote_members

    def __hash__(self):
        return hash((super().__hash__(), tuple(self.remote_members)))

    class Config:
        arbitrary_types_allowed = True