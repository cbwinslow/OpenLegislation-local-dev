from .spotcheck_summary import SpotCheckSummary
from .spotcheck_report_id import SpotCheckReportId
from typing import Optional

class SpotCheckReportSummary(SpotCheckSummary):
    """Holds summary information for a particular spotcheck report"""

    # The Id of the described report
    report_id: Optional[SpotCheckReportId] = None

    # The report notes for the described report
    notes: Optional[str] = None

    # --- Getters / Setters ---

    @property
    def get_report_id(self) -> Optional[SpotCheckReportId]:
        return self.report_id

    @property
    def get_notes(self) -> Optional[str]:
        return self.notes