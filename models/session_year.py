from pydantic import BaseModel, validator
from datetime import datetime, date
from typing import Optional

class SessionYear(BaseModel):
    year: int

    @validator('year', pre=True)
    def validate_year(cls, v):
        if isinstance(v, int):
            computed_session = v - 1 if v % 2 == 0 else v
            if computed_session <= 0:
                raise ValueError(f"Session year must be positive! ({computed_session} computed from {v})")
            return computed_session
        return v

    def previous_session_year(self) -> 'SessionYear':
        return SessionYear(year=self.year - 2)

    def next_session_year(self) -> 'SessionYear':
        return SessionYear(year=self.year + 2)

    @classmethod
    def of(cls, year: int) -> 'SessionYear':
        return cls(year=year)

    @classmethod
    def current(cls) -> 'SessionYear':
        return cls(year=date.today().year)

    def get_start_date_time(self) -> datetime:
        return datetime.combine(date(self.year, 1, 1), datetime.min.time())

    def __str__(self):
        return str(self.year)

    def __lt__(self, other: 'SessionYear'):
        return self.year < other.year

    def __eq__(self, other):
        return isinstance(other, SessionYear) and self.year == other.year

    def __hash__(self):
        return hash(self.year)