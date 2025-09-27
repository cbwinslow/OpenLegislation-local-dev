from pydantic import BaseModel
from typing import List, Dict, Set, Optional

from .base_bill_id import BaseBillId
from .version import Version
from .bill_id import BillId

class Bill(BaseModel):
    base_bill_id: BaseBillId
    title: str = ""
    summary: str = ""
    status: str  # BillStatus
    ldblurb: str = ""
    milestones: List[str] = []  # List[BillStatus]
    amendment_map: Dict[Version, str] = {}  # Dict[Version, BillAmendment]
    amend_publish_status_map: Dict[Version, str] = {}  # Dict[Version, PublishStatus]
    veto_messages: Dict[str, str] = {}  # Dict[VetoId, VetoMessage]
    approval_message: Optional[str] = None  # ApprovalMessage
    active_version: Version = Version.ORIGINAL
    sponsor: str  # BillSponsor
    additional_sponsors: List[str] = []  # List[SessionMember]
    past_committees: Set[str] = set()  # Set[CommitteeVersionId]
    actions: List[str] = []  # List[BillAction]
    substituted_by: Optional[BaseBillId] = None
    reprint_of: Optional[BillId] = None
    direct_previous_version: Optional[BillId] = None
    all_previous_versions: Set[BillId] = set()
    program_info: Optional[str] = None  # ProgramInfo
    committee_agendas: List[str] = []  # List[CommitteeAgendaId]
    calendars: List[str] = []  # List[CalendarId]
    chapter_num: Optional[int] = None
    chapter_year: Optional[int] = None
    federal_congress: Optional[int] = None
    federal_source: Optional[str] = None

    def __init__(self, base_bill_id: BaseBillId, **data):
        super().__init__(base_bill_id=base_bill_id, **data)

    # Add methods as needed