"""Client and helpers for the congress.gov REST API."""

from __future__ import annotations

import logging
import os
from typing import Any, Dict, Iterable, Iterator, Mapping, Optional

from .base import NormalizedRecord, Resource, build_retrying_session, safe_get

LOGGER = logging.getLogger(__name__)

API_ROOT = "https://api.congress.gov/v3"
MAX_PAGE_SIZE = 250


class CongressClient:
    """Minimal congress.gov API client with retry handling."""

    def __init__(self, api_key: Optional[str] = None) -> None:
        self.api_key = api_key or os.getenv("CONGRESS_API_KEY")
        if not self.api_key:
            raise ValueError("A CONGRESS_API_KEY environment variable or --api-key argument is required")
        self.session = build_retrying_session()

    def iter_collection(
        self,
        collection: str,
        *,
        limit: Optional[int] = None,
        page_size: int = MAX_PAGE_SIZE,
        **extra_params: Any,
    ) -> Iterator[NormalizedRecord]:
        """Iterate over items in the provided ``collection``."""

        page_size = min(page_size, MAX_PAGE_SIZE)
        params: Dict[str, Any] = {
            "api_key": self.api_key,
            "format": "json",
            "pageSize": page_size,
        }
        params.update(extra_params)

        url = f"{API_ROOT}/{collection}"
        count = 0
        while url:
            LOGGER.debug("Fetching %s", url)
            response = self.session.get(url, params=params if params else None, timeout=60)
            response.raise_for_status()
            payload = response.json()
            items = payload.get(collection) or payload.get("data") or payload.get("items") or []
            for item in items:
                if limit is not None and count >= limit:
                    return
                normalized = normalize_item(collection, item)
                if normalized is None:
                    continue
                yield normalized
                count += 1
            if limit is not None and count >= limit:
                return
            pagination = payload.get("pagination", {})
            next_url = pagination.get("next")
            if not next_url:
                break
            url = next_url
            params = None  # the next URL is pre-signed with the API key


def normalize_item(collection: str, item: Mapping[str, Any]) -> Optional[NormalizedRecord]:
    """Convert a raw congress.gov payload into a :class:`NormalizedRecord`."""

    external_id = (
        str(
            item.get("billNumber")
            or item.get("number")
            or item.get("bioguideId")
            or item.get("id")
            or item.get("url")
        )
        if item
        else None
    )
    if not external_id:
        LOGGER.debug("Skipping congress.gov item without identifier: %s", item)
        return None

    title = item.get("title") or item.get("name")
    summary = safe_get(item, "summary", "text") or item.get("description")
    document_date = safe_get(item, "latestAction", "actionDate") or item.get("updateDate")

    resources = []
    text_versions: Iterable[Mapping[str, Any]] = safe_get(item, "textVersions") or []
    for version in text_versions:
        download = version.get("downloadable") or version.get("link")
        if not download:
            continue
        resources.append(Resource(url=download, filename=f"{external_id}_{version.get('versionCode', 'text')}.xml"))

    return NormalizedRecord(
        source="congress.gov",
        collection=collection,
        external_id=external_id,
        title=title,
        summary=summary,
        document_date=document_date,
        data=item,
        resources=tuple(resources),
    )

