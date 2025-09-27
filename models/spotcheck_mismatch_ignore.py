from enum import Enum

class SpotCheckMismatchIgnore(Enum):
    NOT_IGNORED = -1
    IGNORE_PERMANENTLY = 0
    IGNORE_UNTIL_RESOLVED = 1
    IGNORE_ONCE = 2

    @property
    def get_code(self) -> int:
        return self.value