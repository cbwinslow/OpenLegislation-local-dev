from __future__ import annotations

from typing import List, Optional

from ..crud.agenda import get_agenda, list_agendas
from ..schemas.agenda import AgendaSchema
from ..session import session_scope


def fetch_agenda(agenda_no: int, year: int) -> Optional[AgendaSchema]:
    with session_scope() as session:
        agenda = get_agenda(session, agenda_no, year)
        if agenda is None:
            return None
        return AgendaSchema.from_orm(agenda)


def fetch_agendas(year: Optional[int] = None, limit: int = 100) -> List[AgendaSchema]:
    with session_scope() as session:
        agendas = list_agendas(session, year=year, limit=limit)
        return [AgendaSchema.from_orm(a) for a in agendas]
