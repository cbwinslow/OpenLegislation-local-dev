import datetime
from pydantic import BaseModel, Field, field_validator
from typing import Optional
from models.session import SessionYear

class BaseLegislativeContent(BaseModel):
    """
    Basic info that is common to all pieces of legislative content.
    """
    year: int
    session: Optional[SessionYear] = None
    modified_date_time: Optional[datetime.datetime] = None
    published_date_time: Optional[datetime.datetime] = None

    def __init__(self, **data):
        super().__init__(**data)
        if 'session' not in data:
            self.session = SessionYear(year=self.year)

    @property
    def is_published(self) -> bool:
        return self.published_date_time is not None

    def __eq__(self, other):
        if not isinstance(other, BaseLegislativeContent):
            return NotImplemented
        return (self.modified_date_time == other.modified_date_time and
                self.published_date_time == other.published_date_time and
                self.session == other.session and
                self.year == other.year)

    def __hash__(self):
        return hash((self.modified_date_time, self.published_date_time, self.session, self.year))

    class Config:
        from_attributes = True
        # Allow extra fields to be added by subclasses
        extra = 'allow'