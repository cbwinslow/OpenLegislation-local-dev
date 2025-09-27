import re
from functools import total_ordering
import datetime
from pydantic import BaseModel, field_validator, model_validator, Field
from typing import ClassVar, Any, Optional, List, Dict, Set
from collections import defaultdict
import json

from models.session import SessionYear
from models.enums import (
    BillType, Version, Chamber, BillStatusType, VetoType, BillVoteType,
    BillVoteCode, TextDiffType, BillTextFormat
)
from models.member import SessionMember
from models.committee import CommitteeId, CommitteeVersionId
from models.attendance import SenateVoteAttendance
from models import bill_text_utils
from models.publish_status import PublishStatus
from models.agenda import CommitteeAgendaId
from models.calendar import CalendarId
from models.base import BaseLegislativeContent


@total_ordering
class BillId(BaseModel):
    base_print_no: str
    session: SessionYear
    version: Version = Version.ORIGINAL
    PRINT_NUMBER_REGEX: ClassVar[str] = "([ASLREJKBC])(\\d{1,5})"
    FULL_PRINT_NUMBER_REGEX: ClassVar[str] = f"^{PRINT_NUMBER_REGEX}([A-Z]?)$"
    PRINT_NUMBER_PATTERN: ClassVar[re.Pattern] = re.compile(FULL_PRINT_NUMBER_REGEX)
    BILL_ID_PATTERN: ClassVar[re.Pattern] = re.compile(f"(?P<printNo>{FULL_PRINT_NUMBER_REGEX})-(?P<year>\\d{{4}})")
    @model_validator(mode='before')
    @classmethod
    def pre_process(cls, data: Any) -> Any:
        if not isinstance(data, dict): return data
        if 'print_no' in data:
            print_no, session_val = data.pop('print_no'), data.get('session')
            if not print_no or not session_val: raise ValueError("Both 'print_no' and 'session' must be provided.")
            normalized_print_no = cls._validate_and_normalize_full_print_no(print_no)
            version_char = normalized_print_no[-1]
            if version_char.isalpha():
                data['version'] = Version.of(version_char)
                data['base_print_no'] = normalized_print_no[:-1]
            else:
                data['version'] = Version.ORIGINAL
                data['base_print_no'] = normalized_print_no
        if isinstance(data.get('session'), int): data['session'] = SessionYear(year=data['session'])
        if 'version' in data and isinstance(data['version'], str): data['version'] = Version.of(data['version'])
        return data
    @field_validator('base_print_no')
    @classmethod
    def validate_base_print_no(cls, v: str) -> str:
        if not v or not v.strip(): raise ValueError("Base print number cannot be empty.")
        normalized = v.strip().upper()
        if not re.fullmatch(cls.PRINT_NUMBER_REGEX, normalized): raise ValueError(f"Invalid base_print_no format: {v}")
        return normalized[0] + normalized[1:].lstrip('0')
    @staticmethod
    def _validate_and_normalize_full_print_no(print_no: str) -> str:
        if not print_no or not print_no.strip(): raise ValueError("PrintNo cannot be null or empty.")
        normalized = print_no.strip().upper()
        if not re.fullmatch(BillId.FULL_PRINT_NUMBER_REGEX, normalized): raise ValueError(f"PrintNo '{print_no}' does not match the required pattern.")
        try: BillType[normalized[0]]
        except KeyError: raise ValueError(f"PrintNo '{print_no}' must begin with a valid letter designator.")
        return normalized
    @property
    def print_no(self) -> str: return f"{self.base_print_no}{self.version}"
    @property
    def bill_type(self) -> BillType: return BillType[self.base_print_no[0]]
    @property
    def chamber(self) -> Chamber: return self.bill_type.chamber
    @property
    def number(self) -> int: return int(re.sub(r"[^\d]", "", self.base_print_no))
    @staticmethod
    def is_base_version(version: Version) -> bool: return version is None or version == Version.ORIGINAL
    @property
    def padded_bill_id_string(self) -> str: return f"{self.padded_print_number}-{self.session.year}"
    @property
    def padded_print_number(self) -> str:
        match = re.match(self.PRINT_NUMBER_REGEX, self.base_print_no)
        if match: return f"{match.group(1)}{int(match.group(2)):05d}{self.version}"
        return ""
    def __str__(self): return f"{self.print_no}-{self.session.year}"
    def __eq__(self, other):
        if not isinstance(other, BillId): return NotImplemented
        return (self.session == other.session and self.base_print_no == other.base_print_no and self.version == other.version)
    def __lt__(self, other):
        if not isinstance(other, BillId): return NotImplemented
        return (self.session, self.base_print_no, self.version.value) < (other.session, other.base_print_no, other.version.value)
    def __hash__(self): return hash((self.base_print_no, self.session, self.version))
    def equals_base(self, other) -> bool:
        if not isinstance(other, BillId): return False
        return self.session == other.session and self.base_print_no == other.base_print_no
    def hash_base(self) -> int: return hash((self.base_print_no, self.session))
    class Config: from_attributes = True; frozen = True; arbitrary_types_allowed = True; validate_assignment = True

class BaseBillId(BillId):
    version: Version = Field(default=Version.ORIGINAL, frozen=True)
    @field_validator('version', mode='before')
    @classmethod
    def _force_base_version(cls, v: Any) -> Version: return Version.ORIGINAL
    @classmethod
    def of(cls, bill_id: BillId): return cls(base_print_no=bill_id.base_print_no, session=bill_id.session)
    def with_version(self, version: Version): return BillId(base_print_no=self.base_print_no, session=self.session, version=version)

@total_ordering
class BillAction(BaseModel):
    bill_id: BillId; date: datetime.date; chamber: Chamber; sequence_no: int = 0; text: str = ""; action_type: str
    def __str__(self): return f"{self.date} ({self.chamber.name}) {self.text}"
    def __eq__(self, other):
        if not isinstance(other, BillAction): return NotImplemented
        return (self.bill_id.equals_base(other.bill_id) and self.date == other.date and self.sequence_no == other.sequence_no and self.chamber == other.chamber and self.text.lower() == other.text.lower())
    def __hash__(self): return (31 * self.bill_id.hash_base() + hash((self.date, self.sequence_no, self.chamber, self.text.lower())))
    def __lt__(self, other):
        if not isinstance(other, BillAction): return NotImplemented
        return self.sequence_no < other.sequence_no
    class Config: arbitrary_types_allowed = True

class BillStatus(BaseModel):
    status_type: BillStatusType; action_date: datetime.date; action_sequence_no: int = 0; committee_id: Optional[CommitteeId] = None; calendar_no: Optional[int] = None
    def __str__(self):
        parts = [f"{self.status_type.value} ({self.action_date})"]
        if self.committee_id: parts.append(str(self.committee_id))
        if self.calendar_no: parts.append(f"Cal No: {self.calendar_no}")
        return " ".join(parts)
    class Config: arbitrary_types_allowed = True

@total_ordering
class ApprovalId(BaseModel):
    year: int; approval_number: int
    def __str__(self): return f"{self.year}-{self.approval_number}"
    def __eq__(self, other):
        if not isinstance(other, ApprovalId): return NotImplemented
        return self.year == other.year and self.approval_number == other.approval_number
    def __hash__(self): return hash((self.year, self.approval_number))
    def __lt__(self, other):
        if not isinstance(other, ApprovalId): return NotImplemented
        if self.year != other.year: return self.year < other.year
        return self.approval_number < other.approval_number
    class Config: frozen = True

@total_ordering
class ApprovalMessage(BaseLegislativeContent):
    bill_id: BillId; approval_number: int; memo_text: Optional[str] = None; chapter: int; signer: Optional[str] = None
    @property
    def approval_id(self) -> ApprovalId: return ApprovalId(year=self.year, approval_number=self.approval_number)
    def __lt__(self, other):
        if not isinstance(other, ApprovalMessage): return NotImplemented
        return self.approval_id < other.approval_id
    class Config: arbitrary_types_allowed = True

@total_ordering
class VetoId(BaseModel):
    year: int; veto_number: int
    def __str__(self): return f"{self.year}-{self.veto_number}"
    def __eq__(self, other):
        if not isinstance(other, VetoId): return NotImplemented
        return self.year == other.year and self.veto_number == other.veto_number
    def __hash__(self): return hash((self.year, self.veto_number))
    def __lt__(self, other):
        if not isinstance(other, VetoId): return NotImplemented
        if self.year != other.year: return self.year < other.year
        return self.veto_number < other.veto_number
    class Config: frozen = True

@total_ordering
class VetoMessage(BaseLegislativeContent):
    bill_id: BaseBillId; veto_number: int; memo_text: Optional[str] = None; veto_type: VetoType; chapter: int; bill_page: int; line_start: int; line_end: int; signer: Optional[str] = None; signed_date: Optional[datetime.date] = None
    @property
    def veto_id(self) -> VetoId: return VetoId(year=self.year, veto_number=self.veto_number)
    def __lt__(self, other):
        if not isinstance(other, VetoMessage): return NotImplemented
        return self.veto_id < other.veto_id
    class Config: arbitrary_types_allowed = True

class ProgramInfo(BaseModel):
    info: str; number: int
    class Config: frozen = True

@total_ordering
class BillVoteId(BaseModel):
    bill_id: BillId; vote_date: datetime.date; vote_type: BillVoteType; sequence_no: int; committee_id: Optional[CommitteeId] = None
    def __lt__(self, other):
        if not isinstance(other, BillVoteId): return NotImplemented
        t1 = (self.bill_id, self.vote_date, self.vote_type.value, self.sequence_no, (self.committee_id is None, self.committee_id))
        t2 = (other.bill_id, other.vote_date, other.vote_type.value, other.sequence_no, (other.committee_id is None, other.committee_id))
        return t1 < t2
    class Config: frozen = True; arbitrary_types_allowed = True

@total_ordering
class BillVote(BaseLegislativeContent):
    bill_id: BillId; vote_type: BillVoteType; vote_date: datetime.date; sequence_no: int = 1; committee_id: Optional[CommitteeId] = None; member_votes: Dict[BillVoteCode, List[SessionMember]] = Field(default_factory=lambda: defaultdict(list)); attendance: SenateVoteAttendance
    @model_validator(mode='before')
    @classmethod
    def _prepare_fields(cls, data: Any) -> Any:
        if isinstance(data, dict):
            if 'vote_id' in data:
                vote_id = data.pop('vote_id')
                data.update({'bill_id': vote_id.bill_id, 'vote_date': vote_id.vote_date, 'vote_type': vote_id.vote_type, 'sequence_no': vote_id.sequence_no, 'committee_id': vote_id.committee_id})
            if 'vote_date' in data and 'year' not in data: data['year'] = data['vote_date'].year
            if 'attendance' not in data:
                if 'year' in data: data['attendance'] = {'year': data['year']}
                else: raise ValueError("Cannot create BillVote without 'year' or 'vote_date' to infer it.")
        return data
    @property
    def vote_id(self) -> BillVoteId: return BillVoteId(bill_id=self.bill_id, vote_date=self.vote_date, vote_type=self.vote_type, sequence_no=self.sequence_no, committee_id=self.committee_id)
    def get_members_by_vote(self, vote_code: BillVoteCode) -> set[SessionMember]: return set(self.member_votes.get(vote_code, []))
    def add_member_vote(self, vote_code: BillVoteCode, member: SessionMember): self.member_votes[vote_code].append(member)
    def count(self) -> int: return sum(len(v) for v in self.member_votes.values())
    def get_vote_counts(self) -> Dict[BillVoteCode, int]: return {code: len(members) for code, members in self.member_votes.items()}
    def __eq__(self, other):
        if not isinstance(other, BillVote): return NotImplemented
        return (self.bill_id == other.bill_id and self.vote_type == other.vote_type and self.vote_date == other.vote_date and self.sequence_no == other.sequence_no and self.committee_id == other.committee_id and self.attendance == other.attendance and {k: v for k, v in self.member_votes.items()} == {k: v for k, v in other.member_votes.items()})
    def __lt__(self, other):
        if not isinstance(other, BillVote): return NotImplemented
        return (self.vote_date, self.vote_type.value) < (other.vote_date, other.vote_type.value)
    def __hash__(self): return hash((self.bill_id, self.vote_type, self.vote_date, frozenset((k, tuple(v)) for k, v in self.member_votes.items()), self.sequence_no, self.committee_id, self.attendance))
    class Config: arbitrary_types_allowed = True

class TextDiff(BaseModel):
    diff_type: TextDiffType; raw_text: str
    @property
    def plain_format_text(self) -> str:
        type_val = self.diff_type.type
        if type_val == 0: return self.raw_text
        elif type_val == 1: return self.raw_text.upper()
        elif type_val == -1: return self.raw_text
        return ""
    @property
    def html_format_text(self) -> str: return f"{self.diff_type.html_opening_tags}{self.raw_text}{self.diff_type.html_closing_tags}"
    @property
    def template_format_text(self) -> str:
        if not self.diff_type.template_css_class: return self.raw_text
        return f'<span class="{" ".join(self.diff_type.template_css_class)}">{self.raw_text}</span>'
    @property
    def text(self) -> str: return self.raw_text
    @property
    def css_classes(self) -> List[str]: return self.diff_type.template_css_class
    class Config: frozen = True; arbitrary_types_allowed = True

class BillText(BaseModel):
    HTML_STYLE: ClassVar[str] = "<STYLE><!--u  {color: Green}s  {color: RED} i  {color: DARKBLUE; background-color:yellow}\n" + "p.brk {page-break-before:always}--></STYLE>\n"
    sobi_plain_text: str = ""; diffs: List[TextDiff] = Field(default_factory=list)
    def get_full_text(self, format: BillTextFormat) -> str:
        if format == BillTextFormat.PLAIN: return bill_text_utils.format_html_extracted_bill_text(self._create_plain_text())
        elif format == BillTextFormat.HTML: return self._create_html_text()
        elif format == BillTextFormat.TEMPLATE: return self._create_template_text()
        return ""
    def _create_plain_text(self) -> str:
        if not self.diffs and self.sobi_plain_text: return self.sobi_plain_text
        return "".join(diff.plain_format_text for diff in self.diffs)
    def _create_html_text(self) -> str:
        if not self.diffs: return ""
        return "".join([self.HTML_STYLE, "<pre>"] + [diff.html_format_text for diff in self.diffs] + ["</pre>"])
    def _create_template_text(self) -> str:
        if not self.diffs: return ""
        return "".join(['<pre class="ol-bill-text">'] + [diff.template_format_text for diff in self.diffs] + ["</pre>"])
    class Config: arbitrary_types_allowed = True

class BillSponsor(BaseModel):
    member: Optional[SessionMember] = None; budget: bool = False; rules: bool = False; redistricting: bool = False
    @property
    def has_member(self) -> bool: return self.member is not None
    def __str__(self):
        if not self.rules and not self.budget and not self.redistricting:
            if self.member: return self.member.lbdc_short_name
            return ""
        s = "RULES" if self.rules else "BUDGET BILL" if self.budget else "REDISTRICTING"
        if self.has_member: s += f" ({self.member.lbdc_short_name})"
        return s.strip()
    class Config: arbitrary_types_allowed = True

class BillAmendment(BaseModel):
    base_bill_id: BaseBillId; version: Version; same_as: Set[BillId] = Field(default_factory=set); memo: str = ""; law_section: str = ""; related_laws_json: str = ""; law_code: str = ""; act_clause: str = ""; bill_text: BillText = Field(default_factory=BillText); current_committee: Optional[CommitteeVersionId] = None; co_sponsors: List[SessionMember] = Field(default_factory=list); multi_sponsors: List[SessionMember] = Field(default_factory=list); stricken: bool = False; votes_map: Dict[BillVoteId, BillVote] = Field(default_factory=dict); uni_bill: bool = False
    @property
    def bill_id(self) -> BillId: return self.base_bill_id.with_version(self.version)
    @property
    def bill_type(self) -> BillType: return self.bill_id.bill_type
    def get_full_text(self, format: BillTextFormat) -> str: return self.bill_text.get_full_text(format)
    def update_vote(self, vote: BillVote): self.votes_map[vote.vote_id] = vote
    @property
    def votes_list(self) -> List[BillVote]: return list(self.votes_map.values())
    @property
    def is_resolution(self) -> bool: return self.bill_type.is_resolution
    @property
    def related_laws_map(self) -> Dict[str, List[str]]:
        if not self.related_laws_json: return {}
        return json.loads(self.related_laws_json)
    class Config: arbitrary_types_allowed = True

class BillAmendNotFoundEx(Exception):
    def __init__(self, bill_id: BillId):
        self.bill_id = bill_id
        super().__init__(f"Bill amendment not found for bill: {bill_id}")

@total_ordering
class Bill(BaseLegislativeContent):
    base_bill_id: BaseBillId; title: str = ""; summary: str = ""; status: Optional[BillStatus] = None; ldblurb: str = ""; milestones: List[BillStatus] = Field(default_factory=list); amendment_map: Dict[Version, BillAmendment] = Field(default_factory=dict); amend_publish_status_map: Dict[Version, PublishStatus] = Field(default_factory=dict); veto_messages: Dict[VetoId, VetoMessage] = Field(default_factory=dict); approval_message: Optional[ApprovalMessage] = None; active_version: Version = Version.ORIGINAL; sponsor: Optional[BillSponsor] = None; additional_sponsors: List[SessionMember] = Field(default_factory=list); past_committees: Set[CommitteeVersionId] = Field(default_factory=set); actions: List[BillAction] = Field(default_factory=list); substituted_by: Optional[BaseBillId] = None; reprint_of: Optional[BillId] = None; direct_previous_version: Optional[BillId] = None; all_previous_versions: Set[BillId] = Field(default_factory=set); program_info: Optional[ProgramInfo] = None; committee_agendas: List[CommitteeAgendaId] = Field(default_factory=list); calendars: List[CalendarId] = Field(default_factory=list); chapter_num: Optional[int] = None; chapter_year: Optional[int] = None; federal_congress: Optional[int] = None; federal_source: Optional[str] = None
    @model_validator(mode='before')
    @classmethod
    def _populate_from_base_id(cls, data: Any) -> Any:
        if isinstance(data, dict):
            if 'base_bill_id' in data and 'year' not in data:
                data['year'] = data['base_bill_id'].session.year
        return data
    def __lt__(self, other):
        if not isinstance(other, Bill): return NotImplemented
        return self.base_bill_id < other.base_bill_id
    def get_amendment(self, version: Version) -> BillAmendment:
        if version in self.amendment_map: return self.amendment_map[version]
        raise BillAmendNotFoundEx(self.base_bill_id.with_version(version))
    def add_amendment(self, bill_amendment: BillAmendment):
        if bill_amendment: self.amendment_map[bill_amendment.version] = bill_amendment
    @property
    def amendment_list(self) -> List[BillAmendment]: return list(self.amendment_map.values())
    @property
    def active_amendment(self) -> BillAmendment: return self.get_amendment(self.active_version)
    class Config: arbitrary_types_allowed = True