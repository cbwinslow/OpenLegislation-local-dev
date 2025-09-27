from pydantic import BaseModel
from typing import Optional

from .committee_id import CommitteeId
from .session_year import SessionYear

class CommitteeSessionId(CommitteeId):
    session: Optional[SessionYear] = None

    def __init__(self, chamber=None, name: str = None, session: SessionYear = None, **data):
        super().__init__(chamber=chamber, name=name, **data)
        self.session = session

    def __str__(self):
        return f"{super().__str__()}-{self.session}"

    def __eq__(self, other):
        if self is other:
            return True
        if not isinstance(other, CommitteeSessionId):
            return False
        if not super().__eq__(other):
            return False
        return self.session == other.session

    def __hash__(self):
        return 31 * super().__hash__() + (self.session.hashCode() if self.session else 0)

    def __lt__(self, other: CommitteeId):
        super_result = super().__lt__(other)
        if super_result == 0 and isinstance(other, CommitteeSessionId):
            return self.session < other.session if self.session and other.session else False
        return super_result

    # Getters / Setters
    def get_session(self) -> Optional[SessionYear]:
        return self.session