"""Utility helpers for PostgreSQL upserts used by federal ingest pipelines."""

from __future__ import annotations

from typing import Dict, Iterable, List

import psycopg2
from psycopg2.extras import Json, execute_values


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
    update_clause = ", ".join(f"{col} = EXCLUDED.{col}" for col in update_columns)

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

                insert_query = f"INSERT INTO {table_name} ({', '.join(columns)}) VALUES %s"
                if update_clause:
                    insert_query += f" ON CONFLICT ({', '.join(conflict_columns)}) DO UPDATE SET {update_clause}"
                else:
                    insert_query += f" ON CONFLICT ({', '.join(conflict_columns)}) DO NOTHING"

                execute_values(cursor, insert_query, prepared_batch)
                total_upserted += len(batch)
        conn.commit()
    return total_upserted
