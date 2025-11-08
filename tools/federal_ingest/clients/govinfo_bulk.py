"""GovInfo bulkdata directory crawler."""
from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from typing import Iterable, Iterator, List, Optional
from types import TracebackType
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
        """
        Initialize the client with an HTTP session.
        
        Parameters:
            session (Optional[requests.Session]): Optional requests Session to use for HTTP requests. If omitted, a new Session is created. The session will have its `User-Agent` header set to the module's default `USER_AGENT` if not already present.
        """
        self.session = session or requests.Session()
        self.session.headers.setdefault("User-Agent", USER_AGENT)

    def close(self) -> None:
        """
        Close the underlying HTTP session.
        
        Releases network resources held by the client's requests.Session.
        """
        self.session.close()

    def __enter__(self) -> "GovInfoBulkClient":
        """
        Enter a context and provide this GovInfoBulkClient instance for use with a with-statement.
        
        Returns:
            GovInfoBulkClient: This client instance (`self`) to be used as the context manager target.
        """
        return self


        self.close()

    def _fetch_listing(self, url: str) -> List[str]:
        """
        Extract href attributes from the HTML listing at the given URL.
        
        Parameters:
            url (str): URL of the directory/listing page to fetch and parse.
        
        Returns:
            List[str]: A list of href attribute values extracted from all anchor tags on the page.
        """
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

    ) -> Iterable[BulkResource]:
        """
        Recursively traverse the HTML directory listing at base_url and yield BulkResource objects for supported bulk files.
        
        Parameters:
            base_url (str): Absolute URL of the directory listing to crawl.
            collection (str): GovInfo collection identifier to attach to each resource.
            congress (Optional[str]): Congress identifier to attach to each resource, or None if not applicable.
            prefix (str): Accumulated path prefix representing the resource's location within the collection.
        
        Returns:
            Iterable[BulkResource]: BulkResource instances for files with extensions `.xml`, `.zip`, `.json`, `.csv`, or `.txt` discovered under the directory.
        """
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

    ) -> Iterator[NormalizedRecord | BulkResource]:
        """
        Iterate over GovInfo bulk data resources for a collection and optional congress.
        
        Parameters:
        	collection (str): Bulkdata collection name to crawl (e.g., "uscode", "bills").
        	congress (Optional[str]): Optional congress identifier to restrict the crawl (e.g., "116").
        	normalized (bool): If True yield normalized records; if False yield raw BulkResource objects.
        
        Returns:
        	Iterator[NormalizedRecord | BulkResource]: Yields a normalized record for each discovered resource when `normalized` is True, or the corresponding `BulkResource` when `normalized` is False.
        """
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

        )
        for resource in resources:
            yield (
                govinfo_bulk_resource_to_record(resource)
                if normalized
                else resource
            )


__all__ = ["GovInfoBulkClient", "BulkResource"]