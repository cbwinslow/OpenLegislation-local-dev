"""Shared utilities for CLI-driven API ingestion with pagination and progress tracking.

This module standardizes incremental ingestion behaviour across multiple endpoints:
- Respects offset/limit style pagination
- Handles rate limiting with client-side throttling
- Supports concurrent page downloads with deterministic state persistence
- Avoids duplicate records using stable identifiers
- Emits structured progress updates for front-end monitoring

The implementation avoids reinventing existing ingestion primitives by reusing the
common configuration module and familiar retry semantics from tenacity.
"""

from __future__ import annotations

import json
import logging
import threading
import time
from concurrent.futures import FIRST_COMPLETED, ThreadPoolExecutor, wait
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

import requests
from requests import Session
from requests.adapters import HTTPAdapter
from tenacity import retry, stop_after_attempt, wait_exponential
from urllib3.util import Retry

from tools.config.settings import settings


LOGGER = logging.getLogger("api_ingestion_cli")
logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")


@dataclass
class APIIngestionConfig:
    """Configuration for a paginated API endpoint."""

    name: str
    base_url: str
    endpoint: str
    api_key: Optional[str] = None
    api_key_param: str = "api_key"
    api_key_header: Optional[str] = None
    page_size: int = 100
    offset_param: str = "offset"
    limit_param: str = "limit"
    records_key: str = "results"
    id_field: str = "id"
    extra_params: Dict[str, Any] = field(default_factory=dict)


@dataclass
class IngestionState:
    """Persistent state for resumable ingestion."""

    next_offset: int = 0
    ingested_ids: set[str] = field(default_factory=set)
    pages_completed: int = 0
    records_completed: int = 0

    def to_json(self) -> Dict[str, Any]:
        return {
            "next_offset": self.next_offset,
            "ingested_ids": sorted(self.ingested_ids),
            "pages_completed": self.pages_completed,
            "records_completed": self.records_completed,
        }

    @classmethod
    def from_path(cls, path: Path) -> "IngestionState":
        if not path.exists():
            return cls()
        data = json.loads(path.read_text())
        return cls(
            next_offset=data.get("next_offset", 0),
            ingested_ids=set(data.get("ingested_ids", [])),
            pages_completed=data.get("pages_completed", 0),
            records_completed=data.get("records_completed", 0),
        )


class PaginatedAPIIngestor:
    """Coordinator that drives paginated ingestion with concurrency and rate limiting."""

    def __init__(
        self,
        config: APIIngestionConfig,
        state_path: Path,
        output_path: Optional[Path] = None,
        rate_limit_per_second: float = 5.0,
        max_workers: int = 4,
    ) -> None:
        self.config = config
        self.state_path = state_path
        self.output_path = output_path
        self.rate_limit_per_second = rate_limit_per_second
        self.max_workers = max_workers
        self.state = IngestionState.from_path(state_path)
        self._rate_lock = threading.Lock()
        self._last_request_time = 0.0
        self.session = self._build_session()
        if output_path:
            output_path.parent.mkdir(parents=True, exist_ok=True)

    def _build_session(self) -> Session:
        session = requests.Session()
        retries = Retry(total=5, backoff_factor=0.5, status_forcelist=[429, 500, 502, 503, 504])
        adapter = HTTPAdapter(max_retries=retries)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        return session

    def _respect_rate_limit(self) -> None:
        if self.rate_limit_per_second <= 0:
            return
        with self._rate_lock:
            elapsed = time.monotonic() - self._last_request_time
            min_interval = 1 / self.rate_limit_per_second
            if elapsed < min_interval:
                time.sleep(min_interval - elapsed)
            self._last_request_time = time.monotonic()

    @retry(wait=wait_exponential(multiplier=1, min=1, max=30), stop=stop_after_attempt(5), reraise=True)
    def _fetch_page(self, offset: int) -> Dict[str, Any]:
        self._respect_rate_limit()
        params = {
            self.config.offset_param: offset,
            self.config.limit_param: self.config.page_size,
            **self.config.extra_params,
        }
        headers = {}
        if self.config.api_key:
            if self.config.api_key_header:
                headers[self.config.api_key_header] = self.config.api_key
            else:
                params[self.config.api_key_param] = self.config.api_key
        url = f"{self.config.base_url.rstrip('/')}/{self.config.endpoint.lstrip('/')}"
        response = self.session.get(url, params=params, headers=headers, timeout=settings.request_timeout)
        response.raise_for_status()
        return response.json()

    def _extract_records(self, payload: Dict[str, Any]) -> List[Dict[str, Any]]:
        data: Any = payload
        for key in self.config.records_key.split("."):
            data = data.get(key, []) if isinstance(data, dict) else []
        if not isinstance(data, list):
            return []
        return data

    def _write_records(self, records: Iterable[Dict[str, Any]]) -> None:
        if not self.output_path:
            return
        with self.output_path.open("a", encoding="utf-8") as fh:
            for record in records:
                fh.write(json.dumps(record))
                fh.write("\n")

    def _save_state(self) -> None:
        self.state_path.parent.mkdir(parents=True, exist_ok=True)
        self.state_path.write_text(json.dumps(self.state.to_json(), indent=2))

    def ingest(self, max_pages: Optional[int] = None) -> None:
        LOGGER.info("Starting %s ingestion", self.config.name)
        LOGGER.info(
            "Resuming from offset %s | pages=%s records=%s",
            self.state.next_offset,
            self.state.pages_completed,
            self.state.records_completed,
        )
        offset = self.state.next_offset
        pages_seen = 0
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = {}
            end_of_data = False
            while not end_of_data:
                while len(futures) < self.max_workers and (max_pages is None or pages_seen < max_pages):
                    futures[executor.submit(self._fetch_page, offset)] = offset
                    offset += self.config.page_size
                    pages_seen += 1
                if not futures:
                    break
                done, _ = wait(futures, return_when=FIRST_COMPLETED)
                for future in done:
                    page_offset = futures.pop(future)
                    try:
                        payload = future.result()
                        records = self._extract_records(payload)
                    except Exception as exc:  # noqa: BLE001
                        LOGGER.error("Failed to fetch offset %s: %s", page_offset, exc)
                        continue

                    if not records:
                        LOGGER.info("No records at offset %s; stopping.", page_offset)
                        end_of_data = True
                        continue

                    new_records = []
                    for record in records:
                        record_id = record.get(self.config.id_field)
                        if record_id is None:
                            continue
                        if record_id in self.state.ingested_ids:
                            continue
                        self.state.ingested_ids.add(str(record_id))
                        new_records.append(record)
                    self._write_records(new_records)
                    self.state.records_completed += len(new_records)
                    self.state.pages_completed += 1
                    self.state.next_offset = max(self.state.next_offset, page_offset + self.config.page_size)
                    self._save_state()
                    LOGGER.info(
                        "%s page @%s -> %s new / %s total | pages=%s",
                        self.config.name,
                        page_offset,
                        len(new_records),
                        self.state.records_completed,
                        self.state.pages_completed,
                    )

                    if max_pages is not None and self.state.pages_completed >= max_pages:
                        end_of_data = True
                        break
        LOGGER.info("Completed %s ingestion", self.config.name)
        LOGGER.info("Total pages=%s records=%s", self.state.pages_completed, self.state.records_completed)
