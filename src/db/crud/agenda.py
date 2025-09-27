from __future__ import annotations

from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from ..models.agenda import (
    Agenda,
    AgendaInfoAddendum,
    AgendaInfoCommittee,
    AgendaInfoCommitteeItem,
    AgendaVoteAddendum,
    AgendaVoteCommittee,
    AgendaVoteCommitteeAttend,
    AgendaVoteCommitteeVote,
)


def get_agenda(session: Session, agenda_no: int, year: int) -> Optional[Agenda]:
    stmt = (
        select(Agenda)
        .where(Agenda.agenda_no == agenda_no, Agenda.year == year)
        .options(
            selectinload(Agenda.info_addenda)
            .selectinload(AgendaInfoAddendum.committees)
            .selectinload(AgendaInfoCommittee.items),
            selectinload(Agenda.vote_addenda)
            .selectinload(AgendaVoteAddendum.committees)
            .selectinload(AgendaVoteCommittee.attendance)
            .selectinload(AgendaVoteCommitteeAttend.session_member)
            .selectinload("member")
            .selectinload("person"),
            selectinload(Agenda.vote_addenda)
            .selectinload(AgendaVoteAddendum.committees)
            .selectinload(AgendaVoteCommittee.votes),
        )
    )
    return session.execute(stmt).scalar_one_or_none()


def list_agendas(session: Session, year: Optional[int] = None, limit: int = 100) -> List[Agenda]:
    stmt = select(Agenda)
    if year is not None:
        stmt = stmt.where(Agenda.year == year)
    stmt = stmt.order_by(Agenda.year.desc(), Agenda.agenda_no.desc()).limit(limit)
    stmt = stmt.options(selectinload(Agenda.info_addenda), selectinload(Agenda.vote_addenda))
    return list(session.execute(stmt).scalars().all())
