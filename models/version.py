from enum import Enum
from typing import List

class Version(str, Enum):
    ORIGINAL = ""
    A = "A"
    B = "B"
    C = "C"
    D = "D"
    E = "E"
    F = "F"
    G = "G"
    H = "H"
    I = "I"
    J = "J"
    K = "K"
    L = "L"
    M = "M"
    N = "N"
    O = "O"
    P = "P"
    Q = "Q"
    R = "R"
    S = "S"
    T = "T"
    U = "U"
    V = "V"
    W = "W"
    X = "X"
    Y = "Y"
    Z = "Z"

    @classmethod
    def of(cls, version: str) -> 'Version':
        clean_version = (version or "").strip().upper()
        if not clean_version or clean_version == "DEFAULT":
            return cls.ORIGINAL
        return cls(clean_version)

    @classmethod
    def before(cls, v: 'Version') -> List['Version']:
        return [ver for ver in cls if ver.value < v.value]

    @classmethod
    def after(cls, v: 'Version') -> List['Version']:
        return [ver for ver in cls if ver.value > v.value]

    def __str__(self):
        return self.value