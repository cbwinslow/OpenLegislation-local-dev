from pydantic import BaseModel

from .person import Person
from .chamber import Chamber

class Member(BaseModel):
    person: Person
    member_id: int
    chamber: Chamber
    incumbent: bool

    def __init__(self, person: Person = None, member_id: int = 0, chamber: Chamber = None, incumbent: bool = False, **data):
        super().__init__(person=person, member_id=member_id, chamber=chamber, incumbent=incumbent, **data)

    def __eq__(self, other):
        if self is other:
            return True
        if not isinstance(other, Member):
            return False
        return (self.person == other.person and
                self.member_id == other.member_id and
                self.chamber == other.chamber and
                self.incumbent == other.incumbent)

    def __hash__(self):
        return hash((self.person, self.member_id, self.chamber, self.incumbent))

    # Getters / Setters
    def get_person(self) -> Person:
        return self.person

    def get_member_id(self) -> int:
        return self.member_id

    def get_chamber(self) -> Chamber:
        return self.chamber

    def is_incumbent(self) -> bool:
        return self.incumbent