from functools import total_ordering
from pydantic import BaseModel
from models.person import Person
from models.enums import Chamber
from models.session import SessionYear

class Member(BaseModel):
    """
    Represents a person holding a specific office
    """
    person: Person
    member_id: int
    chamber: Chamber
    incumbent: bool

    class Config:
        frozen = True
        arbitrary_types_allowed = True

@total_ordering
class SessionMember(BaseModel):
    session_member_id: int
    member: Member
    lbdc_short_name: str
    session_year: SessionYear
    district_code: int
    alternate: bool

    def __eq__(self, other):
        if not isinstance(other, SessionMember):
            return NotImplemented

        # Special equality condition from Java code
        short_name_matches = self.lbdc_short_name == other.lbdc_short_name
        is_alternate_involved = self.alternate or other.alternate

        return (self.member == other.member and
                self.session_year == other.session_year and
                self.district_code == other.district_code and
                (short_name_matches or is_alternate_involved))

    def __hash__(self):
        # Hash code logic from Java code, ignores lbdcShortName and alternate
        return hash((self.member, self.session_year, self.district_code))

    def __lt__(self, other):
        if not isinstance(other, SessionMember):
            return NotImplemented

        # Comparison logic from Java code
        if self.member.member_id != other.member.member_id:
            return self.member.member_id < other.member.member_id
        if self.session_year != other.session_year:
            return self.session_year < other.session_year
        # 'True' first for alternate
        if self.alternate != other.alternate:
            return self.alternate
        return self.lbdc_short_name < other.lbdc_short_name

    def __str__(self):
        return f"{self.lbdc_short_name} (year: {self.session_year}, id: {self.member.member_id})"

    class Config:
        arbitrary_types_allowed = True