from pydantic import BaseModel
from typing import Optional, List, Collection
from .spotcheck_mismatch_type import SpotCheckMismatchType
from .mismatch_state import MismatchState
from .spotcheck_mismatch_ignore import SpotCheckMismatchIgnore
from .spotcheck_mismatch_tracked import SpotCheckMismatchTracked

class SpotCheckMismatch(BaseModel):
    """Encapsulates basic information about a mismatch between the reference and target content."""

    # An integer id that uniquely identifies this mismatch
    mismatch_id: int = 0

    # The type of mismatch that occurred.
    mismatch_type: SpotCheckMismatchType

    # The status of the mismatch (new, existing, etc.)
    state: MismatchState = MismatchState.OPEN

    # String representation of the reference data. (e.g. lbdc daybreak content)
    reference_data: str = ""

    # String representation of the observed data (typically openleg processed content)
    observed_data: str = ""

    # Any details about this mismatch. (Optional)
    notes: Optional[str] = None

    # The ignore status of this mismatch. (Optional)
    ignore_status: Optional[SpotCheckMismatchIgnore] = None

    # A list of related issue tracker ids
    issue_ids: List[str] = []

    def __init__(self, **data):
        super().__init__(**data)
        if self.issue_ids is None:
            self.issue_ids = []

    @classmethod
    def create(cls, mismatch_type: SpotCheckMismatchType, observed_data, reference_data, notes: str = "") -> 'SpotCheckMismatch':
        return cls(
            mismatch_type=mismatch_type,
            observed_data=str(observed_data) if observed_data is not None else "",
            reference_data=str(reference_data) if reference_data is not None else "",
            notes=notes
        )

    @classmethod
    def create_simple(cls, mismatch_type: SpotCheckMismatchType, observed_data, reference_data) -> 'SpotCheckMismatch':
        return cls.create(mismatch_type, observed_data, reference_data, "")

    # --- Functional Getters / Setters ---

    @property
    def is_ignored(self) -> bool:
        return self.ignore_status is not None

    @property
    def get_tracked(self) -> SpotCheckMismatchTracked:
        return SpotCheckMismatchTracked.get_from_boolean(len(self.issue_ids) > 0)

    def add_issue_id(self, issue_id: str) -> None:
        if issue_id not in self.issue_ids:
            self.issue_ids.append(issue_id)

    def get_issue_ids(self) -> List[str]:
        return self.issue_ids.copy()

    def set_issue_ids(self, issue_ids: Collection[str]) -> None:
        self.issue_ids = list(issue_ids)

    # --- Overrides ---

    def __eq__(self, other) -> bool:
        if not isinstance(other, SpotCheckMismatch):
            return False
        return (self.mismatch_type == other.mismatch_type and
                self.state == other.state and
                self.reference_data == other.reference_data and
                self.observed_data == other.observed_data and
                self.notes == other.notes)

    def __hash__(self) -> int:
        return hash((self.mismatch_type, self.state, self.reference_data, self.observed_data, self.notes))

    # --- Basic Getters / Setters ---

    @property
    def get_mismatch_type(self) -> SpotCheckMismatchType:
        return self.mismatch_type

    @property
    def get_state(self) -> MismatchState:
        return self.state

    def set_state(self, state: MismatchState) -> None:
        self.state = state

    @property
    def get_reference_data(self) -> str:
        return self.reference_data

    @property
    def get_observed_data(self) -> str:
        return self.observed_data

    @property
    def get_notes(self) -> Optional[str]:
        return self.notes

    @property
    def get_ignore_status(self) -> Optional[SpotCheckMismatchIgnore]:
        return self.ignore_status

    def set_ignore_status(self, ignore_status: SpotCheckMismatchIgnore) -> None:
        self.ignore_status = ignore_status

    @property
    def get_mismatch_id(self) -> int:
        return self.mismatch_id

    def set_mismatch_id(self, mismatch_id: int) -> None:
        self.mismatch_id = mismatch_id