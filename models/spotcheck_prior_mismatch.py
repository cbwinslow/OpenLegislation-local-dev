from .spotcheck_mismatch import SpotCheckMismatch
from .spotcheck_mismatch_type import SpotCheckMismatchType
from .spotcheck_report_id import SpotCheckReportId
from typing import Optional

class SpotCheckPriorMismatch(SpotCheckMismatch):
    """A SpotCheckPriorMismatch is a mismatch that has previously been recorded by some spot check
    persistence layer. It has a report id associated with it to provide some context."""

    # The id of the report where this mismatch was recorded.
    report_id: Optional[SpotCheckReportId] = None

    @classmethod
    def create(cls, mismatch_type: SpotCheckMismatchType, reference_data: str, observed_data: str, notes: str = "") -> 'SpotCheckPriorMismatch':
        return cls(
            mismatch_type=mismatch_type,
            reference_data=reference_data,
            observed_data=observed_data,
            notes=notes
        )

    # --- Basic Getters/Setters ---

    @property
    def get_report_id(self) -> Optional[SpotCheckReportId]:
        return self.report_id

    def set_report_id(self, report_id: SpotCheckReportId) -> None:
        self.report_id = report_id