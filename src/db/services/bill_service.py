from __future__ import annotations

from typing import List, Optional

from ..crud.bill import get_bill, list_bills
from ..schemas.bill import BillSchema
from ..session import session_scope


def fetch_bill(bill_print_no: str, session_year: int) -> Optional[BillSchema]:
    with session_scope() as session:
        bill = get_bill(session, bill_print_no, session_year)
        if bill is None:
            return None
        return BillSchema.from_orm(bill)


def fetch_bills(limit: int = 50, offset: int = 0) -> List[BillSchema]:
    with session_scope() as session:
        bills = list_bills(session, limit=limit, offset=offset)
        return [BillSchema.from_orm(b) for b in bills]
