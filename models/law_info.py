from __future__ import annotations
from typing import Optional
from enum import Enum
from pydantic import BaseModel

class LawType(str, Enum):
    CONSOLIDATED = "CONSOLIDATED"
    UNCONSOLIDATED = "UNCONSOLIDATED"
    COURT_ACTS = "COURT_ACTS"
    RULES = "RULES"
    MISC = "MISC"

class LawInfo(BaseModel):
    law_id: Optional[str] = None
    name: Optional[str] = None
    chapter_id: Optional[str] = None
    type: Optional[LawType] = None

    def __str__(self) -> str:
        return f"LawInfo {{lawId='{self.law_id}', name='{self.name}', chapterId='{self.chapter_id}', type={self.type}}}"

    def __eq__(self, other) -> bool:
        if not isinstance(other, LawInfo):
            return False
        return self.law_id == other.law_id

    def __lt__(self, other) -> bool:
        if self.law_id and other.law_id:
            return self.law_id < other.law_id
        return False

    # Getters and setters
    def get_law_id(self) -> Optional[str]:
        return self.law_id

    def set_law_id(self, law_id: str) -> None:
        self.law_id = law_id

    def get_name(self) -> Optional[str]:
        return self.name

    def set_name(self, name: str) -> None:
        self.name = name

    def get_chapter_id(self) -> Optional[str]:
        return self.chapter_id

    def set_chapter_id(self, chapter_id: str) -> None:
        self.chapter_id = chapter_id

    def get_type(self) -> Optional[LawType]:
        return self.type

    def set_type(self, type_: LawType) -> None:
        self.type = type_

# Note: LawChapterCode enum would be extensive; implement as needed based on actual usage
# For now, keeping it minimal as in the original simplified version
