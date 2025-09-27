from pydantic import BaseModel
from datetime import datetime
from typing import Optional

from .spotcheck_ref_type import SpotCheckRefType

class SpotCheckReferenceId(BaseModel):
    """A simple model that identifies reference data that is compared against when
    performing spot checks."""

    # Indicate the type of reference that is being used when performing QA.
    reference_type: SpotCheckRefType

    # The date (and time) from which the reference data is valid from.
    ref_active_date_time: Optional[datetime] = None

    def __str__(self) -> str:
        return f"referenceType = {self.reference_type}, refActiveDateTime = {self.ref_active_date_time}"

    @property
    def get_reference_type(self) -> SpotCheckRefType:
        return self.reference_type

    @property
    def get_ref_active_date_time(self) -> Optional[datetime]:
        return self.ref_active_date_time