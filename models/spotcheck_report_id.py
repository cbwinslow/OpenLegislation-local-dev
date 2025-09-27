from pydantic import BaseModel
from datetime import datetime

class SpotCheckReportId(BaseModel):
    reference_type: str  # SpotCheckRefType
    reference_date_time: datetime
    report_date_time: datetime

    def get_reference_id(self):
        # return SpotCheckReferenceId
        pass

    def __str__(self):
        return f"SpotCheckReportId{{referenceType={self.reference_type}, referenceDateTime={self.reference_date_time}, reportDateTime={self.report_date_time}}}"

    def __lt__(self, other: 'SpotCheckReportId'):
        return self.report_date_time < other.report_date_time