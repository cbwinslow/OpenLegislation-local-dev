from pydantic import BaseModel
from typing import Dict, Optional
from datetime import date

from .calendar_id import CalendarId
from .version import Version

class Calendar(BaseModel):
    id: CalendarId
    supplemental_map: Dict[Version, str] = {}  # Dict[Version, CalendarSupplemental]
    active_list_map: Dict[int, str] = {}  # Dict[int, CalendarActiveList]

    def get_active_list(self, id: int) -> Optional[str]:
        return self.active_list_map.get(id)

    def put_active_list(self, active_list: str, sequence_no: int):
        self.active_list_map[sequence_no] = active_list

    def remove_active_list(self, id: int):
        self.active_list_map.pop(id, None)

    def get_supplemental(self, version: Version) -> Optional[str]:
        return self.supplemental_map.get(version)

    def put_supplemental(self, supplemental: str, version: Version):
        self.supplemental_map[version] = supplemental

    def remove_supplemental(self, version: Version):
        self.supplemental_map.pop(version, None)

    def get_cal_date(self) -> Optional[date]:
        # Simplified - in real implementation, extract from supplementals/active lists
        if self.supplemental_map:
            return date.today()  # placeholder
        if self.active_list_map:
            return date.today()  # placeholder
        return None

    def __str__(self):
        return f"Senate Calendar {self.id}"