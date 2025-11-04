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
    """
    Provide JSON-serializable representations for non-standard Python values.
    
    Parameters:
        value: The value to convert for JSON serialization (commonly datetime, date, or set).
    
    Returns:
        An ISO 8601 string for `datetime`/`date` objects, a `list` for `set` objects, or the original value if already serializable.
    
    Raises:
        TypeError: If `value` is not a `datetime`, `date`, or `set` and cannot be serialized by this helper.
    """
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, set):
        return list(value)
    raise TypeError(f"Object of type {type(value)!r} is not JSON serializable")


def export_records(export_path: Path, records: Iterable[NormalizedRecord]) -> int:
    """
    Write an iterable of NormalizedRecord objects to a JSON Lines file.
    
    Each input record is written as one JSON object per line with the keys:
    `table` (table name), `unique_columns` (list), and `data` (record payload).
    
    Parameters:
        export_path (Path): Destination file path to write the JSON Lines output. Parent directories will be created if missing.
        records (Iterable[NormalizedRecord]): Iterable of normalized records to export.
    
    Returns:
        int: Number of records written to the file.
    """

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
    """
    Download a resource from a URL into the destination directory and save it as a local file.
    
    Parameters:
        url (str): The HTTP(S) URL of the resource to download.
        destination_dir (Path): Directory where the file will be saved; created if it does not exist.
        session (requests.Session | None): Optional requests Session to use for the request. If omitted, a temporary session is created and closed by this function; a provided session will not be closed.
    
    Returns:
        Path: The path to the downloaded file on disk. If a file with the same name already exists in destination_dir, that path is returned without downloading.
    
    Raises:
        requests.HTTPError: If the HTTP response contains an error status.
    """

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