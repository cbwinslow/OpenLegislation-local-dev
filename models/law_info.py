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
    law_id: str
    name: str
    chapter_id: str
    type: LawType
    def __str__(self):
        return f"LawInfo {{lawId='{self.law_id}', name='{self.name}', chapterId='{self.chapter_id}', type={self.type}}}"
    def __eq__(self, other):
        return self.law_id == other.law_id
    def __lt__(self, other):
        return self.law_id < other.law_id

class LawChapterCode(str, Enum):
    # Only a subset for brevity; add all as needed
    ABP = "Abandoned Property"
    AGM = "Agriculture & Markets"
    ABC = "Alcoholic Beverage Control"
    ACG = "Alternative County Government"
    ACA = "Arts and Cultural Affairs"
    BNK = "Banking"
    # ... (add all codes as needed)
    # Example for unconsolidated, court acts, rules, misc
    BSW = "Boxing, Sparring and Wrestling Ch. 912/20"
    CTC = "Court of Claims Act"
    CMA = "Assembly Rules"
    CNS = "Constitution"
    # ... (add all as needed)

    @staticmethod
    def get_chapter_name(code: 'LawChapterCode') -> str:
        return code.value

    @staticmethod
    def get_type(code: 'LawChapterCode') -> LawType:
        # This is a simplified mapping; expand as needed
        consolidated = {"ABP", "AGM", "ABC", "ACG", "ACA", "BNK"}
        unconsolidated = {"BSW"}
        court_acts = {"CTC"}
        rules = {"CMA"}
        misc = {"CNS"}
        if code.name in consolidated:
            return LawType.CONSOLIDATED
        if code.name in unconsolidated:
            return LawType.UNCONSOLIDATED
        if code.name in court_acts:
            return LawType.COURT_ACTS
        if code.name in rules:
            return LawType.RULES
        if code.name in misc:
            return LawType.MISC
        return LawType.MISC
