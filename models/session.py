import datetime
from pydantic import BaseModel, field_validator

class SessionYear(BaseModel):
    """
    Simple representation of a session year. The senate has two year session periods, the start of
    which is always on an odd numbered year. This class will perform the minimal validation necessary
    to convert a year into its proper session year.
    """
    year: int

    @field_validator('year')
    def validate_year(cls, v):
        computed_session = v if v % 2 != 0 else v - 1
        if computed_session <= 0:
            raise ValueError(f"Session year must be positive! ({computed_session} computed from {v})")
        return computed_session

    def previous_session_year(self):
        return SessionYear(year=self.year - 2)

    def next_session_year(self):
        return SessionYear(year=self.year + 2)

    @staticmethod
    def of(year: int):
        return SessionYear(year=year)

    @staticmethod
    def current():
        return SessionYear(year=datetime.date.today().year)

    @property
    def start_date_time(self):
        return datetime.datetime(self.year, 1, 1)

    def __str__(self):
        return str(self.year)

    def __lt__(self, other):
        if not isinstance(other, SessionYear):
            return NotImplemented
        return self.year < other.year

    def __hash__(self):
        return hash(self.year)

    class Config:
        from_attributes = True
        frozen = True