from pydantic import BaseModel
from typing import Optional
import re

from .version import Version
from .session_year import SessionYear

class BillId(BaseModel):
    PRINT_NUMBER_REGEX = r"([ASLREJKBC])(\d+)([A-Z]?)"
    BILL_ID_PATTERN = re.compile(rf"(?P<printNo>{PRINT_NUMBER_REGEX})-(?P<year>\d{{4}})")
    DEFAULT_VERSION = Version.ORIGINAL

    base_print_no: str
    session: SessionYear
    version: Version = DEFAULT_VERSION

    def __init__(self, print_no: Optional[str] = None, session: Optional[SessionYear] = None, version: Optional[Version] = None, base_print_no: Optional[str] = None, **data):
        if print_no:
            print_no = self.normalize_print_no(print_no)
            parsed_version = Version.ORIGINAL
            if print_no and print_no[-1].isalpha():
                parsed_version = Version.of(print_no[-1])
                print_no = print_no[:-1]
            self.check_base_print_has_no_version(print_no)
            base_print_no = print_no
            version = parsed_version
        if session:
            self.check_session_year(session)
        super().__init__(base_print_no=base_print_no, session=session, version=version or self.DEFAULT_VERSION, **data)

    @staticmethod
    def normalize_print_no(print_no: str) -> str:
        return print_no.upper() if print_no else ""

    @staticmethod
    def check_base_print_has_no_version(print_no: str):
        if print_no and print_no[-1].isalpha():
            raise ValueError("Base print no should not have version")

    @staticmethod
    def check_session_year(session: SessionYear):
        pass

    def get_base_print_no(self) -> str:
        return self.base_print_no

    def get_session(self) -> SessionYear:
        return self.session

    def get_version(self) -> Version:
        return self.version

    def with_version(self, version: Version) -> 'BillId':
        return BillId(base_print_no=self.base_print_no, session=self.session, version=version)

    def __str__(self):
        return f"{self.base_print_no}{self.version.value}-{self.session.year}"

    def __eq__(self, other):
        return isinstance(other, BillId) and self.base_print_no == other.base_print_no and self.session == other.session and self.version == other.version

    def __hash__(self):
        return hash((self.base_print_no, self.session.year, self.version.value))