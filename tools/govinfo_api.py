"""Lightweight GovInfo API client.

Wraps the public REST endpoints and handles pagination, retries, and error handling.
Usage:
    client = GovInfoAPIClient(api_key="demo")
    for package in client.iter_packages("BILLS", congress=118, start_date="2023-01-01"):
        print(package["packageId"])
"""
from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from typing import Dict, Iterable, Iterator, List, Optional

import requests

logger = logging.getLogger(__name__)


DEFAULT_BASE_URL = "https://api.govinfo.gov"
DEFAULT_BULK_URL = "https://www.govinfo.gov/bulkdata"
DEFAULT_PAGE_SIZE = 100
MAX_RETRIES = 5
BACKOFF_SECONDS = 2.0


class GovInfoError(RuntimeError):
    """Raised when the GovInfo API returns an error response."""


@dataclass
class GovInfoPackage:
    package_id: str
    collection: str
    title: str
    date_issued: Optional[str]
    congress: Optional[int]
    doc_class: Optional[str]
    summary_url: Optional[str]
    download_url: Optional[str]

    @classmethod
    def from_api(cls, payload: Dict[str, object]) -> "GovInfoPackage":
        return cls(
            package_id=str(payload.get("packageId")),
            collection=str(payload.get("collectionCode")),
            title=str(payload.get("title")),
            date_issued=payload.get("dateIssued"),
            congress=payload.get("congress"),
            doc_class=payload.get("docClass"),
            summary_url=payload.get("summary"),
            download_url=payload.get("download"),
        )


class GovInfoAPIClient:
    def __init__(
        self,
        api_key: str,
        *,
        base_url: str = DEFAULT_BASE_URL,
        bulk_url: str = DEFAULT_BULK_URL,
        session: Optional[requests.Session] = None,
        user_agent: str = "OpenLegislationGovInfo/0.1",
    ) -> None:
        if not api_key:
            raise ValueError("GovInfo API key is required")
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.bulk_url = bulk_url.rstrip("/")
        self.session = session or requests.Session()
        self.session.headers.setdefault("User-Agent", user_agent)

    def iter_packages(
        self,
        collection: str,
        *,
        congress: Optional[int] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        page_size: int = DEFAULT_PAGE_SIZE,
        offset: Optional[int] = None,
        offset_mark: Optional[str] = "*",
    ) -> Iterator[GovInfoPackage]:
        """Yield packages in a collection with automatic pagination."""
        offset = 0
        count: Optional[int] = None
        params: Dict[str, object] = {
            "pageSize": page_size,
            "api_key": self.api_key,
        }
        if offset is not None:
            params["offset"] = offset
        elif offset_mark is not None:
            params["offsetMark"] = offset_mark
        if start_date:
            params["startDate"] = start_date
        if end_date:
            params["endDate"] = end_date

        path: str
        if congress is not None:
            path = f"/collections/{collection}/{congress}"
        else:
            path = f"/collections/{collection}"

        while True:
            payload = self._request_json(path, params=params)
            count = payload.get("count")
            packages: List[Dict[str, object]] = payload.get("packages", [])
            if not packages:
                break
            for row in packages:
                yield GovInfoPackage.from_api(row)
            next_page = payload.get("nextPage")
            if not next_page:
                break
            params = self._page_params_from_link(next_page)
            params.setdefault("api_key", self.api_key)

    def get_package(self, package_id: str) -> Dict[str, object]:
        """Return full package metadata."""
        path = f"/packages/{package_id}"
        params = {"api_key": self.api_key}
        return self._request_json(path, params=params)

    def get_package_summary(self, package_id: str) -> Dict[str, object]:
        """Return the package summary payload."""
        path = f"/packages/{package_id}/summary"
        params = {"api_key": self.api_key}
        return self._request_json(path, params=params)

    def download_file(self, url: str, *, chunk_size: int = 1 << 15) -> Iterable[bytes]:
        """Stream a file from an absolute GovInfo URL."""
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                with self.session.get(url, params={"api_key": self.api_key}, stream=True, timeout=60) as resp:
                    if resp.status_code >= 400:
                        raise GovInfoError(f"HTTP {resp.status_code} downloading {url}")
                    for chunk in resp.iter_content(chunk_size=chunk_size):
                        if chunk:
                            yield chunk
                    return
            except Exception as exc:  # pylint: disable=broad-except
                if attempt == MAX_RETRIES:
                    raise
                wait = BACKOFF_SECONDS * attempt
                logger.warning("GovInfo download failed (%s), retrying in %.1fs", exc, wait)
                time.sleep(wait)

    def resolve_bulk_path(self, collection: str, congress: int, *parts: str) -> str:
        segments = "/".join(str(p).strip("/") for p in parts if p)
        return f"{self.bulk_url}/{collection}/{congress}/{segments}".rstrip("/")

    def _request_json(self, path: str, *, params: Optional[Dict[str, object]] = None) -> Dict[str, object]:
        params = dict(params or {})
        params.setdefault("api_key", self.api_key)
        url = f"{self.base_url}{path}"
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                resp = self.session.get(url, params=params, timeout=30)
                if resp.status_code >= 400:
                    raise GovInfoError(f"HTTP {resp.status_code} calling {url}: {resp.text[:200]}")
                return resp.json()
            except Exception as exc:  # pylint: disable=broad-except
                if attempt == MAX_RETRIES:
                    raise
                wait = BACKOFF_SECONDS * attempt
                logger.warning("GovInfo request failed (%s), retrying in %.1fs", exc, wait)
                time.sleep(wait)
        raise GovInfoError(f"Failed to fetch {url}")

    @staticmethod
    def _page_params_from_link(link: str) -> Dict[str, object]:
        """Extract query parameters from the `nextPage` link returned by the API."""
        try:
            query = link.split("?", 1)[1]
        except IndexError:
            return {}
        params: Dict[str, object] = {}
        for part in query.split("&"):
            if not part:
                continue
            if "=" in part:
                key, value = part.split("=", 1)
            else:
                key, value = part, ""
            params[key] = value
        return params
