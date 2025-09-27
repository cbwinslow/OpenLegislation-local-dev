from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional


@dataclass
class GovInfoSponsor:
    name: str
    party: Optional[str] = None
    state: Optional[str] = None
    role: str = "sponsor"


@dataclass
class GovInfoAction:
    description: str
    action_code: Optional[str] = None
    chamber: Optional[str] = None
    action_date: Optional[datetime] = None


@dataclass
class GovInfoBillRecord:
    bill_print_no: str
    session_year: int
    bill_type: str
    title: Optional[str]
    short_title: Optional[str] = None
    summary: Optional[str] = None
    data_source: str = "govinfo"
    congress: Optional[int] = None
    sponsor: Optional[GovInfoSponsor] = None
    cosponsors: List[GovInfoSponsor] = field(default_factory=list)
    actions: List[GovInfoAction] = field(default_factory=list)
    introduced_date: Optional[datetime] = None
    active_version: str = ""


# Agenda structures


@dataclass
class GovInfoAgendaCommitteeItem:
    bill_print_no: str
    session_year: int
    amendment: str = ""
    message: Optional[str] = None


@dataclass
class GovInfoAgendaCommittee:
    committee_name: str
    committee_chamber: str
    meeting_date_time: Optional[datetime] = None
    chair: Optional[str] = None
    location: Optional[str] = None
    notes: Optional[str] = None
    items: List[GovInfoAgendaCommitteeItem] = field(default_factory=list)


@dataclass
class GovInfoAgendaAddendum:
    addendum_id: str
    week_of: Optional[datetime] = None
    modified_date_time: Optional[datetime] = None
    published_date_time: Optional[datetime] = None
    committees: List[GovInfoAgendaCommittee] = field(default_factory=list)


@dataclass
class GovInfoAgendaRecord:
    agenda_no: int
    year: int
    published_date_time: Optional[datetime] = None
    modified_date_time: Optional[datetime] = None
    info_addenda: List[GovInfoAgendaAddendum] = field(default_factory=list)


# Calendar structures


@dataclass
class GovInfoCalendarEntry:
    bill_calendar_no: int
    bill_print_no: Optional[str] = None
    bill_session_year: Optional[int] = None
    bill_amend_version: str = ""
    high: Optional[bool] = None


@dataclass
class GovInfoCalendarActiveList:
    sequence_no: Optional[int]
    calendar_date: Optional[datetime]
    release_date_time: Optional[datetime]
    notes: Optional[str]
    entries: List[GovInfoCalendarEntry] = field(default_factory=list)


@dataclass
class GovInfoCalendarSupplemental:
    sup_version: str
    release_date_time: Optional[datetime]
    notes: Optional[str]
    entries: List[GovInfoCalendarEntry] = field(default_factory=list)


@dataclass
class GovInfoCalendarRecord:
    calendar_no: int
    calendar_year: int
    published_date_time: Optional[datetime] = None
    modified_date_time: Optional[datetime] = None
    active_lists: List[GovInfoCalendarActiveList] = field(default_factory=list)
    supplements: List[GovInfoCalendarSupplemental] = field(default_factory=list)
