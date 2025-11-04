"""Streaming extraction utilities for data.gov datasets."""
from __future__ import annotations

import argparse
import json
import logging
import os
from dataclasses import dataclass
from typing import Callable, Iterable, Iterator, Mapping, MutableMapping, Optional, Sequence

import requests

try:
    import psycopg2  # type: ignore
except ImportError:  # pragma: no cover - psycopg2 is optional for tests
    psycopg2 = None  # type: ignore

LOGGER = logging.getLogger(__name__)

DEFAULT_BASE_URL = "https://catalog.data.gov/api/3/action/package_search"
DEFAULT_PAGE_SIZE = 100
DEFAULT_COMMIT_INTERVAL = 500

Dataset = Mapping[str, object]


@dataclass
class GovDataExtractor:
    """Stream datasets from the data.gov search API."""

    api_key: Optional[str] = None
    query: Optional[str] = None
    page_size: int = DEFAULT_PAGE_SIZE
    max_pages: Optional[int] = None
    base_url: str = DEFAULT_BASE_URL
    session: Optional[requests.Session] = None

    def _build_params(self, start: int) -> MutableMapping[str, object]:
        params: MutableMapping[str, object] = {
            "rows": self.page_size,
            "start": start,
        }
        if self.query:
            params["q"] = self.query
        if self.api_key:
            params["api_key"] = self.api_key
        return params

    def run(self) -> Iterator[Dataset]:
        """Yield dataset metadata one item at a time."""

        session = self.session or requests.Session()
        start = 0
        pages_emitted = 0

        while True:
            if self.max_pages is not None and pages_emitted >= self.max_pages:
                break

            response = session.get(self.base_url, params=self._build_params(start), timeout=30)
            response.raise_for_status()
            payload = response.json()
            result = payload.get("result", {})
            datasets: Sequence[Dataset] = result.get("results", [])  # type: ignore[assignment]
            if not datasets:
                break

            for dataset in datasets:
                yield dataset

            count = len(datasets)
            start += count
            pages_emitted += 1

            if count < self.page_size:
                break


def get_db_connection_from_env() -> "psycopg2.extensions.connection":
    """Create a psycopg2 connection using environment variables."""

    if psycopg2 is None:  # pragma: no cover - runtime guard
        raise RuntimeError("psycopg2 is required for database ingestion")

    return psycopg2.connect(
        host=os.getenv("DB_HOST", "localhost"),
        port=os.getenv("DB_PORT", "5432"),
        dbname=os.getenv("DB_NAME", "openlegdb"),
        user=os.getenv("DB_USER", "postgres"),
        password=os.getenv("DB_PASS", "defaultpass"),
    )


UPSERT_QUERY = """
    INSERT INTO govdata_dataset (dataset_id, payload)
    VALUES (%s, %s)
    ON CONFLICT (dataset_id) DO UPDATE
    SET payload = EXCLUDED.payload;
"""


class IngestionError(RuntimeError):
    """Raised when ingestion fails due to invalid payload."""


def ingest_to_postgres(
    datasets: Iterable[Dataset],
    connection,
    *,
    commit_every: int = DEFAULT_COMMIT_INTERVAL,
    upsert_query: str = UPSERT_QUERY,
) -> int:
    """Stream dataset records into Postgres with periodic commits."""

    if commit_every <= 0:
        raise ValueError("commit_every must be positive")

    cursor = connection.cursor()
    processed = 0
    pending = 0

    try:
        for dataset in datasets:
            dataset_id = dataset.get("id") if isinstance(dataset, Mapping) else None
            if not dataset_id:
                raise IngestionError("dataset missing required 'id' field")

            cursor.execute(upsert_query, (dataset_id, json.dumps(dataset)))
            processed += 1
            pending += 1

            if pending >= commit_every:
                connection.commit()
                pending = 0

        if pending > 0 or processed == 0:
            connection.commit()
    finally:
        cursor.close()

    return processed


def _parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Ingest data.gov datasets into Postgres.")
    parser.add_argument("--query", help="Optional search query.", default=None)
    parser.add_argument("--page-size", type=int, default=DEFAULT_PAGE_SIZE, help="Datasets per API request.")
    parser.add_argument("--max-pages", type=int, default=None, help="Limit the number of API pages to fetch.")
    parser.add_argument("--commit-every", type=int, default=DEFAULT_COMMIT_INTERVAL, help="Commit interval for ingestion.")
    parser.add_argument("--api-key", default=os.getenv("DATA_GOV_API_KEY"), help="data.gov API key.")
    return parser.parse_args(argv)


def main(
    argv: Optional[Sequence[str]] = None,
    *,
    extractor_factory: Optional[Callable[[argparse.Namespace], GovDataExtractor]] = None,
    connection_factory: Optional[Callable[[argparse.Namespace], object]] = None,
    ingest_fn: Callable[..., int] = ingest_to_postgres,
) -> int:
    """CLI entry point for streaming dataset ingestion."""

    args = _parse_args(argv)

    extractor_builder = extractor_factory or (lambda a: GovDataExtractor(
        api_key=a.api_key,
        query=a.query,
        page_size=a.page_size,
        max_pages=a.max_pages,
    ))
    connection_builder = connection_factory or (lambda a: get_db_connection_from_env())

    extractor = extractor_builder(args)
    connection = connection_builder(args)

    try:
        return ingest_fn(extractor.run(), connection, commit_every=args.commit_every)
    finally:
        try:
            connection.close()
        except Exception:  # pragma: no cover - defensive
            LOGGER.exception("Failed to close database connection")


if __name__ == "__main__":  # pragma: no cover - CLI guard
    logging.basicConfig(level=logging.INFO)
    main()
