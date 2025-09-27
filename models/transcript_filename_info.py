from __future__ import annotations
from typing import Optional, Dict, Type
from datetime import date
from pydantic import BaseModel
import re

class TranscriptFilenameInfo(BaseModel):
    NUM_FIELDS = 6
    date_pattern = re.compile(r"\d{6}")
    day_type_pattern = re.compile(r"SENATE(LD)?")
    corrected_pattern = re.compile(r"CORRECTED")
    fixed_pattern = re.compile(r"FIXED$")
    version_pattern = re.compile(r"V\d+")
    session_type_pattern = re.compile(r"E")

    mismatches: Dict[Type, tuple] = {}
    priority: list = []

    def __init__(self, filename: str, date_: date, day_type: str, session_type: str):
        super().__init__()
        self.priority = [0] * self.NUM_FIELDS
        self.mismatches = {}
        clean_filename = filename.upper().replace(".TXT", "").replace(".TXT", "")
        data = self.parse_text_with_pattern(clean_filename, self.version_pattern)
        if data[0]:
            self.priority[0] = int(data[0].replace("V", ""))
        data = self.parse_text_with_pattern(data[1], self.corrected_pattern)
        if data[0]:
            self.priority[1] = 1
        data = self.parse_text_with_pattern(data[1], self.fixed_pattern)
        if data[0]:
            self.priority[2] = 1
        data = self.parse_text_with_pattern(data[1], self.date_pattern)
        date_str = f"{date_.month:02d}{date_.day:02d}{date_.year%100:02d}"
        if data[0] and data[0] != date_str:
            self.add_mismatch(date, data[0], date_str)
            self.priority[3] = -1
        data = self.parse_text_with_pattern(data[1], self.day_type_pattern)
        if data[0]:
            filename_day_type = "LEGISLATIVE" if data[0].endswith("LD") else "SESSION"
            if filename_day_type != day_type:
                self.add_mismatch(str, filename_day_type, day_type)
                self.priority[4] = -1
        data = self.parse_text_with_pattern(data[1], self.session_type_pattern)
        if data[0] and not session_type.startswith("E"):
            self.add_mismatch(str, "An Extraordinary Session", session_type)
            self.priority[5] = -1

    def is_less_accurate_than(self, old_info: 'TranscriptFilenameInfo') -> bool:
        for i in range(self.NUM_FIELDS):
            if self.priority[i] != old_info.priority[i]:
                return self.priority[i] < old_info.priority[i]
        return False

    def get_mismatches(self) -> Optional[str]:
        if not self.mismatches:
            return None
        result = ["\nType\t\tExpected\t\tActual\n"]
        for k, v in self.mismatches.items():
            result.append(f"{k.__name__}\t\t{v[0]}\t\t{v[1]}\n")
        return ''.join(result)

    def add_mismatch(self, typ, expected, actual):
        self.mismatches[typ] = (expected, actual)

    @staticmethod
    def parse_text_with_pattern(text: str, pattern) -> tuple:
        matcher = pattern.search(text)
        if not matcher:
            return None, text
        result = matcher.group()
        return result, text.replace(result, "")
