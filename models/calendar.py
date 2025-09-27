from functools import total_ordering
from pydantic import BaseModel

@total_ordering
class CalendarId(BaseModel):
    """
    CalendarId is a simple wrapper used to uniquely identify a Calendar instance.
    """
    cal_no: int
    year: int

    def __str__(self):
        return f"#{self.cal_no} ({self.year})"

    def __eq__(self, other):
        if not isinstance(other, CalendarId):
            return NotImplemented
        return self.year == other.year and self.cal_no == other.cal_no

    def __hash__(self):
        return hash((self.year, self.cal_no))

    def __lt__(self, other):
        if not isinstance(other, CalendarId):
            return NotImplemented
        if self.year != other.year:
            return self.year < other.year
        return self.cal_no < other.cal_no

    class Config:
        frozen = True
        arbitrary_types_allowed = True