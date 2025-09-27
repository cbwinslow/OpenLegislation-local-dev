from __future__ import annotations
from typing import Optional, Set
from datetime import datetime, date, time
from enum import Enum
import re
from pydantic import BaseModel, Field, validator

# --- Enums and Value Objects ---

class DayType(str, Enum):
    LEGISLATIVE = "LEGISLATIVE"
    SESSION = "SESSION"

    @staticmethod
    def from_text(transcript_text: str) -> Optional["DayType"]:
        speakers: Set[str] = set()
        for line in transcript_text.splitlines():
            # Remove time stamps and "The order of business:"
            line = re.sub(r'\d{1,2}:\d{1,2}', '', line)
            line = line.replace("The order of business:", "")
            if ":" in line:
                # Isolate speaker names
                speaker = re.sub(r'^ *\d* *|:', '', line).strip().upper()
                speakers.add(speaker)
        # Legislative days only have the Secretary and President speaking.
        if len(speakers) == 2:
            return DayType.LEGISLATIVE
        elif len(speakers) > 2:
            return DayType.SESSION
        return None

class SessionType:
    _type_pattern = re.compile(r"(.*)(SESSION)(.*)")
    _regular = "Regular"

    def __init__(self, session_type_str: str):
        if "SECOND" in session_type_str:
            session_type_str = session_type_str.replace("SECOND ", "")
            session_type_str += " II"
        matcher = self._type_pattern.match(session_type_str.upper().replace(" ", ""))
        if not matcher or not self._validate(matcher):
            raise ValueError(f"Cannot parse session label: {session_type_str}")
        capitals = " ".join(word.capitalize() for word in (matcher.group(1) + " " + matcher.group(2)).split())
        self._type_string = capitals + ("" if not matcher.group(3) else " " + matcher.group(3))

    def _validate(self, matcher) -> bool:
        if self._regular.upper() == matcher.group(1) and not matcher.group(3):
            return True
        elif "EXTRAORDINARY" == matcher.group(1):
            try:
                self._numeral_to_int(matcher.group(3))
                return True
            except (ValueError, TypeError):
                pass
        return False

    @staticmethod
    def _numeral_to_int(numeral: str) -> int:
        # Simple numeral to int conversion
        roman = {"I": 1, "II": 2, "III": 3, "IV": 4, "V": 5, "VI": 6, "VII": 7, "VIII": 8, "IX": 9, "X": 10}
        return roman.get(numeral, int(numeral))

    def __str__(self) -> str:
        return self._type_string

    def __eq__(self, other) -> bool:
        if not isinstance(other, SessionType):
            return False
        return self._compare_to(other) == 0

    def __lt__(self, other) -> bool:
        return self._compare_to(other) < 0

    def __hash__(self) -> int:
        return hash(self._type_string)

    def _compare_to(self, other: "SessionType") -> int:
        # Regular sessions come first
        if self._type_string.startswith(self._regular) or other._type_string.startswith(self._regular):
            return other._type_string.__cmp__(self._type_string)  # Python 3 doesn't have __cmp__, use comparison
        return self._type_string.__cmp__(other._type_string)

class TranscriptId(BaseModel):
    date_time: datetime
    session_type: SessionType

    @classmethod
    def from_datetime_and_type(cls, date_time: datetime, type_str: str) -> "TranscriptId":
        return cls(date_time=date_time, session_type=SessionType(type_str))

    def __str__(self) -> str:
        return f"({self.date_time}, {self.session_type})"

    def __eq__(self, other) -> bool:
        if not isinstance(other, TranscriptId):
            return False
        return self.date_time == other.date_time and self.session_type == other.session_type

    def __lt__(self, other) -> bool:
        if self.date_time != other.date_time:
            return self.date_time < other.date_time
        return self.session_type < other.session_type

    def __hash__(self) -> int:
        return hash((self.date_time, self.session_type))

# --- Hearing Domain ---

class Chamber(str, Enum):
    SENATE = "SENATE"
    ASSEMBLY = "ASSEMBLY"

class HearingHostType(str, Enum):
    COMMITTEE = "COMMITTEE"
    LEGISLATIVE_COMMISSION = "LEGISLATIVE COMMISSION"
    TASK_FORCE = "TASK FORCE"
    MAJORITY_COALITION = "MAJORITY COALITION"
    WHOLE_CHAMBER = "WHOLE CHAMBER"

    _type_labels = "|".join([e.value for e in HearingHostType])
    _committee_label = r"(STANDING\s*)?(SUB)?" + HearingHostType.COMMITTEE.value + r"(S)?"
    _coalition_and_task_force = HearingHostType.MAJORITY_COALITION.value + r"\sJOINT " + HearingHostType.TASK_FORCE.value

    @classmethod
    def to_type(cls, type_str: str) -> "HearingHostType":
        return cls(type_str.strip().replace(" ", "_").upper())

    @classmethod
    def standardize_host_block(cls, block: str) -> str:
        block = re.sub(cls._committee_label, HearingHostType.COMMITTEE.value, block)
        # The parser can't handle the multiple types that some hearings have.
        return re.sub(cls._coalition_and_task_force, HearingHostType.TASK_FORCE.value, block)

class HearingHost(BaseModel):
    chamber: Chamber
    type: HearingHostType
    name: str

    _irrelevant_text = r"^(\s?(ON|FOR|THE|AND|,))+|((,|THE|AND|;)\s?)+$"

    def __init__(self, **data):
        super().__init__(**data)
        self.name = self._standardize_name(self.name)

    @classmethod
    def get_hosts(cls, type_str: str, raw_name: str, chamber: Optional[Chamber]) -> list["HearingHost"]:
        hosts = []
        # Denotes a joint host.
        if chamber is None:
            hosts.extend(cls.get_hosts(type_str, raw_name, Chamber.SENATE))
            hosts.extend(cls.get_hosts(type_str, raw_name, Chamber.ASSEMBLY))
            return hosts
        type_ = HearingHostType.to_type(type_str)
        standardized_text = cls._standardize_name(raw_name)
        # When there is a list of committees, sometimes only the first is marked as a committee,
        # and the names are separated by semicolons.
        host_texts = standardized_text.split(";")
        for host_text in host_texts:
            host = cls(chamber=chamber, type=type_, name=host_text)
            hosts.append(host)
        return hosts

    @classmethod
    def _standardize_name(cls, name: str) -> str:
        return name.upper().replace(r'\s+', ' ').replace(', AND| &', ' AND').replace(cls._irrelevant_text, '').strip()

class HearingId(BaseModel):
    id: int

    def __str__(self) -> str:
        return str(self.id)

    def __eq__(self, other) -> bool:
        if not isinstance(other, HearingId):
            return False
        return self.id == other.id

    def __lt__(self, other) -> bool:
        return self.id < other.id

    def __hash__(self) -> int:
        return hash(self.id)

# --- Main Models ---

class Transcript(BaseModel):
    id: TranscriptId
    day_type: DayType
    location: Optional[str] = None
    text: Optional[str] = None
    filename: Optional[str] = None
    session_year: int = Field(..., description="Year of the session")

    def __init__(self, **data):
        super().__init__(**data)
        if self.day_type is None:
            raise ValueError("dayType cannot be null")

    @validator("session_year", pre=True, always=True)
    def set_session_year(cls, v, values):
        if v is not None:
            return v
        id_ = values.get("id")
        if id_ and hasattr(id_, "date_time"):
            return id_.date_time.year
        return None

    def get_id(self) -> TranscriptId:
        return self.id

    def get_date_time(self) -> datetime:
        return self.id.date_time

    def get_session_type(self) -> str:
        return str(self.id.session_type)

    def get_day_type(self) -> DayType:
        return self.day_type

    def get_location(self) -> Optional[str]:
        return self.location

    def get_text(self) -> Optional[str]:
        return self.text

    def get_filename(self) -> Optional[str]:
        return self.filename

    def __eq__(self, other) -> bool:
        if self is other:
            return True
        if not isinstance(other, Transcript):
            return False
        return (
            self.id == other.id and
            self.day_type == other.day_type and
            self.location == other.location and
            self.text == other.text and
            self.filename == other.filename
        )

    def __hash__(self) -> int:
        return hash((self.id, self.day_type, self.location, self.text, self.filename))

class Hearing(BaseModel):
    id: Optional[HearingId] = None
    filename: str
    text: str
    title: str
    address: str
    date: date
    start_time: Optional[time] = None
    end_time: Optional[time] = None
    hosts: Optional[Set[HearingHost]] = None
    session_year: int = Field(..., description="Year of the session")

    def __init__(self, **data):
        super().__init__(**data)
        self.session_year = self.date.year

    def set_id(self, id_: HearingId) -> None:
        self.id = id_

    def get_id(self) -> Optional[HearingId]:
        return self.id

    def get_text(self) -> str:
        return self.text

    def get_date(self) -> date:
        return self.date

    def get_title(self) -> str:
        return self.title

    def get_address(self) -> str:
        return self.address

    def get_hosts(self) -> Optional[Set[HearingHost]]:
        return self.hosts

    def set_hosts(self, hosts: Set[HearingHost]) -> None:
        self.hosts = hosts

    def get_start_time(self) -> Optional[time]:
        return self.start_time

    def get_end_time(self) -> Optional[time]:
        return self.end_time

    def get_filename(self) -> str:
        return self.filename

    def __eq__(self, other) -> bool:
        if self is other:
            return True
        if not isinstance(other, Hearing):
            return False
        return (
            self.id == other.id and
            self.filename == other.filename and
            self.text == other.text and
            self.title == other.title and
            self.address == other.address and
            self.date == other.date and
            self.start_time == other.start_time and
            self.end_time == other.end_time and
            self.hosts == other.hosts
        )

    def __hash__(self) -> int:
        return hash((self.id, self.filename, self.text, self.title, self.address, self.date, self.start_time, self.end_time, self.hosts))

# --- Exceptions ---

class TranscriptNotFoundEx(Exception):
    pass

class HearingNotFoundEx(Exception):
    pass

class DuplicateTranscriptEx(Exception):
    pass

class TranscriptNotFoundEx(Exception):
    def __init__(self, transcript_id: Optional[TranscriptId], ex: Optional[Exception] = None):
        msg = (
            f"Transcript {transcript_id} could not be retrieved."
            if transcript_id else "Transcript could not be retrieved since the given TranscriptId was null"
        )
        super().__init__(msg)
        self.transcript_id = transcript_id
        self.__cause__ = ex

class DuplicateTranscriptEx(Exception):
    def __init__(self, date_time: datetime):
        super().__init__(f"There are multiple transcripts at {date_time}. Please specify.")
        self.date_time = date_time
