from enum import Enum

class Chamber(str, Enum):
    SENATE = "SENATE"
    ASSEMBLY = "ASSEMBLY"

    def get_abbreviation(self) -> str:
        return "S" if self == Chamber.SENATE else "A"

    def opposite(self) -> 'Chamber':
        return Chamber.ASSEMBLY if self == Chamber.SENATE else Chamber.SENATE

    @classmethod
    def get_value(cls, value: str) -> 'Chamber':
        return cls(value.strip().upper())