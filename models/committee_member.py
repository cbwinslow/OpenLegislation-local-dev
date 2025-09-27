from pydantic import BaseModel
from typing import Optional
from functools import cmp_to_key

from .session_member import SessionMember
from .committee_member_title import CommitteeMemberTitle

class CommitteeMember(BaseModel):
    sequence_no: int = 0
    session_member: Optional[SessionMember] = None
    title: Optional[CommitteeMemberTitle] = None
    majority: bool = False

    def __init__(self, sequence_no: int = 0, session_member: SessionMember = None,
                 title: CommitteeMemberTitle = None, majority: bool = False, **data):
        super().__init__(sequence_no=sequence_no, session_member=session_member,
                        title=title, majority=majority, **data)

    def __eq__(self, other):
        if not isinstance(other, CommitteeMember):
            return False
        return (self.sequence_no == other.sequence_no and
                self.session_member == other.session_member and
                self.title == other.title and
                self.majority == other.majority)

    def __hash__(self):
        return hash((self.sequence_no, self.session_member, self.title, self.majority))

    def __lt__(self, other: 'CommitteeMember'):
        if self.sequence_no != other.sequence_no:
            return self.sequence_no < other.sequence_no
        if self.session_member != other.session_member:
            return self.session_member < other.session_member
        if self.title != other.title:
            return self.title < other.title
        return self.majority < other.majority  # majority first

    @staticmethod
    def get_comparator():
        return cmp_to_key(lambda x, y: -1 if x < y else 1 if x > y else 0)

    # Basic Getters/Setters
    def get_sequence_no(self) -> int:
        return self.sequence_no

    def set_sequence_no(self, sequence_no: int):
        self.sequence_no = sequence_no

    def get_session_member(self) -> Optional[SessionMember]:
        return self.session_member

    def set_session_member(self, session_member: SessionMember):
        self.session_member = session_member

    def get_title(self) -> Optional[CommitteeMemberTitle]:
        return self.title

    def set_title(self, title: CommitteeMemberTitle):
        self.title = title

    def is_majority(self) -> bool:
        return self.majority

    def set_majority(self, majority: bool):
        self.majority = majority