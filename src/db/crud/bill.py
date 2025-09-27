from __future__ import annotations

from typing import Iterable, List, Optional

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from ..models.bill import (
    Bill,
    BillAmendment,
    BillAmendmentCosponsor,
    BillAmendmentMultiSponsor,
    BillSponsor,
    BillSponsorAdditional,
)


def get_bill(session: Session, bill_print_no: str, session_year: int) -> Optional[Bill]:
    stmt = (
        select(Bill)
        .where(Bill.bill_print_no == bill_print_no, Bill.bill_session_year == session_year)
        .options(
            selectinload(Bill.amendments)
            .selectinload(BillAmendment.actions),
            selectinload(Bill.amendments)
            .selectinload(BillAmendment.publish_statuses),
            selectinload(Bill.amendments)
            .selectinload(BillAmendment.cosponsors)
            .selectinload(BillAmendmentCosponsor.session_member)
            .selectinload("member")
            .selectinload("person"),
            selectinload(Bill.amendments)
            .selectinload(BillAmendment.multi_sponsors)
            .selectinload(BillAmendmentMultiSponsor.session_member)
            .selectinload("member")
            .selectinload("person"),
            selectinload(Bill.sponsors)
            .selectinload(BillSponsor.session_member)
            .selectinload("member")
            .selectinload("person"),
            selectinload(Bill.additional_sponsors)
            .selectinload(BillSponsorAdditional.session_member)
            .selectinload("member")
            .selectinload("person"),
        )
    )
    return session.execute(stmt).scalar_one_or_none()


def list_bills(session: Session, limit: int = 100, offset: int = 0) -> List[Bill]:
    stmt = (
        select(Bill)
        .order_by(Bill.bill_session_year.desc(), Bill.bill_print_no)
        .limit(limit)
        .offset(offset)
        .options(
            selectinload(Bill.sponsors)
            .selectinload(BillSponsor.session_member)
            .selectinload("member")
            .selectinload("person"),
            selectinload(Bill.additional_sponsors)
            .selectinload(BillSponsorAdditional.session_member)
            .selectinload("member")
            .selectinload("person"),
        )
    )
    return list(session.execute(stmt).scalars().all())


def save_bill(session: Session, bill: Bill) -> Bill:
    session.add(bill)
    return bill


def save_all(session: Session, bills: Iterable[Bill]) -> None:
    session.add_all(list(bills))
