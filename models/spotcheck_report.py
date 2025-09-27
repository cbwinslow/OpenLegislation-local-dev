from pydantic import BaseModel
from typing import Dict, TypeVar

from .spotcheck_report_id import SpotCheckReportId

ContentKey = TypeVar('ContentKey')

class SpotCheckReport(BaseModel):
    id: int
    report_id: SpotCheckReportId
    observation_map: Dict[str, str] = {}  # Map[ContentKey, SpotCheckObservation]
    notes: str

    def get_summary(self):
        # return SpotCheckReportSummary
        pass

    def get_open_mismatch_count(self, ignored: bool) -> int:
        # simplified
        return 0

    # Add other methods as needed