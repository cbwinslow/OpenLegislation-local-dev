from __future__ import annotations

from enum import Enum

from .chamber import Chamber


class BillType(str, Enum):
    S = ("S", Chamber.SENATE, "Senate", False)
    J = ("J", Chamber.SENATE, "Regular and Joint", True)
    B = ("B", Chamber.SENATE, "Concurrent", True)
    R = ("R", Chamber.SENATE, "Rules and Extraordinary Session", True)
    A = ("A", Chamber.ASSEMBLY, "Assembly", False)
    K = ("K", Chamber.ASSEMBLY, "Regular", True)
    C = ("C", Chamber.ASSEMBLY, "Concurrent", True)
    E = ("E", Chamber.ASSEMBLY, "Rules and Extraordinary Session", True)
    L = ("L", Chamber.ASSEMBLY, "Joint", True)

    def __new__(cls, value: str, chamber: Chamber, name: str, resolution: bool):
        obj = str.__new__(cls, value)
        obj._value_ = value
        obj._chamber = chamber
        obj._full_name = name
        obj._is_resolution = resolution
        return obj

    @property
    def chamber(self) -> Chamber:
        return self._chamber

    @property
    def full_name(self) -> str:
        return self._full_name

    def get_chamber(self) -> Chamber:
        return self._chamber

    def get_name(self) -> str:
        return self._full_name

    def is_resolution(self) -> bool:
        return self._is_resolution

    @classmethod
    def from_value(cls, value: str) -> "BillType":
        if value is None:
            raise ValueError("BillType value cannot be None")
        normalized = value.strip().upper()
        try:
            return cls(normalized)
        except ValueError as exc:
            raise ValueError(f"Unknown bill type '{value}'") from exc
