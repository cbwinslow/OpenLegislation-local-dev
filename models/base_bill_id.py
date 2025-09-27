from pydantic import BaseModel
from typing import Optional

from .bill_id import BillId
from .version import Version
from .session_year import SessionYear

class BaseBillId(BillId):
    base_print_no: str
    session: SessionYear
    version: Version = Version.ORIGINAL  # Always ORIGINAL

    def __init__(self, print_no: str, session: SessionYear, **data):
        super().__init__(print_no=print_no, session=session, version=Version.ORIGINAL, **data)

    @property
    def get_version(self) -> Version:
        return Version.ORIGINAL

    def with_version(self, version: Version) -> BillId:
        return BillId(base_print_no=self.base_print_no, session=self.session, version=version)

    @classmethod
    def of(cls, bill_id: BillId) -> 'BaseBillId':
        return cls(print_no=bill_id.base_print_no, session=bill_id.session)