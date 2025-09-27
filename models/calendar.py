from __future__ import annotations
from pydantic import BaseModel, Field
from typing import Dict, Optional, List
from datetime import date, datetime
from enum import EnumMap
from collections import OrderedDict

from .calendar_id import CalendarId
from .version import Version
from .session_year import SessionYear

# Placeholder classes - need to implement fully later
class CalendarSupplemental(BaseModel):
    version: Version
    cal_date: Optional[date] = None

    def get_version(self) -> Version:
        return self.version

    def get_cal_date(self) -> Optional[date]:
        return self.cal_date

    def get_calendar_supplemental_id(self) -> "CalendarSupplementalId":
        return CalendarSupplementalId()  # Placeholder

class CalendarSupplementalId(BaseModel):
    def to_calendar_entry_list_id(self) -> "CalendarEntryListId":
        return CalendarEntryListId()  # Placeholder

class CalendarActiveList(BaseModel):
    sequence_no: int
    cal_date: Optional[date] = None

    def get_sequence_no(self) -> int:
        return self.sequence_no

    def get_cal_date(self) -> Optional[date]:
        return self.cal_date

    def get_calendar_active_list_id(self) -> "CalendarActiveListId":
        return CalendarActiveListId()  # Placeholder

class CalendarActiveListId(BaseModel):
    def to_calendar_entry_list_id(self) -> "CalendarEntryListId":
        return CalendarEntryListId()  # Placeholder

class CalendarEntryListId(BaseModel):
    pass

class Calendar(BaseModel):
    id: Optional[CalendarId] = None
    supplemental_map: EnumMap[Version, CalendarSupplemental] = Field(default_factory=lambda: EnumMap(Version))
    active_list_map: OrderedDict[int, CalendarActiveList] = Field(default_factory=OrderedDict)
    session_year: int = Field(..., description="Year of the session")
    published_date_time: Optional[datetime] = None

    def __init__(self, calendar_id: Optional[CalendarId] = None, **data):
        super().__init__(**data)
        if calendar_id:
            self.id = calendar_id
            self.session_year = calendar_id.year
        elif self.id:
            self.session_year = self.id.year

    def get_active_list(self, id_: int) -> Optional[CalendarActiveList]:
        return self.active_list_map.get(id_)

    def put_active_list(self, active_list: CalendarActiveList) -> None:
        self.active_list_map[active_list.sequence_no] = active_list

    def remove_active_list(self, id_: int) -> None:
        self.active_list_map.pop(id_, None)

    def get_supplemental(self, version: Version) -> Optional[CalendarSupplemental]:
        return self.supplemental_map.get(version)

    def put_supplemental(self, supplemental: CalendarSupplemental) -> None:
        self.supplemental_map[supplemental.version] = supplemental

    def remove_supplemental(self, version: Version) -> None:
        self.supplemental_map.pop(version, None)

    def get_cal_date(self) -> Optional[date]:
        if self.supplemental_map:
            return next(iter(self.supplemental_map.values())).cal_date
        elif self.active_list_map:
            return next(iter(self.active_list_map.values())).cal_date
        return None

    def __str__(self) -> str:
        return f"Senate Calendar {self.id}"

    def __eq__(self, other) -> bool:
        if self is other:
            return True
        if not isinstance(other, Calendar):
            return False
        return (
            self.id == other.id and
            self.supplemental_map == other.supplemental_map and
            self.active_list_map == other.active_list_map and
            self.published_date_time == other.published_date_time
        )

    def __hash__(self) -> int:
        return hash((self.id, tuple(self.supplemental_map.items()), tuple(self.active_list_map.items()), self.published_date_time))

    # Getters and setters
    def get_id(self) -> Optional[CalendarId]:
        return self.id

    def get_calendar_entry_list_ids(self) -> List[CalendarEntryListId]:
        calendar_entry_list_ids = []
        for supplemental in self.supplemental_map.values():
            calendar_entry_list_ids.append(supplemental.get_calendar_supplemental_id().to_calendar_entry_list_id())
        for active_list in self.active_list_map.values():
            calendar_entry_list_ids.append(active_list.get_calendar_active_list_id().to_calendar_entry_list_id())
        return calendar_entry_list_ids

    def set_id(self, calendar_number: int, year: int) -> None:
        self.id = CalendarId(calendar_number=calendar_number, year=year)

    def set_id_from_calendar_id(self, id_: CalendarId) -> None:
        self.id = id_

    def get_supplemental_map(self) -> EnumMap[Version, CalendarSupplemental]:
        return self.supplemental_map

    def set_supplemental_map(self, supplemental_map: EnumMap[Version, CalendarSupplemental]) -> None:
        self.supplemental_map = supplemental_map

    def get_active_list_map(self) -> OrderedDict[int, CalendarActiveList]:
        return self.active_list_map

    def set_active_list_map(self, active_list_map: OrderedDict[int, CalendarActiveList]) -> None:
        self.active_list_map = active_list_map