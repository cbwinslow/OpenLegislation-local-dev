"""Shared CLI helpers for federal ingestion scripts."""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Iterable, List, Optional

from ..db import create_db_engine, session_scope, upsert_normalized_records
from ..normalization import NormalizedRecord
from ..storage import export_records

logger = logging.getLogger(__name__)


def configure_logging(verbose: bool) -> None:
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(level=level, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")


def handle_records(
    records: Iterable[NormalizedRecord],
    *,
    export_path: Optional[Path] = None,
    upsert: bool = False,
    database_url: Optional[str] = None,
) -> List[NormalizedRecord]:
    """Materialize records and optionally export or persist them."""

    record_list = list(records)
    logger.debug("Materialized %s records", len(record_list))
    if export_path:
        export_records(export_path, record_list)
    if upsert and record_list:
        engine = create_db_engine(database_url)
        with session_scope(engine) as session:
            upsert_results = upsert_normalized_records(session, record_list)
            for table_name, count in upsert_results.items():
                logger.info("Upserted %s rows into %s", count, table_name)
    return record_list


__all__ = ["configure_logging", "handle_records"]
