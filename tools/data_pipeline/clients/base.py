"""Common base client with retry-aware HTTP helpers."""
from __future__ import annotations

import logging
from typing import Any, Dict, Optional

import requests
from requests import Response
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

logger = logging.getLogger(__name__)


class ApiError(RuntimeError):
    """Raised when an HTTP API call fails."""


class BaseApiClient:
    """Base class providing HTTP helpers for API clients."""

    base_url: str
    timeout: int

    def __init__(
        self,
        base_url: str,
        *,
        timeout: int = 30,
        session: Optional[requests.Session] = None,
        default_headers: Optional[Dict[str, str]] = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.session = session or requests.Session()
        self.default_headers = default_headers or {}

    def _build_url(self, path: str) -> str:
        if path.startswith("http"):
            return path
        return f"{self.base_url}/{path.lstrip('/')}"

    @retry(
        retry=retry_if_exception_type((requests.RequestException, ApiError)),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        reraise=True,
    )
    def _request(
        self,
        method: str,
        path: str,
        *,
        params: Optional[Dict[str, Any]] = None,
        json: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> Response:
        url = self._build_url(path)
        logger.debug("Performing %s request to %s", method, url)
        merged_headers = {**self.default_headers, **(headers or {})}
        response = self.session.request(
            method,
            url,
            timeout=self.timeout,
            params=params,
            json=json,
            headers=merged_headers,
        )
        if not response.ok:
            logger.error("API request failed: %s %s -> %s", method, url, response.status_code)
            raise ApiError(f"{method} {url} returned {response.status_code}: {response.text}")
        return response

    def get(self, path: str, **kwargs: Any) -> Response:
        return self._request("GET", path, **kwargs)

    def post(self, path: str, **kwargs: Any) -> Response:
        return self._request("POST", path, **kwargs)

    def close(self) -> None:
        self.session.close()

    def __enter__(self) -> "BaseApiClient":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:  # type: ignore[override]
        self.close()

