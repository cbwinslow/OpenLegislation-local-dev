"""Database helpers for federal ingestion pipelines."""
from __future__ import annotations

from collections import defaultdict
from contextlib import contextmanager
from typing import Dict, Iterable, Iterator, List, Sequence

from sqlalchemy import create_engine
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from tools.db_config import get_connection_string

from .config import get_settings
from .normalization import NormalizedRecord
from .schema import TABLE_MAP


def create_db_engine(override_url: str | None = None) -> Engine:
    """
    Create a SQLAlchemy Engine for the application's database connection.
    
    Parameters:
        override_url (str | None): Optional database URL to use instead of settings or the default connection string.
    
    Returns:
        Engine: A SQLAlchemy Engine configured with the future API for the resolved database URL.
    """
    settings = get_settings()
    url = override_url or settings.database_url or get_connection_string()
    return create_engine(url, future=True)


@contextmanager
def session_scope(engine: Engine) -> Iterator[Session]:
    """
    Provide a transactional SQLAlchemy session bound to the given engine, committing on successful exit, rolling back on exception, and always closing the session.
    
    Returns:
        session (Session): A SQLAlchemy session bound to the provided engine; committed on normal exit, rolled back if an exception occurs, and closed on exit.
    """
    SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def upsert_normalized_records(session: Session, records: Iterable[NormalizedRecord]) -> Dict[str, int]:
    """
    Upserts multiple normalized records into their corresponding database tables, grouping rows by their target table and applying per-table conflict resolution using each record's unique key columns.
    
    Parameters:
        records (Iterable[NormalizedRecord]): Iterable of records where each record must include:
            - "table": target table name (str)
            - "data": dict mapping column names to values for insertion
            - "unique_columns": sequence of column names that form the conflict key for upsert
    
    Returns:
        Dict[str, int]: Mapping from table name to the number of rows processed for that table.
    
    Raises:
        KeyError: If a record references a table name not present in TABLE_MAP.
    """
    grouped: Dict[str, List[Dict]] = defaultdict(list)
    unique_columns: Dict[str, Sequence[str]] = {}
    for record in records:
        table_name = record["table"]
        grouped[table_name].append(record["data"])
        unique_columns.setdefault(table_name, record["unique_columns"])

    results: Dict[str, int] = {}
    for table_name, rows in grouped.items():
        table = TABLE_MAP.get(table_name)
        if table is None:
            raise KeyError(f"Unknown table {table_name}")
        stmt = insert(table).values(rows)
        first = rows[0]
        uniques = unique_columns[table_name]
        update_cols = {
            column: getattr(stmt.excluded, column)
            for column in first.keys()
            if column not in uniques
        }
        on_conflict_stmt = stmt.on_conflict_do_update(index_elements=list(uniques), set_=update_cols)
        session.execute(on_conflict_stmt)
        results[table_name] = len(rows)
    return results


__all__ = ["create_db_engine", "session_scope", "upsert_normalized_records"]