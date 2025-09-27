from pydantic import BaseModel
from typing import Optional
from datetime import datetime

from .session_year import SessionYear

class BaseLegislativeContent(BaseModel):
    session: Optional[SessionYear] = None
    year: int = 0
    modified_date_time: Optional[datetime] = None
    published_date_time: Optional[datetime] = None

    def __init__(self, **data):
        super().__init__(**data)
        if self.year and not self.session:
            self.session = SessionYear.of(self.year)

    def __eq__(self, other):
        if not isinstance(other, BaseLegislativeContent):
            return False
        return (self.modified_date_time == other.modified_date_time and
                self.published_date_time == other.published_date_time and
                self.session == other.session and
                self.year == other.year)

    def __hash__(self):
        return hash((self.modified_date_time, self.published_date_time, self.session, self.year))

    # Functional Getters/Setters
    def is_published(self) -> bool:
        return self.published_date_time is not None

    def set_year(self, year: int):
        self.year = year
        if not self.session:
            self.session = SessionYear.of(year)

    # Basic Getters/Setters
    def get_published_date_time(self) -> Optional[datetime]:
        return self.published_date_time

    def set_published_date_time(self, published_date_time: datetime):
        self.published_date_time = published_date_time

    def get_modified_date_time(self) -> Optional[datetime]:
        return self.modified_date_time

    def set_modified_date_time(self, modified_date_time: datetime):
        self.modified_date_time = modified_date_time

    def get_session(self) -> Optional[SessionYear]:
        return self.session

    def set_session(self, session: SessionYear):
        self.session = session

    def get_year(self) -> int:
        return self.year