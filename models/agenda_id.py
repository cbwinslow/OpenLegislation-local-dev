from pydantic import BaseModel
from typing import Optional
import uuid

class AgendaId(BaseModel):
    number: int
    year: int

    def __init__(self, number: Optional[int] = None, year: int = 0, **data):
        if number is None:
            # Added for Json Deserialization - generate a unique number
            number = hash(uuid.uuid4()) % 1000000
        super().__init__(number=number, year=year, **data)

    def __str__(self):
        return f"{self.year}-{self.number}"

    def __eq__(self, other):
        if self is other:
            return True
        if not isinstance(other, AgendaId):
            return False
        return self.number == other.number and self.year == other.year

    def __hash__(self):
        return hash((self.number, self.year))

    def __lt__(self, other: 'AgendaId'):
        if self.year != other.year:
            return self.year < other.year
        return self.number < other.number

    # Basic Getters/Setters
    def get_number(self) -> int:
        return self.number

    def get_year(self) -> int:
        return self.year