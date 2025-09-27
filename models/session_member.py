from pydantic import BaseModel
from typing import Optional

from .member import Member
from .session_year import SessionYear

class SessionMember(BaseModel):
    session_member_id: int = 0
    member: Optional[Member] = None
    lbdc_short_name: Optional[str] = None
    session_year: Optional[SessionYear] = None
    district_code: Optional[int] = None
    alternate: bool = False

    def __init__(self, session_member_id: int = 0, member: Member = None,
                 lbdc_short_name: str = None, session_year: SessionYear = None,
                 district_code: int = None, alternate: bool = False, **data):
        super().__init__(session_member_id=session_member_id, member=member,
                        lbdc_short_name=lbdc_short_name, session_year=session_year,
                        district_code=district_code, alternate=alternate, **data)

    def update_from_other(self, other: 'SessionMember'):
        self.member = Member(other.member)
        self.session_member_id = other.get_session_member_id()
        self.lbdc_short_name = other.get_lbdc_short_name()
        self.alternate = other.is_alternate()
        self.session_year = other.get_session_year()
        self.district_code = other.get_district_code()

    def __eq__(self, other):
        if self is other:
            return True
        if not isinstance(other, SessionMember):
            return False
        return (self.member == other.member and
                self.session_year == other.session_year and
                self.district_code == other.district_code and
                (self.lbdc_short_name == other.lbdc_short_name or
                 self.alternate or other.alternate))

    def __hash__(self):
        return hash((self.member, self.session_year, self.district_code))

    def __str__(self):
        return f"{self.lbdc_short_name} (year: {self.session_year}, id: {self.member.get_member_id() if self.member else None})"

    def __lt__(self, other: 'SessionMember'):
        if self.member.get_member_id() != other.member.get_member_id():
            return self.member.get_member_id() < other.member.get_member_id()
        if self.session_year != other.session_year:
            return self.session_year < other.session_year
        if self.alternate != other.alternate:
            return other.alternate  # alternate first (True > False)
        return (self.lbdc_short_name or "") < (other.lbdc_short_name or "")

    # Basic Getters/Setters
    def get_session_member_id(self) -> int:
        return self.session_member_id

    def set_session_member_id(self, session_member_id: int):
        self.session_member_id = session_member_id

    def get_member(self) -> Optional[Member]:
        return self.member

    def set_member(self, member: Member):
        self.member = member

    def get_lbdc_short_name(self) -> Optional[str]:
        return self.lbdc_short_name

    def set_lbdc_short_name(self, lbdc_short_name: str):
        self.lbdc_short_name = lbdc_short_name

    def get_session_year(self) -> Optional[SessionYear]:
        return self.session_year

    def set_session_year(self, session_year: SessionYear):
        self.session_year = session_year

    def get_district_code(self) -> Optional[int]:
        return self.district_code

    def set_district_code(self, district_code: int):
        self.district_code = district_code

    def is_alternate(self) -> bool:
        return self.alternate

    def set_alternate(self, alternate: bool):
        self.alternate = alternate