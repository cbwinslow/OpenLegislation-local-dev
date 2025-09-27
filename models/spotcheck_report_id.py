from pydantic import BaseModel
from datetime import datetime
from typing import Optional

from .spotcheck_ref_type import SpotCheckRefType
from .spotcheck_reference_id import SpotCheckReferenceId

class SpotCheckReportId(BaseModel):
    # The reference type used to validate data against.
    reference_type: Optional[SpotCheckRefType] = None

    # The date that the reference was registered
    reference_date_time: Optional[datetime] = None

    # When this report was generated.
    report_date_time: datetime

    def __init__(self, **data):
        super().__init__(**data)

    @classmethod
    def create(cls, reference_type: SpotCheckRefType, report_date_time: datetime, reference_date_time: Optional[datetime] = None) -> 'SpotCheckReportId':
        return cls(
            reference_type=reference_type,
            report_date_time=report_date_time,
            reference_date_time=reference_date_time
        )

    # --- Functional Getters ---

    def get_reference_id(self) -> Optional[SpotCheckReferenceId]:
        if self.reference_type is None:
            return None
        return SpotCheckReferenceId(
            reference_type=self.reference_type,
            ref_active_date_time=self.reference_date_time
        )

    # --- Overrides ---

    def __str__(self):
        return f"SpotCheckReportId{{referenceType={self.reference_type}, referenceDateTime={self.reference_date_time}, reportDateTime={self.report_date_time}}}"

    def __lt__(self, other: 'SpotCheckReportId'):
        return self.report_date_time < other.report_date_time

    # --- Basic Getters ---

    @property
    def get_reference_type(self) -> Optional[SpotCheckRefType]:
        return self.reference_type

    @property
    def get_reference_date_time(self) -> Optional[datetime]:
        return self.reference_date_time

    @property
    def get_report_date_time(self) -> datetime:
        return self.report_date_time