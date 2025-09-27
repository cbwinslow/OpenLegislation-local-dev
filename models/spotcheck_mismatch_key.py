from typing import TypeVar, Generic
from .spotcheck_mismatch_type import SpotCheckMismatchType

ContentId = TypeVar('ContentId')

class SpotCheckMismatchKey(Generic[ContentId]):
    """Identifies any spotcheck mismatches observed for a specific report type, content id, and mismatch type
    Used to group recurring mismatches"""

    def __init__(self, content_id: ContentId, mismatch_type: SpotCheckMismatchType):
        self.content_id = content_id
        self.mismatch_type = mismatch_type

    def __eq__(self, other) -> bool:
        if not isinstance(other, SpotCheckMismatchKey):
            return False
        return self.content_id == other.content_id and self.mismatch_type == other.mismatch_type

    def __hash__(self) -> int:
        return hash((self.content_id, self.mismatch_type))

    # --- Getters ---

    @property
    def get_content_id(self) -> ContentId:
        return self.content_id

    @property
    def get_mismatch_type(self) -> SpotCheckMismatchType:
        return self.mismatch_type