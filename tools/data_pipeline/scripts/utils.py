"""Utility helpers for ingestion scripts."""
from __future__ import annotations

from itertools import islice
from typing import Iterable, Iterator, List, Sequence

from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.sql.schema import Table
from sqlalchemy.orm import Session


def chunked(iterable: Iterable, size: int) -> Iterator[List]:
    iterator = iter(iterable)
    while True:
        chunk = list(islice(iterator, size))
        if not chunk:
            break
        yield chunk


def upsert_records(session: Session, table: Table, records: Sequence[dict], conflict_columns: Sequence[str]) -> None:
    if not records:
        return
    stmt = insert(table).values(records)
    first_record = records[0]
    update_cols = {
        column: getattr(stmt.excluded, column)
        for column in first_record.keys()
        if column not in conflict_columns
    }
    on_conflict_stmt = stmt.on_conflict_do_update(index_elements=conflict_columns, set_=update_cols)
    session.execute(on_conflict_stmt)

