"""Common HTTP client utilities for federal data ingest pipelines."""

from __future__ import annotations

import json
import logging
import time
from dataclasses import dataclass
from typing import Any, Dict, Iterable, Optional

import requests

from tools.settings import settings


LOGGER = logging.getLogger(__name__)


@dataclass
class RequestConfig:
    """Runtime configuration for API requests."""

    api_key: Optional[str]
    base_url: str
    rate_limit_delay: float = settings.rate_limit_delay
    timeout: int = settings.request_timeout
    headers: Optional[Dict[str, str]] = None


class HTTPError(RuntimeError):
    """Raised when a remote API returns a non-success response."""

    def __init__(self, status_code: int, message: str, payload: Optional[dict] = None):
        super().__init__(f"HTTP {status_code}: {message}")
        self.status_code = status_code
        self.payload = payload or {}


class BaseAPIClient:
    """Shared functionality for interacting with remote HTTP APIs."""

    def __init__(self, config: RequestConfig):
        self.config = config

    def _build_headers(self) -> Dict[str, str]:
        headers = {"Accept": "application/json"}
        if self.config.headers:
            headers.update(self.config.headers)
        if self.config.api_key:
            headers["X-API-Key"] = self.config.api_key
        return headers

    def _request(self, method: str, url: str, params: Optional[Dict[str, Any]] = None) -> dict:
        headers = self._build_headers()
        LOGGER.debug("Requesting %s %s", method, url)
        response = requests.request(
            method,
            url,
            params=params,
            headers=headers,
            timeout=self.config.timeout,
        )
        if response.status_code >= 400:
            message = response.text
            try:
                payload = response.json()
                message = json.dumps(payload)
            except ValueError:
                payload = None
            raise HTTPError(response.status_code, message, payload)
        time.sleep(self.config.rate_limit_delay)
        return response.json()

    def _resolve_url(self, *parts: Iterable[str]) -> str:
        cleaned = [str(part).strip("/") for part in parts if part is not None]
        return "/".join([self.config.base_url.rstrip("/")] + cleaned)
