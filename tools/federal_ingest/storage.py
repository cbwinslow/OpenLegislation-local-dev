"""Storage helpers for exporting ingestion results and downloading resources."""
from __future__ import annotations

import json
import logging
from datetime import date, datetime
from pathlib import Path
from typing import Iterable

import requests

from .normalization import NormalizedRecord

logger = logging.getLogger(__name__)


def _json_default(value):  # type: ignore[override]
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, set):
        return list(value)
    raise TypeError(f"Object of type {type(value)!r} is not JSON serializable")


def export_records(export_path: Path, records: Iterable[NormalizedRecord]) -> int:
    """Write normalized records to a JSON Lines file."""

    export_path.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    with export_path.open("w", encoding="utf-8") as handle:
        for record in records:
            payload = {
                "table": record["table"],
                "unique_columns": list(record["unique_columns"]),
                "data": record["data"],
            }
            handle.write(json.dumps(payload, default=_json_default) + "\n")
            count += 1
    logger.info("Wrote %s records to %s", count, export_path)
    return count


def download_resource(url: str, destination_dir: Path, *, session: requests.Session | None = None) -> Path:
    """Download a resource to the destination directory, returning the file path."""

    destination_dir.mkdir(parents=True, exist_ok=True)
    local_name = url.split("/")[-1]
    target_path = destination_dir / local_name
    if target_path.exists():
        logger.info("Skipping existing download %s", target_path)
        return target_path
    sess = session or requests.Session()
    logger.info("Downloading %s -> %s", url, target_path)
    with sess.get(url, stream=True, timeout=60) as response:
        response.raise_for_status()
        with target_path.open("wb") as fh:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    fh.write(chunk)
    if session is None:
        sess.close()
    return target_path


__all__ = ["export_records", "download_resource"]
