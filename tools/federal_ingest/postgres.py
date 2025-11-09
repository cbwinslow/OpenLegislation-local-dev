"""Utility helpers for PostgreSQL upserts used by federal ingest pipelines."""

from __future__ import annotations

import re
from typing import Dict, Iterable, List

import psycopg2
from psycopg2.extras import Json, execute_values
from psycopg2.extensions import quote_ident


def _validate_identifier(name: str) -> None:
    """Validate that an identifier (table or column name) is safe to use in SQL.
    
    Raises ValueError if the identifier contains suspicious characters.
    """
    if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', name):
        raise ValueError(f"Invalid SQL identifier: {name}")


def _quote_identifier(conn, name: str) -> str:
    """Safely quote a SQL identifier (table or column name).
    
    Args:
        conn: psycopg2 connection object
        name: identifier to quote
        
    Returns:
        Properly quoted identifier safe for SQL interpolation
    """
    _validate_identifier(name)
    # Use psycopg2's quote_ident for proper SQL identifier quoting
    return quote_ident(name, conn)


def upsert_records(
    table_name: str,
    records: Iterable[Dict],
    conflict_columns: List[str],
    db_config: Dict,
    chunk_size: int = 100,
) -> int:
    """Perform batched UPSERT operations for the provided records."""

    records_list = list(records)
    if not records_list:
        return 0

    columns = sorted({key for record in records_list for key in record.keys()})
    if not columns:
        return 0

    update_columns = [col for col in columns if col not in conflict_columns]

    with psycopg2.connect(**db_config) as conn:
        # Validate and quote all identifiers
        quoted_table = _quote_identifier(conn, table_name)
        quoted_columns = [_quote_identifier(conn, col) for col in columns]
        quoted_conflict_columns = [_quote_identifier(conn, col) for col in conflict_columns]
        
        # Build UPDATE clause with quoted identifiers
        update_clause = ", ".join(
            f"{_quote_identifier(conn, col)} = EXCLUDED.{_quote_identifier(conn, col)}"
            for col in update_columns
        )
        
        with conn.cursor() as cursor:
            total_upserted = 0
            for start in range(0, len(records_list), chunk_size):
                batch = records_list[start : start + chunk_size]
                prepared_batch = []
                for record in batch:
                    row = []
                    for column in columns:
                        value = record.get(column)
                        if isinstance(value, (dict, list)):
                            row.append(Json(value))
                        else:
                            row.append(value)
                    prepared_batch.append(tuple(row))

                # Use quoted identifiers to prevent SQL injection
                insert_query = f"INSERT INTO {quoted_table} ({', '.join(quoted_columns)}) VALUES %s"
                if update_clause:
                    insert_query += f" ON CONFLICT ({', '.join(quoted_conflict_columns)}) DO UPDATE SET {update_clause}"
                else:
                    insert_query += f" ON CONFLICT ({', '.join(quoted_conflict_columns)}) DO NOTHING"

                execute_values(cursor, insert_query, prepared_batch)
                total_upserted += len(batch)
        conn.commit()
    return total_upserted
