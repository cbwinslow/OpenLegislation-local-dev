from enum import Enum
from typing import Dict, Optional

class AgendaVoteAction(Enum):
    REPORTED = "R"
    FIRST_READING = "F"
    THIRD_READING = "3"
    REFERRED_TO_COMMITTEE = "RC"
    DEFEATED = "D"
    RESTORED_TO_THIRD = "R3"
    SPECIAL = "S"

    def __init__(self, code: str):
        self.code = code

    @property
    def get_code(self) -> str:
        return self.code

    @staticmethod
    def value_of_code(code: Optional[str]) -> Optional['AgendaVoteAction']:
        if code is None:
            raise ValueError("Supplied code cannot be null when mapping to AgendaVoteAction.")
        code_upper = code.strip().upper()
        for action in AgendaVoteAction:
            if action.code == code_upper:
                return action
        return None