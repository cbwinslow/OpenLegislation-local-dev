import datetime
from functools import total_ordering
from pydantic import BaseModel
from models.enums import Chamber
from models.session import SessionYear

@total_ordering
class CommitteeId(BaseModel):
    """
    Represents a committee's unique identifier.
    """
    chamber: Chamber
    name: str

    def __str__(self):
        return f"{self.chamber.name}-{self.name}"

    def __eq__(self, other):
        if not isinstance(other, CommitteeId):
            return NotImplemented
        # Equality does not consider inheritance, only field values
        return (hasattr(other, 'chamber') and self.chamber == other.chamber and
                hasattr(other, 'name') and self.name.lower() == other.name.lower())

    def __hash__(self):
        return hash((self.chamber, self.name.lower()))

    def __lt__(self, other):
        if not isinstance(other, CommitteeId):
            return NotImplemented
        if self.chamber.name != other.chamber.name:
            return self.chamber.name < other.chamber.name
        return self.name.lower() < other.name.lower()

    class Config:
        frozen = True
        arbitrary_types_allowed = True

@total_ordering
class CommitteeSessionId(CommitteeId):
    """
    Identifies a committee for a single session of congress
    """
    session: SessionYear

    def __str__(self):
        return f"{super().__str__()}-{self.session}"

    def __eq__(self, other):
        if not isinstance(other, CommitteeSessionId):
            return False
        return super().__eq__(other) and self.session == other.session

    def __hash__(self):
        return hash((super().__hash__(), self.session))

    def __lt__(self, other):
        if not isinstance(other, CommitteeId):
            return NotImplemented

        # Compare parent fields first
        if super().__lt__(other): return True
        if self.name.lower() > other.name.lower() or self.chamber.name > other.chamber.name: return False

        # Parent fields are equal, compare child fields
        if isinstance(other, CommitteeSessionId):
            return self.session < other.session

        # self is more specific than other (a base CommitteeId), so not less than
        return False

    class Config:
        arbitrary_types_allowed = True

@total_ordering
class CommitteeVersionId(CommitteeSessionId):
    """
    Identifies a committee for a single session, referenced at a specific date and time.
    """
    reference_date: datetime.datetime

    def __str__(self):
        return f"{super().__str__()}-{self.reference_date}"

    def __eq__(self, other):
        if not isinstance(other, CommitteeVersionId):
            return False
        return super().__eq__(other) and self.reference_date == other.reference_date

    def __hash__(self):
        return hash((super().__hash__(), self.reference_date))

    def __lt__(self, other):
        if not isinstance(other, CommitteeId):
            return NotImplemented

        # Compare CommitteeId fields
        if CommitteeId.__lt__(self, other): return True
        if self.name.lower() > other.name.lower() or self.chamber.name > other.chamber.name: return False

        # Compare CommitteeSessionId fields
        if not isinstance(other, CommitteeSessionId): return False # self is more specific
        if self.session < other.session: return True
        if self.session > other.session: return False

        # Compare CommitteeVersionId fields
        if isinstance(other, CommitteeVersionId):
            return self.reference_date < other.reference_date

        # self is more specific
        return False