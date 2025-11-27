"""Shared primitives for MCP ingestion servers."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, List, Optional, Tuple

import requests
import logging

logger = logging.getLogger(__name__)

@dataclass
class PaginationConfig:
    """Defines pagination semantics for a provider."""

    kind: str = "offset"  # "offset" or "page"
    page_param: str = "offset"
    page_size_param: str = "limit"
    start: int = 0
    page_size: int = 100
    results_path: Tuple[str, ...] = ("results",)
    total_path: Optional[Tuple[str, ...]] = None
    max_pages: Optional[int] = None

    def advance(self, current: int, last_batch_count: int) -> int:
        """Return the next offset/page based on the pagination strategy."""
        if self.kind == "page":
            return current + 1
        return current + last_batch_count


@dataclass
class EndpointConfig:
    """Endpoint metadata for bulk ingestion."""

    name: str
    path: str
    pagination: PaginationConfig
    description: str = ""
    extra_params: Dict[str, Any] = field(default_factory=dict)
    result_key_fallbacks: Tuple[str, ...] = ("results", "data", "items")


class MCPBulkIngestor:
    """Reusable client for paginated API ingestion.

    This client is designed for single-threaded, sequential API request
    processing. Rate limiting uses blocking time.sleep() calls. For
    concurrent request handling, consider an async implementation with
    asyncio.sleep() instead.
    """

    def __init__(
        self,
        base_url: str,
        api_key: Optional[str] = None,
        api_key_header: str = "X-Api-Key",
        default_rate_limit_per_sec: float = 3.0,
        session: Optional[requests.Session] = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.api_key_header = api_key_header
        self.rate_limit_per_sec = default_rate_limit_per_sec
        self.session = session or requests.Session()
        self._last_request_ts: Optional[float] = None

    def _throttle(self) -> None:
        """Simple sleep-based rate limiting.

        Note: This implementation uses time.sleep() which blocks the current
        thread. It is designed for single-threaded sequential processing of
        API requests. For concurrent request scenarios, consider using
        async/await patterns with asyncio.sleep() instead.
        """
        if self._last_request_ts is None:
            return
        elapsed = time.time() - self._last_request_ts
        min_interval = 1.0 / self.rate_limit_per_sec
        if elapsed < min_interval:
            time.sleep(min_interval - elapsed)

    def _headers(self) -> Dict[str, str]:
        headers: Dict[str, str] = {"Accept": "application/json"}
        if self.api_key:
            # Basic validation to prevent header injection
            api_key = self.api_key.strip()
            if not api_key:
                raise ValueError("API key must not be empty or whitespace")
            if '\n' in api_key or '\r' in api_key:
                raise ValueError("API key contains invalid characters (newline or carriage return)")
            headers[self.api_key_header] = api_key
        return headers

    def request(self, path: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Perform a GET request with throttling and JSON parsing."""
        self._throttle()
        url = f"{self.base_url}{path}"
        response = self.session.get(url, headers=self._headers(), params=params, timeout=60)
        self._last_request_ts = time.time()
        response.raise_for_status()
        return response.json()

    @staticmethod
    def _pluck(data: Dict[str, Any], path: Tuple[str, ...]) -> Optional[Any]:
        current: Any = data
        for key in path:
            if not isinstance(current, dict) or key not in current:
                return None
            current = current[key]
        return current

    def fetch_paginated(
        self,
        endpoint: EndpointConfig,
        start: Optional[int] = None,
        page_size: Optional[int] = None,
        max_pages: Optional[int] = None,
        extra_params: Optional[Dict[str, Any]] = None,
    ) -> Iterable[Dict[str, Any]]:
        """Iterate over pages while honoring pagination semantics and totals."""
        pagination = endpoint.pagination
        current = pagination.start if start is None else start
        size = pagination.page_size if page_size is None else page_size
        page_cap = max_pages if max_pages is not None else pagination.max_pages
        params = dict(endpoint.extra_params)
        if extra_params:
            params.update(extra_params)

        pages_seen = 0
        total_records: Optional[int] = None

        while True:
            params[pagination.page_param] = current
            params[pagination.page_size_param] = size
            payload = self.request(endpoint.path, params)

            results = None
            if pagination.results_path:
                results = self._pluck(payload, pagination.results_path)
            if results is None:
                if isinstance(payload, dict):
                    for key in endpoint.result_key_fallbacks:
                        candidate = payload.get(key)
                        if candidate is not None:
                            results = candidate
                            break
                else:
                    results = payload

            if results is None:
                results = []

            if pagination.total_path and total_records is None:
                total_candidate = self._pluck(payload, pagination.total_path)
                if isinstance(total_candidate, int):
                    total_records = total_candidate

            yield {
                "endpoint": endpoint.name,
                "params": dict(params),
                "offset": current,
                "page_size": size,
                "total": total_records,
                "results": results,
            }

            batch_count = len(results) if isinstance(results, list) else 0
            if batch_count == 0:
                break

            pages_seen += 1
            current = pagination.advance(current, batch_count)

            if page_cap is not None and pages_seen >= page_cap:
                break
            if total_records is not None and pagination.kind == "offset" and current >= total_records:
                break

    def ingest_endpoints(
        self,
        endpoints: List[EndpointConfig],
        start_offsets: Optional[Dict[str, int]] = None,
        page_size_overrides: Optional[Dict[str, int]] = None,
        max_pages: Optional[int] = None,
    ) -> Dict[str, int]:
        """Ingest multiple endpoints and return counts per endpoint."""
        start_map = start_offsets or {}
        size_map = page_size_overrides or {}
        counts: Dict[str, int] = {}

        for endpoint in endpoints:
            total = 0
            for page in self.fetch_paginated(
                endpoint,
                start=start_map.get(endpoint.name),
                page_size=size_map.get(endpoint.name),
                max_pages=max_pages,
            ):
                results = page.get("results", [])
                if isinstance(results, list):
                    total += len(results)
            counts[endpoint.name] = total
        return counts


__all__ = ["PaginationConfig", "EndpointConfig", "MCPBulkIngestor"]
