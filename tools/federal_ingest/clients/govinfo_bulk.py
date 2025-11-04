"""GovInfo bulkdata directory crawler."""
from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from typing import Iterable, Iterator, List, Optional
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

from ..normalization import NormalizedRecord, govinfo_bulk_resource_to_record

logger = logging.getLogger(__name__)

BULK_BASE_URL = "https://www.govinfo.gov/bulkdata"
USER_AGENT = "OpenLegislationFederalIngest/1.0 (+https://github.com/nysenate/OpenLegislation)"


@dataclass
class BulkResource:
    """Metadata describing a GovInfo bulk data resource."""

    url: str
    collection: str
    congress: Optional[str]
    resource_path: str


class GovInfoBulkClient:
    """Crawl bulkdata directory listings and yield normalized records."""

    def __init__(self, *, session: Optional[requests.Session] = None) -> None:
        self.session = session or requests.Session()
        self.session.headers.setdefault("User-Agent", USER_AGENT)

    def close(self) -> None:
        self.session.close()

    def __enter__(self) -> "GovInfoBulkClient":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:  # type: ignore[override]
        self.close()

    def _fetch_listing(self, url: str) -> List[str]:
        logger.debug("Fetching bulk listing %s", url)
        response = self.session.get(url, timeout=30)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        return [link.get("href") for link in soup.select("a[href]")]

    def _iter_resources(
        self,
        base_url: str,
        *,
        collection: str,
        congress: Optional[str],
        prefix: str = "",
        file_extensions: tuple[str, ...] = ('.xml', '.zip', '.json', '.csv', '.txt'),
    ) -> Iterable[BulkResource]:
        listing = self._fetch_listing(base_url)
        for href in listing:
            if not href or href in {"../", "?"}:
                continue
            absolute = urljoin(base_url, href)
            if href.endswith("/"):
                # Recurse into sub-directory
                yield from self._iter_resources(
                    absolute,
                    collection=collection,
                    congress=congress,
                    prefix=os.path.join(prefix, href.strip("/")),
                    file_extensions=file_extensions,
                )
                continue
            if not href.lower().endswith(file_extensions):
                continue
            resource_path = os.path.join(prefix, os.path.basename(urlparse(absolute).path))
            yield BulkResource(
                url=absolute,
                collection=collection,
                congress=congress,
                resource_path=resource_path,
            )

    def iter_resources(
        self,
        *,
        collection: str,
        congress: Optional[str] = None,
        normalized: bool = True,
        file_extensions: tuple[str, ...] = ('.xml', '.zip', '.json', '.csv', '.txt'),
    ) -> Iterator[NormalizedRecord | BulkResource]:
        target_url = BULK_BASE_URL.rstrip("/") + f"/{collection}"
        if congress:
            target_url += f"/{congress}"
        if not target_url.endswith("/"):
            target_url += "/"
        resources = self._iter_resources(
            target_url,
            collection=collection,
            congress=congress,
            prefix="",
            file_extensions=file_extensions,
        )
        for resource in resources:
            yield (
                govinfo_bulk_resource_to_record(resource)
                if normalized
                else resource
            )


__all__ = ["GovInfoBulkClient", "BulkResource"]
