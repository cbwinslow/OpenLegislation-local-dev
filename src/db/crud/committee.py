from __future__ import annotations

from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from ..models.committee import Committee, CommitteeMember, CommitteeVersion


def get_committee(session: Session, name: str, chamber: str) -> Optional[Committee]:
    stmt = (
        select(Committee)
        .where(Committee.name == name, Committee.chamber == chamber)
        .options(
            selectinload(Committee.versions),
            selectinload(Committee.members)
            .selectinload(CommitteeMember.session_member)
            .selectinload("member")
            .selectinload("person"),
            selectinload(Committee.members).selectinload(CommitteeMember.version),
        )
    )
    return session.execute(stmt).scalar_one_or_none()


def list_committees(session: Session, chamber: Optional[str] = None) -> List[Committee]:
    stmt = select(Committee)
    if chamber:
        stmt = stmt.where(Committee.chamber == chamber)
    stmt = stmt.order_by(Committee.chamber, Committee.name)
    stmt = stmt.options(selectinload(Committee.versions))
    return list(session.execute(stmt).scalars().all())
