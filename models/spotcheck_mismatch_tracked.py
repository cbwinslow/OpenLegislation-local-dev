from enum import Enum

class SpotCheckMismatchTracked(Enum):
    TRACKED = "TRACKED"
    UNTRACKED = "UNTRACKED"

    @staticmethod
    def get_from_boolean(tracked: bool):
        return SpotCheckMismatchTracked.TRACKED if tracked else SpotCheckMismatchTracked.UNTRACKED