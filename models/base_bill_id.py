from typing import Optional

from .bill_id import BillId
from .bill_type import BillType
from .version import Version
from .session_year import SessionYear
from .chamber import Chamber

class BaseBillId(BillId):
    def __init__(self, print_no: Optional[str] = None, session: Optional[SessionYear] = None, **data):
        if print_no:
            print_no = self.normalize_print_no(print_no)
        if isinstance(session, int):
            session = SessionYear(year=session)
        super().__init__(print_no=print_no, session=session, version=self.DEFAULT_VERSION, **data)

    @classmethod
    def of(cls, bill_id: BillId) -> 'BaseBillId':
        return cls(print_no=bill_id.base_print_no, session=bill_id.session)

    def with_version(self, version: Version) -> BillId:
        return BillId(base_print_no=self.base_print_no, session=self.session, version=version)

    def get_version(self) -> Version:
        return self.DEFAULT_VERSION

    def get_base_print_no(self) -> str:
        return self.base_print_no

    def get_bill_type(self) -> BillType:
        return BillType(self.base_print_no[0])

    def get_chamber(self) -> Chamber:
        return self.get_bill_type().get_chamber()

    def compare_to(self, other: 'BaseBillId') -> int:
        return self.__lt__(other) - (1 if self < other else 0)  # Simplified

    def __lt__(self, other) -> bool:
        if self.session != other.session:
            return self.session < other.session
        return self.base_print_no < other.base_print_no
