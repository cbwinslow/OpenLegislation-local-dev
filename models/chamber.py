from enum import Enum


class Chamber(Enum):
    SENATE = 'S'
    ASSEMBLY = 'A'

    def get_abbreviation(self) -> str:
        return self.value

    def as_sql_enum(self) -> str:
        return self.name.lower()

    def opposite(self) -> "Chamber":
        return Chamber.ASSEMBLY if self is Chamber.SENATE else Chamber.SENATE

    @staticmethod
    def get_value(value: str):
        if value is None:
            raise ValueError("Supplied value cannot be null when mapping to Chamber.")
        return Chamber(value.strip().upper())
