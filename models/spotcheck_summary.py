from pydantic import BaseModel
from typing import Dict, Tuple
from collections import defaultdict
import collections

from .spotcheck_mismatch_type import SpotCheckMismatchType
from .mismatch_state import MismatchState
from .spotcheck_mismatch_ignore import SpotCheckMismatchIgnore
from .spotcheck_mismatch_tracked import SpotCheckMismatchTracked
from .spotcheck_observation import SpotCheckObservation

class SpotCheckSummary(BaseModel):
    """Holds summary information for a particular spotcheck report"""

    # The number of occurrences for each mismatch type in the report, divided by mismatch status
    mismatch_counts: Dict[Tuple[SpotCheckMismatchType, MismatchState],
                         Dict[Tuple[SpotCheckMismatchIgnore, SpotCheckMismatchTracked], int]] = {}

    def __init__(self, **data):
        super().__init__(**data)
        if self.mismatch_counts is None:
            self.mismatch_counts = {}

    # --- Functional Getters / Setters ---

    def add_mismatch_type_count(self, mismatch_type: SpotCheckMismatchType, status: MismatchState,
                               ignore_status: SpotCheckMismatchIgnore, tracked: bool, count: int) -> None:
        """Record a type/status count"""
        key = (mismatch_type, status)
        if key not in self.mismatch_counts:
            self.mismatch_counts[key] = {}

        tracked_enum = SpotCheckMismatchTracked.get_from_boolean(tracked)
        sub_key = (ignore_status, tracked_enum)

        existing_value = self.mismatch_counts[key].get(sub_key, 0)
        self.mismatch_counts[key][sub_key] = existing_value + count

    def add_counts_from_observations(self, observations) -> None:
        """Add counts from a collection of observations"""
        for obs in observations:
            for mismatch in obs.mismatches.values():
                self.add_mismatch_type_count(
                    mismatch.mismatch_type,
                    mismatch.state,
                    mismatch.ignore_status or SpotCheckMismatchIgnore.NOT_IGNORED,
                    len(mismatch.issue_ids) > 0,
                    1
                )

    def get_mismatch_statuses(self) -> Dict[MismatchState, int]:
        """Get mismatch statuses with counts"""
        result = defaultdict(int)
        for (_, status), sub_dict in self.mismatch_counts.items():
            result[status] += sum(sub_dict.values())
        return dict(result)

    # --- Getters ---

    @property
    def get_mismatch_counts(self) -> Dict[Tuple[SpotCheckMismatchType, MismatchState],
                                        Dict[Tuple[SpotCheckMismatchIgnore, SpotCheckMismatchTracked], int]]:
        return self.mismatch_counts