"""Shared helper functions for federal ingestion pipelines."""

from __future__ import annotations

import json
import os
from datetime import datetime
from typing import Dict, Iterable, List, Optional

from tools.settings import settings

from .postgres import upsert_records


def write_json_records(records: Iterable[Dict], output_dir: str, prefix: str) -> List[str]:
    """Write normalized records to timestamped JSONL files."""

    os.makedirs(output_dir, exist_ok=True)
    timestamp = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    path = os.path.join(output_dir, f"{prefix}_{timestamp}.jsonl")
    written_paths: List[str] = []
    with open(path, "w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")
    written_paths.append(path)
    return written_paths


def upsert_to_postgres(
    table_name: str,
    records: Iterable[Dict],
    conflict_columns: List[str],
    db_config: Optional[Dict] = None,
    chunk_size: int = 100,
) -> int:
    """Upsert normalized records into PostgreSQL."""

    return upsert_records(
        table_name=table_name,
        records=list(records),
        conflict_columns=conflict_columns,
        db_config=db_config or settings.db_config,
        chunk_size=chunk_size,
    )
