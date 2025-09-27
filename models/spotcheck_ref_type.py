from enum import Enum
from typing import List
import json

from .spotcheck_data_source import SpotCheckDataSource
from .spotcheck_content_type import SpotCheckContentType

class SpotCheckRefType(Enum):
    """Enumeration of the types of sources that can provide data for QA purposes."""

    LBDC_DAYBREAK = ("daybreak", "Daybreak", SpotCheckDataSource.LBDC, SpotCheckContentType.BILL)
    LBDC_SCRAPED_BILL = ("scraped-bill", "Scraped Bill", SpotCheckDataSource.LBDC, SpotCheckContentType.BILL)
    LBDC_CALENDAR_ALERT = ("floor-alert", "LBDC Calendar Alert", SpotCheckDataSource.LBDC, SpotCheckContentType.CALENDAR)
    LBDC_AGENDA_ALERT = ("agenda-alert", "Agenda Alert", SpotCheckDataSource.LBDC, SpotCheckContentType.AGENDA_WEEK)

    SENATE_SITE_BILLS = ("senate-site-bills", "Nysenate.gov Bill", SpotCheckDataSource.NYSENATE, SpotCheckContentType.BILL_AMENDMENT)
    SENATE_SITE_CALENDAR = ("senate-site-calendar", "Nysenate.gov Calendar", SpotCheckDataSource.NYSENATE, SpotCheckContentType.CALENDAR)
    SENATE_SITE_AGENDA = ("senate-site-agenda", "Nysenate.gov Agenda", SpotCheckDataSource.NYSENATE, SpotCheckContentType.AGENDA)
    SENATE_SITE_LAW = ("senate-site-law", "NYSenate.gov Law", SpotCheckDataSource.NYSENATE, SpotCheckContentType.LAW)

    OPENLEG_BILL = ("openleg-bill", "Openleg Bill", SpotCheckDataSource.OPENLEG, SpotCheckContentType.BILL)
    OPENLEG_CAL = ("openleg-cal", "Openleg Cal", SpotCheckDataSource.OPENLEG, SpotCheckContentType.CALENDAR)
    OPENLEG_AGENDA = ("openleg-agenda", "Openleg Agenda", SpotCheckDataSource.OPENLEG, SpotCheckContentType.AGENDA)

    def __init__(self, ref_name: str, display_name: str, data_source: SpotCheckDataSource, content_type: SpotCheckContentType):
        self.ref_name = ref_name
        self.display_name = display_name
        self.data_source = data_source
        self.content_type = content_type

    def checked_mismatch_types(self):
        """Get a set of SpotCheckMismatchTypes that are checked in this Reference Type."""
        from .spotcheck_mismatch_type import SpotCheckMismatchType
        return {mismatch_type for mismatch_type in SpotCheckMismatchType
                if self in mismatch_type.ref_types}

    @property
    def get_ref_name(self) -> str:
        return self.ref_name

    @property
    def get_display_name(self) -> str:
        return self.display_name

    @property
    def get_data_source(self) -> SpotCheckDataSource:
        return self.data_source

    @property
    def get_content_type(self) -> SpotCheckContentType:
        return self.content_type

    @staticmethod
    def get_by_ref_name(ref_name: str):
        for ref_type in SpotCheckRefType:
            if ref_type.ref_name == ref_name:
                return ref_type
        return None

    @staticmethod
    def get(data_source: SpotCheckDataSource, content_type: SpotCheckContentType) -> List['SpotCheckRefType']:
        return [ref_type for ref_type in SpotCheckRefType
                if ref_type.data_source == data_source and ref_type.content_type == content_type]

    @staticmethod
    def get_ref_json_map():
        return json.dumps({ref_type.name: ref_type.ref_name for ref_type in SpotCheckRefType})

    @staticmethod
    def get_display_json_map():
        return json.dumps({ref_type.name: ref_type.display_name for ref_type in SpotCheckRefType})

    @staticmethod
    def get_ref_content_type_json_map():
        return json.dumps({ref_type.name: ref_type.content_type.name for ref_type in SpotCheckRefType})