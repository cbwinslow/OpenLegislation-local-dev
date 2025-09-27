from __future__ import annotations

from typing import List, Optional

from ..crud.committee import get_committee, list_committees
from ..schemas.committee import CommitteeSchema
from ..session import session_scope


def fetch_committee(name: str, chamber: str) -> Optional[CommitteeSchema]:
    with session_scope() as session:
        committee = get_committee(session, name, chamber)
        if committee is None:
            return None
        return CommitteeSchema.from_orm(committee)


def fetch_committees(chamber: Optional[str] = None) -> List[CommitteeSchema]:
    with session_scope() as session:
        committees = list_committees(session, chamber=chamber)
        return [CommitteeSchema.from_orm(c) for c in committees]
