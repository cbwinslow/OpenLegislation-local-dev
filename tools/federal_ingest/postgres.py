"""Utility helpers for PostgreSQL upserts used by federal ingest pipelines."""

from __future__ import annotations

import re
from typing import Dict, Iterable, List

import psycopg2
from psycopg2 import sql
from psycopg2.extras import Json, execute_values


def _validate_identifier(identifier: str) -> None:
    """Validate SQL identifiers to prevent injection attacks.
    
    Raises:
        ValueError: If identifier contains invalid characters.
    """
    if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', identifier):
        raise ValueError(f"Invalid SQL identifier: {identifier}")


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

    # Validate all identifiers to prevent SQL injection
    _validate_identifier(table_name)
    for col in columns:
        _validate_identifier(col)
    for col in conflict_columns:
        _validate_identifier(col)

    update_columns = [col for col in columns if col not in conflict_columns]

    with psycopg2.connect(**db_config) as conn:
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

                # Build INSERT query using psycopg2.sql for safe identifier composition
                insert_query = sql.SQL("INSERT INTO {} ({}) VALUES %s").format(
                    sql.Identifier(table_name),
                    sql.SQL(', ').join(sql.Identifier(col) for col in columns)
                )
                
                if update_columns:
                    update_clause = sql.SQL(', ').join(
                        sql.SQL("{} = EXCLUDED.{}").format(sql.Identifier(col), sql.Identifier(col))
                        for col in update_columns
                    )
                    conflict_clause = sql.SQL(" ON CONFLICT ({}) DO UPDATE SET {}").format(
                        sql.SQL(', ').join(sql.Identifier(col) for col in conflict_columns),
                        update_clause
                    )
                else:
                    conflict_clause = sql.SQL(" ON CONFLICT ({}) DO NOTHING").format(
                        sql.SQL(', ').join(sql.Identifier(col) for col in conflict_columns)
                    )
                
                full_query = insert_query.as_string(conn) + conflict_clause.as_string(conn)
                execute_values(cursor, full_query, prepared_batch)
                total_upserted += len(batch)
        conn.commit()
    return total_upserted
