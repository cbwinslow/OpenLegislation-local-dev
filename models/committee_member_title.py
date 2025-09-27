from enum import Enum

class CommitteeMemberTitle(Enum):
    CHAIR_PERSON = "CHAIR_PERSON"
    VICE_CHAIR = "VICE_CHAIR"
    MEMBER = "MEMBER"

    def as_sql_enum(self) -> str:
        return self.name.lower()

    @staticmethod
    def value_of_sql_enum(sql_enum: str) -> 'CommitteeMemberTitle':
        return CommitteeMemberTitle(sql_enum.upper())