from enum import Enum
from typing import Set
import json

from .spotcheck_ref_type import SpotCheckRefType

class SpotCheckMismatchType(Enum):
    """Enumeration of the different bill fields that we can check for data quality issues."""

    # --- General ---
    ALL = ("All", frozenset(SpotCheckRefType))
    REFERENCE_DATA_MISSING = ("Ref. Missing", frozenset(SpotCheckRefType))
    OBSERVE_DATA_MISSING = ("Source Missing", frozenset(SpotCheckRefType))

    # --- Bill data mismatches ---
    BILL_ACTION = ("Action", frozenset([SpotCheckRefType.LBDC_DAYBREAK, SpotCheckRefType.SENATE_SITE_BILLS, SpotCheckRefType.OPENLEG_BILL]))
    BILL_ACTIVE_AMENDMENT = ("Active Amendment", frozenset([SpotCheckRefType.LBDC_DAYBREAK, SpotCheckRefType.LBDC_SCRAPED_BILL, SpotCheckRefType.SENATE_SITE_BILLS, SpotCheckRefType.OPENLEG_BILL]))
    BILL_AMENDMENT_PUBLISH = ("Published Status", frozenset([SpotCheckRefType.LBDC_DAYBREAK, SpotCheckRefType.SENATE_SITE_BILLS]))
    BILL_COSPONSOR = ("Co Sponsor", frozenset([SpotCheckRefType.LBDC_DAYBREAK, SpotCheckRefType.SENATE_SITE_BILLS, SpotCheckRefType.OPENLEG_BILL]))
    BILL_FULLTEXT_PAGE_COUNT = ("Page Count", frozenset([SpotCheckRefType.LBDC_DAYBREAK]))
    BILL_TEXT_LINE_OFFSET = ("Text Line Offset", frozenset([SpotCheckRefType.LBDC_SCRAPED_BILL, SpotCheckRefType.SENATE_SITE_BILLS]))
    BILL_TEXT_CONTENT = ("Text Content", frozenset([SpotCheckRefType.LBDC_SCRAPED_BILL, SpotCheckRefType.SENATE_SITE_BILLS]))
    BILL_TEXT_RESO_HEADER = ("Reso. Header", frozenset([SpotCheckRefType.LBDC_SCRAPED_BILL]))
    BILL_LAW_CODE_SUMMARY = ("Law/Summary", frozenset([SpotCheckRefType.LBDC_DAYBREAK]))
    BILL_LAW_SECTION = ("Law Section", frozenset([SpotCheckRefType.LBDC_DAYBREAK, SpotCheckRefType.SENATE_SITE_BILLS, SpotCheckRefType.OPENLEG_BILL]))
    BILL_MEMO = ("Memo", frozenset([SpotCheckRefType.LBDC_SCRAPED_BILL, SpotCheckRefType.SENATE_SITE_BILLS]))
    BILL_MULTISPONSOR = ("Multi Sponsor", frozenset([SpotCheckRefType.LBDC_DAYBREAK, SpotCheckRefType.SENATE_SITE_BILLS, SpotCheckRefType.OPENLEG_BILL]))
    BILL_SESSION_YEAR = ("Session Year", frozenset([SpotCheckRefType.LBDC_DAYBREAK, SpotCheckRefType.OPENLEG_BILL]))
    BILL_SPONSOR = ("Sponsor", frozenset([SpotCheckRefType.LBDC_DAYBREAK, SpotCheckRefType.SENATE_SITE_BILLS, SpotCheckRefType.OPENLEG_BILL]))
    BILL_ADDITIONAL_SPONSOR = ("Bill Additional Sponsor", frozenset([SpotCheckRefType.OPENLEG_BILL]))
    BILL_TITLE = ("Title", frozenset([SpotCheckRefType.LBDC_DAYBREAK, SpotCheckRefType.SENATE_SITE_BILLS, SpotCheckRefType.OPENLEG_BILL]))

    BILL_BASE_PRINT_NO = ("Base Print No", frozenset([SpotCheckRefType.SENATE_SITE_BILLS]))
    BILL_CHAMBER = ("Chamber", frozenset([SpotCheckRefType.SENATE_SITE_BILLS]))
    BILL_SAME_AS = ("Same As", frozenset([SpotCheckRefType.SENATE_SITE_BILLS]))
    BILL_PREVIOUS_VERSIONS = ("Prev. Versions", frozenset([SpotCheckRefType.SENATE_SITE_BILLS]))
    BILL_IS_AMENDED = ("Is Amended", frozenset([SpotCheckRefType.SENATE_SITE_BILLS]))
    BILL_HAS_SAME_AS = ("Has Same As", frozenset([SpotCheckRefType.SENATE_SITE_BILLS]))
    BILL_PUBLISH_DATE = ("Publish Date", frozenset([SpotCheckRefType.SENATE_SITE_BILLS]))
    BILL_MILESTONES = ("Milestones", frozenset([SpotCheckRefType.SENATE_SITE_BILLS]))
    BILL_LAST_STATUS = ("Last Status", frozenset([SpotCheckRefType.SENATE_SITE_BILLS, SpotCheckRefType.OPENLEG_BILL]))
    BILL_LAST_STATUS_COMM = ("Last Status Committee", frozenset([SpotCheckRefType.SENATE_SITE_BILLS]))
    BILL_LAST_STATUS_DATE = ("Last Status Date", frozenset([SpotCheckRefType.SENATE_SITE_BILLS]))
    BILL_SUMMARY = ("Summary", frozenset([SpotCheckRefType.SENATE_SITE_BILLS, SpotCheckRefType.OPENLEG_BILL]))
    BILL_LAW_CODE = ("Law Code", frozenset([SpotCheckRefType.SENATE_SITE_BILLS, SpotCheckRefType.OPENLEG_BILL]))
    BILL_TEXT = ("Full Text", frozenset([SpotCheckRefType.SENATE_SITE_BILLS, SpotCheckRefType.OPENLEG_BILL]))
    BILL_VOTE_INFO = ("Bill Vote Info", frozenset([SpotCheckRefType.SENATE_SITE_BILLS, SpotCheckRefType.OPENLEG_BILL]))
    BILL_VOTE_ROLL = ("Bill Vote Roll", frozenset([SpotCheckRefType.SENATE_SITE_BILLS, SpotCheckRefType.OPENLEG_BILL]))
    BILL_SCRAPE_VOTE = ("Bill Scrape Vote", frozenset([SpotCheckRefType.LBDC_SCRAPED_BILL]))
    BILL_HTML_TEXT = ("HTML Full Text", frozenset([SpotCheckRefType.LBDC_SCRAPED_BILL]))

    BILL_APPROVAL_MESSAGE = ("Bill Approve Message", frozenset([SpotCheckRefType.OPENLEG_BILL]))
    BILL_COMMITTEE_AGENDAS = ("Bill Committee Agendas", frozenset([SpotCheckRefType.OPENLEG_BILL]))
    BILL_PAST_COMMITTEES = ("Bill Past Committees", frozenset([SpotCheckRefType.OPENLEG_BILL]))
    BILL_CALENDARS = ("Bill Calendars", frozenset([SpotCheckRefType.OPENLEG_BILL]))

    # --- Agenda mismatches ---
    AGENDA_ID = ("Agenda Id", frozenset([SpotCheckRefType.SENATE_SITE_AGENDA]))

    # --- Agenda Committee Meeting info mismatches ---
    AGENDA_BILL_LISTING = ("Bill List", frozenset([SpotCheckRefType.LBDC_AGENDA_ALERT, SpotCheckRefType.SENATE_SITE_AGENDA, SpotCheckRefType.OPENLEG_AGENDA]))
    AGENDA_CHAIR = ("Chair", frozenset([SpotCheckRefType.LBDC_AGENDA_ALERT, SpotCheckRefType.OPENLEG_AGENDA]))
    AGENDA_MEETING_TIME = ("Meeting Time", frozenset([SpotCheckRefType.LBDC_AGENDA_ALERT, SpotCheckRefType.SENATE_SITE_AGENDA, SpotCheckRefType.OPENLEG_AGENDA]))
    AGENDA_LOCATION = ("Location", frozenset([SpotCheckRefType.LBDC_AGENDA_ALERT, SpotCheckRefType.SENATE_SITE_AGENDA, SpotCheckRefType.OPENLEG_AGENDA]))
    AGENDA_NOTES = ("Notes", frozenset([SpotCheckRefType.LBDC_AGENDA_ALERT, SpotCheckRefType.SENATE_SITE_AGENDA, SpotCheckRefType.OPENLEG_AGENDA]))
    AGENDA_BILLS = ("Bills", frozenset([SpotCheckRefType.LBDC_AGENDA_ALERT, SpotCheckRefType.SENATE_SITE_AGENDA, SpotCheckRefType.OPENLEG_AGENDA]))
    AGENDA_MODIFIED_DATE_TIME = ("Modified Date Time", frozenset([SpotCheckRefType.OPENLEG_AGENDA]))
    AGENDA_HAS_VOTES = ("Has Votes", frozenset([SpotCheckRefType.OPENLEG_AGENDA]))
    AGENDA_ATTENDANCE_LIST = ("Agenda Attendance List", frozenset([SpotCheckRefType.OPENLEG_AGENDA]))
    AGENDA_VOTES_LIST = ("Agenda Votes List", frozenset([SpotCheckRefType.OPENLEG_AGENDA]))

    # --- Calendar mismatches ---
    CALENDAR_ID = ("Calendar Id", frozenset([SpotCheckRefType.SENATE_SITE_CALENDAR]))

    # --- Floor / Supplemental mismatches ---
    SUPPLEMENTAL_ENTRY = ("Supplemental Entry", frozenset([SpotCheckRefType.LBDC_CALENDAR_ALERT, SpotCheckRefType.SENATE_SITE_CALENDAR, SpotCheckRefType.OPENLEG_CAL]))
    FLOOR_ENTRY = ("Floor Entry", frozenset([SpotCheckRefType.SENATE_SITE_CALENDAR, SpotCheckRefType.OPENLEG_CAL]))

    FLOOR_CAL_DATE = ("Floor Calendar Date", frozenset([SpotCheckRefType.LBDC_CALENDAR_ALERT, SpotCheckRefType.OPENLEG_CAL]))
    FLOOR_CAL_YEAR = ("Floor Calendar Year", frozenset([SpotCheckRefType.OPENLEG_CAL]))
    FLOOR_RELEASE_DATE_TIME = ("Floor Release Date Time", frozenset([SpotCheckRefType.OPENLEG_CAL]))
    FLOOR_SECTION_TYPE = ("Floor Section", frozenset([SpotCheckRefType.LBDC_CALENDAR_ALERT, SpotCheckRefType.OPENLEG_CAL]))

    # --- Active list mismatches ---
    ACTIVE_LIST_CAL_DATE = ("Active List Calendar Date", frozenset([SpotCheckRefType.LBDC_CALENDAR_ALERT, SpotCheckRefType.OPENLEG_CAL]))
    ACTIVE_LIST_ENTRY = ("Active List Entry", frozenset([SpotCheckRefType.LBDC_CALENDAR_ALERT, SpotCheckRefType.SENATE_SITE_CALENDAR, SpotCheckRefType.OPENLEG_CAL]))

    # --- Active List data mismatches ---
    ACTIVE_LIST_RELEASE_DATE_TIME = ("Active List Release Time", frozenset([SpotCheckRefType.LBDC_CALENDAR_ALERT, SpotCheckRefType.OPENLEG_CAL]))
    ACTIVE_LIST_NOTES = ("Active List Notes", frozenset([SpotCheckRefType.OPENLEG_CAL]))

    # --- Law Mismatches ---
    LAW_TREE = ("Law Tree", frozenset([SpotCheckRefType.SENATE_SITE_LAW]))
    LAW_IDS = ("Law Ids", frozenset([SpotCheckRefType.SENATE_SITE_LAW]))
    LAW_TREE_NODE_NOT_FOUND = ("Tree Node Not Found", frozenset([SpotCheckRefType.SENATE_SITE_LAW]))

    # Tree Node Mismatches
    LAW_DOC_NEXT_SIBLING_URL = ("Next Sibling Url", frozenset([SpotCheckRefType.SENATE_SITE_LAW]))
    LAW_DOC_PREV_SIBLING_URL = ("Prev Sibling Url", frozenset([SpotCheckRefType.SENATE_SITE_LAW]))
    LAW_DOC_PARENT_LOC_IDS = ("Parent Location Ids", frozenset([SpotCheckRefType.SENATE_SITE_LAW]))
    LAW_DOC_PARENT_ID = ("Parent Id", frozenset([SpotCheckRefType.SENATE_SITE_LAW]))
    LAW_DOC_REPEALED = ("Is Repealed", frozenset([SpotCheckRefType.SENATE_SITE_LAW]))
    LAW_DOC_REPEALED_DATE = ("Repealed Date", frozenset([SpotCheckRefType.SENATE_SITE_LAW]))
    LAW_DOC_SEQUENCE_NO = ("Sequence No.", frozenset([SpotCheckRefType.SENATE_SITE_LAW]))
    LAW_DOC_FROM_SECTION = ("From Section", frozenset([SpotCheckRefType.SENATE_SITE_LAW]))
    LAW_DOC_TO_SECTION = ("To Section", frozenset([SpotCheckRefType.SENATE_SITE_LAW]))

    # Document Mismatches
    LAW_DOC_TITLE = ("Title", frozenset([SpotCheckRefType.SENATE_SITE_LAW]))
    LAW_DOC_ACTIVE_DATE = ("Active Date", frozenset([SpotCheckRefType.SENATE_SITE_LAW]))
    LAW_DOC_DOC_LEVEL_ID = ("Doc Level Id", frozenset([SpotCheckRefType.SENATE_SITE_LAW]))
    LAW_DOC_DOC_TYPE = ("Doc Type", frozenset([SpotCheckRefType.SENATE_SITE_LAW]))
    LAW_DOC_LAW_ID = ("Law Id", frozenset([SpotCheckRefType.SENATE_SITE_LAW]))
    LAW_DOC_LAW_NAME = ("Law Name", frozenset([SpotCheckRefType.SENATE_SITE_LAW]))
    LAW_DOC_LAW_TYPE = ("Law Type", frozenset([SpotCheckRefType.SENATE_SITE_LAW]))
    LAW_DOC_LOCATION_ID = ("Location Id", frozenset([SpotCheckRefType.SENATE_SITE_LAW]))
    LAW_DOC_TEXT = ("Text", frozenset([SpotCheckRefType.SENATE_SITE_LAW]))

    def __init__(self, display_name: str, ref_types: frozenset):
        self.display_name = display_name
        self.ref_types = ref_types

    @property
    def get_display_name(self) -> str:
        return self.display_name

    @property
    def get_ref_types(self) -> frozenset:
        return self.ref_types

    def possible_for_content_type(self, content_type) -> bool:
        """Check if this mismatch type is possible for the given content type."""
        # This would need SpotCheckContentType implementation
        # For now, return True
        return True

    @staticmethod
    def get_spot_check_mismatch_by_display_name(display_name: str):
        for mismatch_type in SpotCheckMismatchType:
            if mismatch_type.display_name == display_name:
                return mismatch_type
        return None

    @staticmethod
    def get_name(mismatch_type):
        if mismatch_type is None:
            return "%"
        return mismatch_type.name

    @staticmethod
    def get_json_map():
        return json.dumps({mismatch_type.name: mismatch_type.display_name for mismatch_type in SpotCheckMismatchType})

    @staticmethod
    def get_json_reftype_mismatch_map():
        # This would need a more complex mapping
        # For now, return empty dict
        return json.dumps({})