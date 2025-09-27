from pydantic import BaseModel

class AgendaId(BaseModel):
    number: int
    year: int

    def __str__(self):
        return f"{self.year}-{self.number}"

    def __eq__(self, other):
        return isinstance(other, AgendaId) and self.number == other.number and self.year == other.year

    def __hash__(self):
        return hash((self.number, self.year))

    def __lt__(self, other: 'AgendaId'):
        if self.year != other.year:
            return self.year < other.year
        return self.number < other.number