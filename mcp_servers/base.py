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
        """
        Compute the next pagination index (page number or offset) according to the configured strategy.
        
        Args:
            current (int): Current page index or offset.
            last_batch_count (int): Number of items returned in the last page; used when the pagination kind is "offset".
        
        Returns:
            int: Next page index if `kind` is "page" (current + 1), otherwise next offset computed as current + last_batch_count.
        
        Notes:
            - `last_batch_count` should be ≥ 0 for meaningful offset advancement.
        """
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
    """Reusable client for paginated API ingestion."""

    def __init__(
        self,
        base_url: str,
        api_key: Optional[str] = None,
        api_key_header: str = "X-Api-Key",
        default_rate_limit_per_sec: float = 3.0,
        session: Optional[requests.Session] = None,
    ) -> None:
        """
        Create a bulk ingestor client configured for a target API.
        
        Args:
            base_url (str): Base URL for API requests. Trailing slash will be removed.
            api_key (Optional[str]): API key to include in requests, if provided.
            api_key_header (str): Header name to send the API key under.
            default_rate_limit_per_sec (float): Default allowed request rate in requests per second.
            session (Optional[requests.Session]): Requests session to use; if None, a new Session is created.
        
        Returns:
            None
        
        Side effects:
            - May create and store a new requests.Session when `session` is None.
            - Stores the provided configuration on the instance and initializes internal rate-limiting state.
        """
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.api_key_header = api_key_header
        self.rate_limit_per_sec = default_rate_limit_per_sec
        self.session = session or requests.Session()
        self._last_request_ts: Optional[float] = None

    def _throttle(self) -> None:
        """
        Enforces the configured rate limit by sleeping until the minimum interval since the last request has passed.
        
        If no previous request timestamp is recorded, this is a no-op. When invoked and the elapsed time since the last request is less than 1 / rate_limit_per_sec, the method blocks the calling thread for the remaining interval.
        
        Side effects:
            Blocks (sleeps) the current thread when rate limiting is applied.
        """
        if self._last_request_ts is None:
            return
        elapsed = time.time() - self._last_request_ts
        min_interval = 1.0 / self.rate_limit_per_sec
        if elapsed < min_interval:
            time.sleep(min_interval - elapsed)

    def _headers(self) -> Dict[str, str]:
        """
        Build HTTP request headers including JSON Accept and an optional API key header.
        
        Returns:
            dict: Mapping of header names to values. Always contains "Accept": "application/json".
                If the instance has an API key configured, includes a header with the name given by
                the instance's `api_key_header` and the API key as its value.
        """
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
        """
        Send a throttled GET request to the given path and return the parsed JSON response.
        
        Args:
            path (str): API path to append to the instance's base URL.
            params (Dict[str, Any]): Query parameters to include in the request.
        
        Returns:
            Dict[str, Any]: The response body parsed from JSON.
        
        Raises:
            requests.HTTPError: If the response has a non-2xx status (raised by response.raise_for_status()).
            ValueError: If the response body cannot be decoded as JSON.
        
        Side effects:
            - Observes the instance rate limit by sleeping as needed before the request.
            - Updates the instance's last-request timestamp.
            - Uses a 60-second request timeout.
        """
        self._throttle()
        url = f"{self.base_url}{path}"
        response = self.session.get(url, headers=self._headers(), params=params, timeout=60)
        self._last_request_ts = time.time()
        response.raise_for_status()
        return response.json()

    @staticmethod
    def _pluck(data: Dict[str, Any], path: Tuple[str, ...]) -> Optional[Any]:
        """
        Traverse a nested mapping and return the value found at the given key path.
        
        Args:
            data (Dict[str, Any]): Root mapping to traverse.
            path (Tuple[str, ...]): Sequence of keys describing the nested path to follow.
        
        Returns:
            Optional[Any]: The value at the end of the path, or `None` if any key is missing or an intermediate value is not a mapping.
        
        Notes:
            An empty `path` returns `data` unchanged.
        """
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
        """
        Iterate pages from an endpoint according to its pagination rules and yield per-page results and metadata.
        
        Args:
            endpoint (EndpointConfig): Endpoint metadata including path and PaginationConfig.
            start (Optional[int]): Override starting offset or page index; if omitted uses endpoint.pagination.start.
            page_size (Optional[int]): Override page size; if omitted uses endpoint.pagination.page_size.
            max_pages (Optional[int]): Maximum number of pages to fetch; if omitted uses endpoint.pagination.max_pages.
            extra_params (Optional[Dict[str, Any]]): Additional query parameters merged with endpoint.extra_params.
        
        Yields:
            Dict[str, Any]: A dictionary for each fetched page with keys:
                - "endpoint": endpoint.name
                - "params": the query parameters used for the request
                - "offset": current offset or page index used for the request
                - "page_size": page size used for the request
                - "total": total number of records when available (int or None)
                - "results": the extracted results for the page (list or other JSON value)
        
        Raises:
            requests.HTTPError: If an HTTP request returns a non-success status (propagated from self.request).
        
        Side effects:
            Performs network requests and enforces the client's rate limiting and header behaviour.
        """
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
        """
        Ingest multiple endpoints and return the total number of items retrieved for each endpoint.
        
        Args:
            endpoints (List[EndpointConfig]): Endpoint configurations to ingest.
            start_offsets (Optional[Dict[str, int]]): Per-endpoint starting offset or page index to override the endpoint pagination start.
            page_size_overrides (Optional[Dict[str, int]]): Per-endpoint page size overrides.
            max_pages (Optional[int]): Optional cap on pages to fetch per endpoint.
        
        Returns:
            Dict[str, int]: Mapping from endpoint name to the total count of items ingested for that endpoint. The total is computed by summing the lengths of `results` lists from pages; non-list `results` values are ignored.
        
        Raises:
            Any exception raised by underlying fetching operations (for example network or HTTP errors) is propagated.
        """
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