from __future__ import annotations
from typing import List, Dict, Set, Optional, Any
from datetime import datetime
from pydantic import BaseModel, Field
from enum import Enum
from collections import OrderedDict

from .base_bill_id import BaseBillId
from .version import Version
from .bill_id import BillId
from .session_year import SessionYear
from .chamber import Chamber

# Placeholder classes - need to implement fully later
class BillStatus(BaseModel):
    pass

class BillAmendment(BaseModel):
    bill_id: BillId
    version: Version

    def shallow_clone(self) -> "BillAmendment":
        return BillAmendment(bill_id=self.bill_id, version=self.version)

class PublishStatus(BaseModel):
    effect_date_time: Optional[datetime] = None

    def is_published(self) -> bool:
        return True  # Placeholder

class VetoId(BaseModel):
    pass

class VetoMessage(BaseModel):
    pass

class ApprovalMessage(BaseModel):
    pass

class BillSponsor(BaseModel):
    pass

class SessionMember(BaseModel):
    pass

class CommitteeVersionId(BaseModel):
    pass

class BillAction(BaseModel):
    pass

class ProgramInfo(BaseModel):
    pass

class CommitteeAgendaId(BaseModel):
    pass

class CalendarId(BaseModel):
    pass

class Bill(BaseModel):
    base_bill_id: BaseBillId
    title: str = ""
    summary: str = ""
    status: Optional[BillStatus] = None
    ldblurb: str = ""
    milestones: List[BillStatus] = Field(default_factory=list)
    amendment_map: Dict[Version, BillAmendment] = Field(default_factory=dict)
    amend_publish_status_map: Dict[Version, PublishStatus] = Field(default_factory=dict)
    veto_messages: Dict[VetoId, VetoMessage] = Field(default_factory=dict)
    approval_message: Optional[ApprovalMessage] = None
    active_version: Version = Version.ORIGINAL
    sponsor: Optional[BillSponsor] = None
    additional_sponsors: List[SessionMember] = Field(default_factory=list)
    past_committees: Set[CommitteeVersionId] = Field(default_factory=set)
    actions: List[BillAction] = Field(default_factory=list)
    substituted_by: Optional[BaseBillId] = None
    reprint_of: Optional[BillId] = None
    direct_previous_version: Optional[BillId] = None
    all_previous_versions: Set[BillId] = Field(default_factory=set)
    program_info: Optional[ProgramInfo] = None
    committee_agendas: List[CommitteeAgendaId] = Field(default_factory=list)
    calendars: List[CalendarId] = Field(default_factory=list)
    chapter_num: Optional[int] = None
    chapter_year: Optional[int] = None
    federal_congress: Optional[int] = None
    federal_source: Optional[str] = None
    session_year: int = Field(..., description="Year of the session")

    def __init__(self, base_bill_id: Optional[BaseBillId] = None, **data):
        if base_bill_id:
            data['base_bill_id'] = base_bill_id
            data['session_year'] = base_bill_id.session.year if base_bill_id.session else None
        super().__init__(**data)
        if self.base_bill_id:
            self.session_year = self.base_bill_id.session.year

    def compare_to(self, other: "Bill") -> int:
        return self.base_bill_id.compare_to(other.base_bill_id)

    def set_published_date_time(self, publish_date_time: datetime) -> None:
        # Set the publish date time - simplified
        pass

    def to_string(self) -> str:
        return str(self.base_bill_id)

    def shallow_clone(self) -> "Bill":
        # Create a shallow clone
        clone = Bill(base_bill_id=self.base_bill_id)
        clone.amendment_map = {}
        for amendment in self.get_amendment_list():
            clone.add_amendment(amendment.shallow_clone())
        return clone

    def get_bill_info(self) -> "BillInfo":
        return BillInfo(bill=self)

    def get_base_print_no(self) -> str:
        return self.base_bill_id.get_base_print_no()

    def get_bill_type(self) -> "BillType":
        return self.base_bill_id.get_bill_type()

    def get_chamber(self) -> Chamber:
        return self.base_bill_id.get_chamber()

    def get_ldblurb(self) -> str:
        return self.ldblurb

    def is_resolution(self) -> bool:
        return self.get_bill_type().is_resolution()

    def get_amendment(self, version: Version) -> BillAmendment:
        if self.has_amendment(version):
            return self.amendment_map[version]
        raise ValueError(f"Bill amendment not found for version {version}")

    def get_amendment_list(self) -> List[BillAmendment]:
        return list(self.amendment_map.values())

    def get_amendment_ids(self) -> Set[BillId]:
        return {amendment.bill_id for amendment in self.amendment_map.values()}

    def add_amendment(self, bill_amendment: BillAmendment) -> None:
        if bill_amendment:
            self.amendment_map[bill_amendment.version] = bill_amendment
        else:
            raise ValueError("Supplied BillAmendment cannot be null.")

    def add_amendments(self, bill_amendments: List[BillAmendment]) -> None:
        for amendment in bill_amendments:
            self.add_amendment(amendment)

    def get_publish_status(self, version: Version) -> Optional[PublishStatus]:
        return self.amend_publish_status_map.get(version)

    def update_publish_status(self, version: Version, publish_status: PublishStatus) -> None:
        if publish_status:
            self.amend_publish_status_map[version] = publish_status
        else:
            raise ValueError("Supplied PublishStatus cannot be null.")

    def set_publish_statuses(self, publish_status_map: Dict[Version, PublishStatus]) -> None:
        self.amend_publish_status_map.clear()
        if publish_status_map:
            for version, status in publish_status_map.items():
                self.update_publish_status(version, status)
        else:
            raise ValueError("Supplied PublishStatusMap cannot be null.")

    def is_base_version_published(self) -> bool:
        status = self.amend_publish_status_map.get(Version.ORIGINAL)
        return status is not None and status.is_published()

    def has_amendment(self, version: Version) -> bool:
        return version in self.amendment_map and self.amendment_map[version] is not None

    def has_active_amendment(self) -> bool:
        return self.has_amendment(self.active_version)

    def set_active_version(self, active_version: Version) -> None:
        self.active_version = active_version
        if active_version not in self.amendment_map:
            self.amendment_map[active_version] = BillAmendment(
                bill_id=BillId(base_bill_id=self.base_bill_id, version=active_version),
                version=active_version
            )

    def get_active_amendment(self) -> BillAmendment:
        return self.get_amendment(self.active_version)

    def add_action(self, action: BillAction) -> None:
        self.actions.append(action)

    def add_past_committee(self, committee_version_id: CommitteeVersionId) -> None:
        self.past_committees.add(committee_version_id)

    def get_full_text_plain(self) -> str:
        if self.has_active_amendment():
            return self.get_active_amendment().get_full_text("PLAIN")
        return ""

    # Getters and setters
    def get_base_bill_id(self) -> BaseBillId:
        return self.base_bill_id

    def set_base_bill_id(self, base_bill_id: BaseBillId) -> None:
        self.base_bill_id = base_bill_id

    def get_title(self) -> str:
        return self.title

    def set_title(self, title: str) -> None:
        self.title = title

    def get_summary(self) -> str:
        return self.summary

    def set_summary(self, summary: str) -> None:
        self.summary = summary

    def get_active_version(self) -> Version:
        return self.active_version

    def get_amendment_map(self) -> Dict[Version, BillAmendment]:
        return self.amendment_map

    def get_amend_publish_status_map(self) -> Dict[Version, PublishStatus]:
        return self.amend_publish_status_map

    def get_status(self) -> Optional[BillStatus]:
        return self.status

    def set_status(self, status: BillStatus) -> None:
        self.status = status

    def get_milestones(self) -> List[BillStatus]:
        return self.milestones

    def set_milestones(self, milestones: List[BillStatus]) -> None:
        self.milestones = milestones

    def get_veto_messages(self) -> Dict[VetoId, VetoMessage]:
        return self.veto_messages

    def set_veto_messages(self, veto_messages: Dict[VetoId, VetoMessage]) -> None:
        self.veto_messages = veto_messages

    def get_approval_message(self) -> Optional[ApprovalMessage]:
        return self.approval_message

    def set_approval_message(self, approval_message: ApprovalMessage) -> None:
        self.approval_message = approval_message

    def get_direct_previous_version(self) -> Optional[BillId]:
        return self.direct_previous_version

    def set_direct_previous_version(self, direct_previous_version: BillId) -> None:
        self.direct_previous_version = direct_previous_version

    def get_all_previous_versions(self) -> Set[BillId]:
        return self.all_previous_versions

    def set_all_previous_versions(self, previous_versions: Set[BillId]) -> None:
        self.all_previous_versions = previous_versions

    def get_substituted_by(self) -> Optional[BaseBillId]:
        return self.substituted_by

    def set_substituted_by(self, substituted_by: BaseBillId) -> None:
        self.substituted_by = substituted_by

    def get_actions(self) -> List[BillAction]:
        return self.actions

    def set_actions(self, actions: List[BillAction]) -> None:
        self.actions = actions

    def get_sponsor(self) -> Optional[BillSponsor]:
        return self.sponsor

    def set_sponsor(self, sponsor: BillSponsor) -> None:
        self.sponsor = sponsor

    def set_ldblurb(self, blurb: str) -> None:
        self.ldblurb = blurb

    def get_past_committees(self) -> Set[CommitteeVersionId]:
        return self.past_committees

    def set_past_committees(self, past_committees: Set[CommitteeVersionId]) -> None:
        self.past_committees = past_committees

    def get_additional_sponsors(self) -> List[SessionMember]:
        return self.additional_sponsors

    def set_additional_sponsors(self, additional_sponsors: List[SessionMember]) -> None:
        self.additional_sponsors = additional_sponsors

    def get_program_info(self) -> Optional[ProgramInfo]:
        return self.program_info

    def set_program_info(self, program_info: ProgramInfo) -> None:
        self.program_info = program_info

    def get_committee_agendas(self) -> List[CommitteeAgendaId]:
        return self.committee_agendas

    def set_committee_agendas(self, committee_agendas: List[CommitteeAgendaId]) -> None:
        self.committee_agendas = committee_agendas

    def get_calendars(self) -> List[CalendarId]:
        return self.calendars

    def set_calendars(self, calendars: List[CalendarId]) -> None:
        self.calendars = calendars

    def get_chapter_num(self) -> Optional[int]:
        return self.chapter_num

    def set_chapter_num(self, chapter_num: int) -> None:
        self.chapter_num = chapter_num

    def get_chapter_year(self) -> Optional[int]:
        return self.chapter_year

    def set_chapter_year(self, chapter_year: int) -> None:
        self.chapter_year = chapter_year

    def get_federal_congress(self) -> Optional[int]:
        return self.federal_congress

    def set_federal_congress(self, federal_congress: int) -> None:
        self.federal_congress = federal_congress

    def get_federal_source(self) -> Optional[str]:
        return self.federal_source

    def set_federal_source(self, federal_source: str) -> None:
        self.federal_source = federal_source

    @staticmethod
    def congress_to_session_year(congress: int) -> int:
        if 1 <= congress <= 117:
            return 1789 + (congress - 1) * 2
        elif congress == 118:
            return 2023
        elif congress == 119:
            return 2025
        raise ValueError(f"Unsupported congress number: {congress}")

    def set_reprint_of(self, reprint_of: BillId) -> None:
        self.reprint_of = reprint_of

    def get_reprint_of(self) -> Optional[BillId]:
        return self.reprint_of

    def has_valid_laws(self, version: Version) -> bool:
        if version is None or not self.has_amendment(version):
            return False
        status = self.amend_publish_status_map.get(version)
        if status is None:
            return False
        publish_date = status.effect_date_time
        if publish_date is None:
            return False
        law_start_date = datetime(2014, 1, 1)
        return publish_date > law_start_date

class BillInfo(BaseModel):
    bill: Bill

class BillType(str, Enum):
    ASSEMBLY = "A"
    SENATE = "S"
    # Add other types as needed

    def get_chamber(self) -> Chamber:
        if self.value == "A":
            return Chamber.ASSEMBLY
        elif self.value == "S":
            return Chamber.SENATE
        return Chamber.SENATE  # Default

    def is_resolution(self) -> bool:
        return self.value in ["R", "J", "K", "L", "E"]  # Simplified