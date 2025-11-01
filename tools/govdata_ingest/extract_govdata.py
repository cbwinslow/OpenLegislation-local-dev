"""Streaming ingestion pipeline for catalog.data.gov datasets.

This module exposes two primary entry points:

* :func:`ingest_to_postgres` which accepts an iterator (or iterator of
  pre-batched iterables) of dataset records and persists them into
  PostgreSQL using periodic commits to bound memory usage.
* :func:`main` which orchestrates the extractor and ingestion flow for
  command-line usage.

The refactoring focuses on ensuring that ingestion works incrementally so
that large exports do not require materialising the full dataset in
memory. The code has intentionally been structured to make it easy to
inject alternative connection factories and insert behaviour for testing
purposes.
"""

from __future__ import annotations

import argparse
import json
import logging
import os
from collections.abc import Callable, Iterable, Iterator, Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any, Optional

import psycopg2
from psycopg2.extras import execute_values
import requests

from tools.db_config import get_connection_params

DEFAULT_BATCH_SIZE = 500
LOGGER = logging.getLogger(__name__)


def _looks_like_batch(item: Any) -> bool:
    """Return ``True`` when *item* appears to be an iterable of mappings."""

    if isinstance(item, Mapping):
        return False
    if isinstance(item, (str, bytes)):
        return False
    if not isinstance(item, Iterable):
        return False
    for element in item:
        if not isinstance(element, Mapping):
            return False
    return True


def _yield_batches(
    stream: Iterable[Mapping[str, Any]] | Iterable[Sequence[Mapping[str, Any]]],
    batch_size: int,
) -> Iterator[list[Mapping[str, Any]]]:
    """Normalise *stream* into batches of at most *batch_size* items."""

    buffer: list[Mapping[str, Any]] = []
    for item in stream:
        if _looks_like_batch(item):
            if buffer:
                yield buffer
                buffer = []

            chunk: list[Mapping[str, Any]] = []
            for record in item:  # type: ignore[union-attr]
                chunk.append(record)
                if len(chunk) >= batch_size:
                    yield chunk
                    chunk = []
            if chunk:
                yield chunk
        else:
            if not isinstance(item, Mapping):
                raise TypeError("ingestion stream must yield mapping objects")
            buffer.append(item)
            if len(buffer) >= batch_size:
                yield buffer
                buffer = []
    if buffer:
        yield buffer


_default_table_prepared = False


def _ensure_default_table(connection: psycopg2.extensions.connection) -> None:
    """Create the fallback storage table when using the default inserter."""

    global _default_table_prepared
    if _default_table_prepared:
        return
    with connection.cursor() as cursor:
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS master.govdata_raw (
                dataset_id TEXT PRIMARY KEY,
                payload JSONB NOT NULL,
                ingested_at TIMESTAMP DEFAULT NOW()
            )
            """
        )
    connection.commit()
    _default_table_prepared = True


def _default_insert_batch(
    connection: psycopg2.extensions.connection, batch: Sequence[Mapping[str, Any]]
) -> None:
    """Insert *batch* into ``master.govdata_raw`` using upserts."""

    if not batch:
        return

    _ensure_default_table(connection)

    rows = []
    for record in batch:
        dataset_id = record.get("id") or record.get("dataset_id")
        if not dataset_id:
            raise ValueError("GovData record missing 'id' or 'dataset_id'")
        rows.append((dataset_id, json.dumps(record, default=str)))

    with connection.cursor() as cursor:
        execute_values(
            cursor,
            """
            INSERT INTO master.govdata_raw (dataset_id, payload)
            VALUES %s
            ON CONFLICT (dataset_id)
            DO UPDATE SET payload = EXCLUDED.payload,
                          ingested_at = NOW()
            """,
            rows,
        )


def ingest_to_postgres(
    records: Iterable[Mapping[str, Any]] | Iterable[Sequence[Mapping[str, Any]]],
    connection_factory: Optional[Callable[[], psycopg2.extensions.connection]] = None,
    *,
    batch_size: int = DEFAULT_BATCH_SIZE,
    commit_every: Optional[int] = None,
    insert_batch: Optional[
        Callable[[psycopg2.extensions.connection, Sequence[Mapping[str, Any]]], None]
    ] = None,
    progress_callback: Optional[Callable[[int], None]] = None,
) -> int:
    """Stream *records* into PostgreSQL with periodic commits."""

    if batch_size <= 0:
        raise ValueError("batch_size must be positive")

    commit_threshold = commit_every or batch_size
    if commit_threshold <= 0:
        raise ValueError("commit_every must be positive when provided")

    factory = connection_factory or (lambda: psycopg2.connect(**get_connection_params()))
    inserter = insert_batch or _default_insert_batch

    total_ingested = 0
    pending_since_commit = 0
    connection = factory()

    try:
        for batch in _yield_batches(records, batch_size):
            inserter(connection, batch)
            total_ingested += len(batch)
            pending_since_commit += len(batch)

            if pending_since_commit >= commit_threshold:
                connection.commit()
                pending_since_commit = 0

            if progress_callback is not None:
                progress_callback(total_ingested)

        if pending_since_commit:
            connection.commit()

    finally:
        try:
            connection.close()
        except Exception:  # pragma: no cover - defensive cleanup
            LOGGER.exception("Failed to close PostgreSQL connection")

    return total_ingested


@dataclass
class GovDataExtractor:
    """Simple extractor for catalog.data.gov package metadata."""

    api_url: str = os.getenv(
        "GOVDATA_API_URL", "https://catalog.data.gov/api/3/action/package_search"
    )
    api_key: Optional[str] = os.getenv("GOVDATA_API_KEY")
    page_size: int = 100
    session: requests.Session = field(default_factory=requests.Session)

    def run(self, *, limit: Optional[int] = None) -> Iterator[Mapping[str, Any]]:
        """Yield dataset metadata records from catalog.data.gov."""

        headers = {}
        if self.api_key:
            headers["X-Api-Key"] = self.api_key

        collected = 0
        start = 0
        while True:
            params = {"rows": self.page_size, "start": start}
            response = self.session.get(self.api_url, params=params, headers=headers, timeout=30)
            response.raise_for_status()
            payload = response.json()
            result = payload.get("result", {})
            records = result.get("results", [])
            if not records:
                break

            for record in records:
                yield record
                collected += 1
                if limit is not None and collected >= limit:
                    return

            start += len(records)
            if limit is not None and collected >= limit:
                break


def parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    """Parse CLI arguments for the ingestion pipeline."""

    parser = argparse.ArgumentParser(description="Ingest catalog.data.gov metadata")
    parser.add_argument("--limit", type=int, default=None, help="Maximum records to fetch")
    parser.add_argument("--batch-size", type=int, default=DEFAULT_BATCH_SIZE)
    parser.add_argument(
        "--commit-every",
        type=int,
        default=None,
        help="Number of records between commits (defaults to batch size)",
    )
    parser.add_argument("--dry-run", action="store_true", help="Print batches without writing")
    parser.add_argument(
        "--log-level", default=os.getenv("LOG_LEVEL", "INFO"), help="Logging verbosity"
    )
    return parser.parse_args(argv)


def main(argv: Optional[Sequence[str]] = None) -> int:
    """Command-line entry point for streaming ingestion."""

    args = parse_args(argv)
    logging.basicConfig(level=getattr(logging, args.log_level.upper(), logging.INFO))

    extractor = GovDataExtractor()
    record_stream = extractor.run(limit=args.limit)

    if args.dry_run:
        total = 0
        for batch in _yield_batches(record_stream, args.batch_size):
            total += len(batch)
            LOGGER.info("Dry-run batch of %s records", len(batch))
        LOGGER.info("Dry-run completed with %s records", total)
        return total

    total = ingest_to_postgres(
        record_stream,
        batch_size=args.batch_size,
        commit_every=args.commit_every,
    )
    LOGGER.info("Ingested %s records", total)
    return total


if __name__ == "__main__":  # pragma: no cover - CLI entry point
    raise SystemExit(main())
