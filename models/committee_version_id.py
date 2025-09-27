from pydantic import BaseModel
from typing import Optional
from datetime import datetime

from .committee_session_id import CommitteeSessionId
from .committee_id import CommitteeId
from .session_year import SessionYear

class CommitteeVersionId(CommitteeSessionId):
    reference_date: Optional[datetime] = None

    def __init__(self, chamber=None, name: str = None, session: SessionYear = None,
                 reference_date: datetime = None, **data):
        if reference_date is None:
            raise ValueError("referenceDate cannot be null!")
        super().__init__(chamber=chamber, name=name, session=session, **data)
        self.reference_date = reference_date

    def __str__(self):
        return f"{super().__str__()}-{self.reference_date}"

    def __eq__(self, other):
        if self is other:
            return True
        if not isinstance(other, CommitteeVersionId):
            return False
        if not super().__eq__(other):
            return False
        return self.reference_date == other.reference_date

    def __hash__(self):
        return 31 * super().__hash__() + (hash(self.reference_date) if self.reference_date else 0)

    def __lt__(self, other: CommitteeId):
        super_result = super().__lt__(other)
        if super_result == 0 and isinstance(other, CommitteeVersionId):
            return self.reference_date < other.reference_date if self.reference_date and other.reference_date else False
        return super_result

    # Basic Getters/Setters
    def get_reference_date(self) -> Optional[datetime]:
        return self.reference_date