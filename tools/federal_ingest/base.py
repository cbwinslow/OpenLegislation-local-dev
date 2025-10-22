"""Shared utilities for the federal ingestion command line tools."""

from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable, Iterator, List, Mapping, Optional, Sequence

import psycopg2
from psycopg2.extras import execute_values
import requests
from requests import Session
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

LOGGER = logging.getLogger("federal_ingest")

ISO_FORMAT = "%Y-%m-%dT%H:%M:%S.%fZ"


@dataclass
class Resource:
    """Metadata about an optional downloadable asset."""

    url: str
    filename: Optional[str] = None
    media_type: Optional[str] = None

    def as_dict(self) -> Dict[str, Any]:
        data: Dict[str, Any] = {"url": self.url}
        if self.filename:
            data["filename"] = self.filename
        if self.media_type:
            data["media_type"] = self.media_type
        return data


@dataclass
class NormalizedRecord:
    """Normalised representation of a document fetched from a federal API."""

    source: str
    collection: str
    external_id: str
    data: Mapping[str, Any]
    title: Optional[str] = None
    summary: Optional[str] = None
    document_date: Optional[str] = None
    retrieved_at: datetime = field(default_factory=lambda: datetime.utcnow())
    resources: Sequence[Resource] = field(default_factory=list)

    def to_row(self) -> Dict[str, Any]:
        """Convert the record into a serialisable row for PostgreSQL."""

        return {
            "source": self.source,
            "collection": self.collection,
            "external_id": self.external_id,
            "title": self.title,
            "summary": self.summary,
            "document_date": self.document_date,
            "retrieved_at": self.retrieved_at.strftime(ISO_FORMAT),
            "data": json.dumps(self.data, sort_keys=True),
            "resources": json.dumps([resource.as_dict() for resource in self.resources]),
        }


class RecordExporter:
    """Persist records to disk as newline-delimited JSON documents."""

    def __init__(self, output_dir: Path) -> None:
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def write_records(self, records: Iterable[NormalizedRecord]) -> List[Path]:
        """Write each record to ``output_dir`` and return created file paths."""

        written: List[Path] = []
        for record in records:
            filename = f"{record.collection}_{record.external_id}.json"
            target = self.output_dir / filename
            payload = record.to_row()
            payload["data"] = json.loads(payload["data"])  # embed raw dict for disk export
            payload["resources"] = json.loads(payload["resources"])
            with target.open("w", encoding="utf-8") as handle:
                json.dump(payload, handle, ensure_ascii=False, indent=2, sort_keys=True)
            written.append(target)
            LOGGER.debug("Wrote %s", target)
        return written


class ResourceDownloader:
    """Download optional resources to a directory."""

    def __init__(self, session: Optional[Session] = None) -> None:
        self.session = session or build_retrying_session()

    def download(self, resources: Iterable[Resource], destination_dir: Path) -> List[Path]:
        destination_dir.mkdir(parents=True, exist_ok=True)
        downloaded: List[Path] = []
        for resource in resources:
            target = destination_dir / (resource.filename or Path(resource.url).name)
            LOGGER.info("Downloading %s", resource.url)
            response = self.session.get(resource.url, timeout=60)
            response.raise_for_status()
            with target.open("wb") as handle:
                handle.write(response.content)
            downloaded.append(target)
        return downloaded


class PostgresUpserter:
    """Insert or update records in PostgreSQL using ``ON CONFLICT``."""

    def __init__(self, dsn: Optional[str] = None, table: str = "federal_documents", conflict_fields: Optional[Sequence[str]] = None) -> None:
        self.dsn = dsn or os.getenv("FEDERAL_DB_URL") or os.getenv("DB_URL")
        if not self.dsn:
            raise ValueError("A database connection string is required")
        self.table = table
        self.conflict_fields = tuple(conflict_fields or ("source", "collection", "external_id"))

    def upsert(self, records: Iterable[NormalizedRecord]) -> int:
        """Upsert records into the configured table."""

        rows = [record.to_row() for record in records]
        if not rows:
            return 0

        columns = list(rows[0].keys())
        placeholders = "(" + ",".join(["%s"] * len(columns)) + ")"
        update_assignments = ", ".join([f"{column} = EXCLUDED.{column}" for column in columns if column not in self.conflict_fields])

        query = f"""
            INSERT INTO {self.table} ({', '.join(columns)})
            VALUES %s
            ON CONFLICT ({', '.join(self.conflict_fields)})
            DO UPDATE SET {update_assignments}
        """

        with psycopg2.connect(self.dsn) as connection:
            with connection.cursor() as cursor:
                execute_values(cursor, query, [tuple(row[column] for column in columns) for row in rows], template=placeholders)
        LOGGER.info("Upserted %s rows into %s", len(rows), self.table)
        return len(rows)


def build_retrying_session(backoff_factor: float = 0.5, retries: int = 5) -> Session:
    session = requests.Session()
    retry = Retry(
        total=retries,
        read=retries,
        connect=retries,
        backoff_factor=backoff_factor,
        status_forcelist=(429, 500, 502, 503, 504),
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return session


def safe_get(mapping: Mapping[str, Any], *keys: str) -> Optional[Any]:
    """Retrieve a nested value from a mapping using ``keys``."""

    current: Any = mapping
    for key in keys:
        if not isinstance(current, Mapping):
            return None
        current = current.get(key)
        if current is None:
            return None
    return current


def iter_records(generator: Iterable[NormalizedRecord]) -> Iterator[NormalizedRecord]:
    """Ensure generators are iterated only once when required by multiple sinks."""

    for record in generator:
        yield record

