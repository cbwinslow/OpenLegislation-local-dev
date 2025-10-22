"""Shared helpers for research analysis scripts."""

from __future__ import annotations

import json
import logging
import os
import pathlib
import sys
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, Iterable, Optional

import psycopg2
import psycopg2.extras

try:
    from tools import db_config
except ModuleNotFoundError:  # pragma: no cover - fallback when executed directly
    sys.path.append(str(pathlib.Path(__file__).resolve().parents[1]))
    from tools import db_config  # type: ignore


DEFAULT_REPORT_DIR = pathlib.Path("reports")
DEFAULT_REPORT_DIR.mkdir(exist_ok=True)


@dataclass
class DbSettings:
    """Connection settings for PostgreSQL."""

    host: str
    port: str
    database: str
    user: str
    password: str

    @classmethod
    def from_env(cls) -> "DbSettings":
        params = db_config.get_connection_params()
        return cls(
            host=params["host"],
            port=str(params["port"]),
            database=params["database"],
            user=params["user"],
            password=params["password"],
        )


def configure_logging(verbosity: int = 0) -> None:
    """Configure root logger for CLI scripts."""

    level = logging.WARNING
    if verbosity == 1:
        level = logging.INFO
    elif verbosity >= 2:
        level = logging.DEBUG

    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
    )


@contextmanager
def db_cursor(dict_cursor: bool = True):
    """Context manager yielding a database cursor."""

    conn_params = db_config.get_connection_params()
    logging.getLogger(__name__).debug("Connecting to database at %s", conn_params["host"])
    conn = psycopg2.connect(**conn_params)
    try:
        if dict_cursor:
            cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        else:
            cursor = conn.cursor()
        try:
            yield cursor
        finally:
            cursor.close()
    finally:
        conn.close()


def ensure_report_dir(path: Optional[str] = None) -> pathlib.Path:
    """Ensure the report directory exists and return a Path."""

    report_dir = pathlib.Path(path or DEFAULT_REPORT_DIR)
    report_dir.mkdir(parents=True, exist_ok=True)
    return report_dir


def timestamped_filename(prefix: str, suffix: str = "json", report_dir: Optional[str] = None) -> pathlib.Path:
    """Generate a timestamped filename inside the report directory."""

    ensure_report_dir(report_dir)
    ts = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    directory = pathlib.Path(report_dir or DEFAULT_REPORT_DIR)
    return directory / f"{prefix}_{ts}.{suffix}"


def dump_json(data: Any, output_path: pathlib.Path) -> pathlib.Path:
    """Write JSON data to disk with UTF-8 encoding."""

    with output_path.open("w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=2, ensure_ascii=False)
    return output_path


def chunk_iterable(iterable: Iterable[Any], size: int) -> Iterable[list[Any]]:
    """Yield successive chunks of size from iterable."""

    chunk: list[Any] = []
    for item in iterable:
        chunk.append(item)
        if len(chunk) >= size:
            yield chunk
            chunk = []
    if chunk:
        yield chunk


def safe_float(value: Optional[Any]) -> Optional[float]:
    """Convert a value to float safely."""

    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def load_json_lines(path: os.PathLike[str] | str) -> Iterable[Dict[str, Any]]:
    """Yield dictionaries from a JSON Lines file."""

    with open(path, "r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            yield json.loads(line)
