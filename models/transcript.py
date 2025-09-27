from __future__ import annotations
from typing import Optional, Set
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field, validator

# --- Enums and Value Objects ---

class DayType(str, Enum):
    LEGISLATIVE = "LEGISLATIVE"
    SESSION = "SESSION"

    @staticmethod
    def from_text(transcript_text: str) -> Optional["DayType"]:
        speakers: Set[str] = set()
        for line in transcript_text.splitlines():
            line = line.replace("The order of business:", "")
            if ":" in line:
                speaker = line.split(":", 1)[0].strip().upper()
                speakers.add(speaker)
        if len(speakers) == 2:
            return DayType.LEGISLATIVE
        elif len(speakers) > 2:
            return DayType.SESSION
        return None

class SessionType(str):
    def __init__(self, session_type_str: str):
        # Java logic: parse and validate session type string
        s = session_type_str.upper().replace(" ", "")
        if "SECOND" in s:
            s = s.replace("SECOND", "") + "II"
        if s.startswith("REGULARSESSION"):
            self.value = "Regular Session"
        elif s.startswith("EXTRAORDINARYSESSION"):
            self.value = "Extraordinary Session" + s[len("EXTRAORDINARYSESSION"):]
        else:
            raise ValueError(f"Cannot parse session label: {session_type_str}")
    def __str__(self):
        return self.value
    def __eq__(self, other):
        return str(self) == str(other)
    def __lt__(self, other):
        return str(self) < str(other)
    def __hash__(self):
        return hash(self.value)

class TranscriptId(BaseModel):
    date_time: datetime
    session_type: SessionType
    def __str__(self):
        return f"({self.date_time}, {self.session_type})"
    def __eq__(self, other):
        return (self.date_time, self.session_type) == (other.date_time, other.session_type)
    def __lt__(self, other):
        if self.date_time != other.date_time:
            return self.date_time < other.date_time
        return self.session_type < other.session_type

# --- Main Model ---

class Transcript(BaseModel):
    id: TranscriptId
    day_type: DayType
    location: Optional[str] = None
    text: Optional[str] = None
    filename: Optional[str] = None
    session_year: int = Field(..., description="Year of the session")

    @validator("session_year", pre=True, always=True)
    def set_session_year(cls, v, values):
        if v is not None:
            return v
        id = values.get("id")
        if id and hasattr(id, "date_time"):
            return id.date_time.year
        return None

    def get_date_time(self) -> datetime:
        return self.id.date_time

    def get_session_type(self) -> str:
        return str(self.id.session_type)

    def __eq__(self, other):
        if not isinstance(other, Transcript):
            return False
        return (
            self.id == other.id and
            self.day_type == other.day_type and
            self.location == other.location and
            self.text == other.text and
            self.filename == other.filename
        )

    def __hash__(self):
        return hash((self.id, self.day_type, self.location, self.text, self.filename))

# --- Exceptions ---

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
