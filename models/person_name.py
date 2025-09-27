from pydantic import BaseModel
from typing import Optional

from .chamber import Chamber

class PersonName(BaseModel):
    full_name: Optional[str] = None
    prefix: Optional[str] = None
    first_name: Optional[str] = None
    middle_name: Optional[str] = None
    last_name: Optional[str] = None
    suffix: Optional[str] = None

    def __init__(self, full_name: str = None, most_recent_chamber: Chamber = None,
                 first_name: str = None, middle_name: str = None,
                 last_name: str = None, suffix: str = None, prefix: str = None, **data):
        if most_recent_chamber and not prefix:
            prefix = "Senator" if most_recent_chamber == Chamber.SENATE else "Assembly Member"
        super().__init__(full_name=full_name, prefix=prefix, first_name=first_name,
                        middle_name=middle_name, last_name=last_name, suffix=suffix, **data)

    def __lt__(self, other: 'PersonName'):
        if self.last_name != other.last_name:
            return self.last_name < other.last_name
        if self.first_name != other.first_name:
            return self.first_name < other.first_name
        return (self.middle_name or "") < (other.middle_name or "")