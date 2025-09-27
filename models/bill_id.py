from pydantic import BaseModel
from typing import Optional
import re

from .version import Version
from .session_year import SessionYear
from .chamber import Chamber
from .bill_type import BillType

class BillId(BaseModel):
    PRINT_NUMBER_REGEX = r"([ASLREJKBC])(\d+)([A-Z]?)"
    PRINT_NUMBER_PATTERN = re.compile(PRINT_NUMBER_REGEX)
    BILL_ID_PATTERN = re.compile(rf"(?P<printNo>{PRINT_NUMBER_REGEX})-(?P<year>\d{{4}})")
    DEFAULT_VERSION = Version.ORIGINAL

    base_print_no: str
    session: SessionYear
    version: Version = DEFAULT_VERSION

    def __init__(self, print_no: Optional[str] = None, session: Optional[int] = None, version: Optional[str] = None,
                 base_print_no: Optional[str] = None, base_bill_id: Optional['BaseBillId'] = None, **data):
        if base_bill_id:
            base_print_no = base_bill_id.base_print_no
            session = base_bill_id.session
            version = version or str(self.DEFAULT_VERSION)
        elif print_no:
            print_no = self.normalize_print_no(print_no)
            # Strip out the version from the print no if it exists.
            parsed_version = self.DEFAULT_VERSION
            if print_no and print_no[-1].isalpha():
                parsed_version = Version.of(print_no[-1])
                print_no = print_no[:-1]
            self.check_base_print_has_no_version(print_no)
            base_print_no = print_no
            version = parsed_version
        if isinstance(session, int):
            session = SessionYear(year=session)
        if isinstance(version, str):
            version = Version.of(version)
        if session:
            self.check_session_year(session)
        super().__init__(base_print_no=base_print_no, session=session, version=version or self.DEFAULT_VERSION, **data)

    @classmethod
    def get_base_id(cls, bill_id: 'BillId') -> 'BaseBillId':
        from .base_bill_id import BaseBillId
        return BaseBillId(base_print_no=bill_id.base_print_no, session=bill_id.session)

    def get_print_no(self) -> str:
        return self.base_print_no + str(self.version)

    def get_bill_type(self) -> BillType:
        return BillType(self.base_print_no[0])

    def get_chamber(self) -> Chamber:
        return self.get_bill_type().get_chamber()

    def get_number(self) -> int:
        return int(re.sub(r'[^\d]', '', self.base_print_no))

    @staticmethod
    def is_base_version(version: Version) -> bool:
        return version is None or version == BillId.DEFAULT_VERSION

    def get_padded_bill_id_string(self) -> str:
        return self.get_padded_print_number() + "-" + str(self.session.year)

    def get_padded_print_number(self) -> str:
        matcher = self.PRINT_NUMBER_PATTERN.match(self.get_print_no())
        if matcher:
            return f"{matcher.group(1)}{int(matcher.group(2)):05d}{matcher.group(3)}"
        return ""

    @staticmethod
    def normalize_print_no(print_no: str) -> str:
        if not print_no or not print_no.strip():
            raise ValueError("PrintNo when constructing BillId cannot be null/empty.")
        # Remove all non-alphanumeric characters from the printNo.
        print_no = print_no.strip().upper()
        print_no = re.sub(r'[^A-Z0-9]', '', print_no)
        # Check that printNo matches the pattern
        if not BillId.PRINT_NUMBER_PATTERN.match(print_no):
            raise ValueError(f"PrintNo ({print_no}) does not match print no pattern ({BillId.PRINT_NUMBER_PATTERN.pattern()})")
        # Check that printNo starts with a valid bill type designator
        try:
            BillType(print_no[0])
        except ValueError as exc:
            raise ValueError(f"PrintNo ({print_no}) must begin with a valid letter designator.")
        # Trim leading 0's after the first character
        print_no = print_no[0] + print_no[1:].lstrip('0')
        return print_no

    @staticmethod
    def check_base_print_has_no_version(base_print_no: str):
        if base_print_no and base_print_no[-1].isalpha():
            raise ValueError(f"BasePrintNo cannot have a version appended to it. ({base_print_no})")

    @staticmethod
    def check_session_year(session: SessionYear):
        if session is None:
            raise ValueError("Supplied SessionYear cannot be null")

    def __str__(self) -> str:
        return f"{self.base_print_no}{str(self.version)}-{self.session.year}"

    def __eq__(self, other) -> bool:
        if other is None:
            return False
        if not self.equals_base(other):
            return False
        return self.version == other.version

    def __hash__(self) -> int:
        return 31 * self.hash_code_base() + hash(self.version)

    def equals_base(self, other) -> bool:
        if self is other:
            return True
        if not isinstance(other, BillId):
            return False
        return self.session == other.session and self.base_print_no == other.base_print_no

    def hash_code_base(self) -> int:
        return hash((self.base_print_no, self.session))

    def __lt__(self, other) -> bool:
        if self.session != other.session:
            return self.session < other.session
        if self.base_print_no != other.base_print_no:
            return self.base_print_no < other.base_print_no
        return self.version.value < other.version.value

    # Getters
    def get_base_print_no(self) -> str:
        return self.base_print_no

    def get_session(self) -> SessionYear:
        return self.session

    def get_version(self) -> Version:
        return self.version

    def with_version(self, version: Version) -> 'BillId':
        return BillId(base_print_no=self.base_print_no, session=self.session, version=version)
