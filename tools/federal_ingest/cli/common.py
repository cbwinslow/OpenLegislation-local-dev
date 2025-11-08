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
    """
    Configure the global logging level and output format for CLI tools.
    
    Sets the root logger level to DEBUG when `verbose` is True, otherwise to INFO, and configures the basic log format to include timestamp, level, logger name, and message.
    
    Parameters:
        verbose (bool): If True, enable verbose (DEBUG) logging; otherwise use INFO.
    """
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(level=level, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")


def handle_records(
    records: Iterable[NormalizedRecord],
    *,
    export_path: Optional[Path] = None,
    upsert: bool = False,
    database_url: Optional[str] = None,
) -> List[NormalizedRecord]:
    """
    Materializes an iterable of NormalizedRecord objects and optionally exports them to storage and/or upserts them into a database.
    
    Parameters:
        records (Iterable[NormalizedRecord]): Iterable of normalized records to materialize and process.
        export_path (Optional[Path]): If provided, exports the materialized records to this path using the storage exporter.
        upsert (bool): If True, upserts the materialized records into the database.
        database_url (Optional[str]): Database connection URL used to create the engine when `upsert` is True; if None, a default engine is created.
    
    Returns:
        List[NormalizedRecord]: The materialized list of input records.
    """

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