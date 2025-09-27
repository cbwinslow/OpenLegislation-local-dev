from pydantic import BaseModel

class CalendarId(BaseModel):
    cal_no: int
    year: int

    def __str__(self):
        return f"#{self.cal_no} ({self.year})"

    def __eq__(self, other):
        return isinstance(other, CalendarId) and self.cal_no == other.cal_no and self.year == other.year

    def __hash__(self):
        return hash((self.cal_no, self.year))

    def __lt__(self, other: 'CalendarId'):
        if self.year != other.year:
            return self.year < other.year
        return self.cal_no < other.cal_no