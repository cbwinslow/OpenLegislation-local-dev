from pydantic import BaseModel

from .person import Person
from .chamber import Chamber

class Member(BaseModel):
    person: Person
    member_id: int
    chamber: Chamber
    incumbent: bool

    def __init__(self, person: Person, member_id: int, chamber: Chamber, incumbent: bool, **data):
        super().__init__(person=person, member_id=member_id, chamber=chamber, incumbent=incumbent, **data)

    def is_incumbent(self) -> bool:
        return self.incumbent

    def __eq__(self, other):
        return isinstance(other, Member) and self.person == other.person and self.member_id == other.member_id and self.chamber == other.chamber and self.incumbent == other.incumbent

    def __hash__(self):
        return hash((self.person, self.member_id, self.chamber, self.incumbent))