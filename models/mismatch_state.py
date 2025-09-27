from enum import Enum

class MismatchState(Enum):
    """The state of a mismatch, open if this mismatch still exists, closed if it has been resolved."""
    OPEN = "OPEN"
    CLOSED = "CLOSED"