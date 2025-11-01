"""Client for the Congress.gov v3 REST API."""

from __future__ import annotations

from typing import Any, Dict, Iterable, List, Optional

from tools.settings import settings

from .base_client import BaseAPIClient, RequestConfig


class CongressGovClient(BaseAPIClient):
    """Lightweight wrapper around the Congress.gov REST API."""

    DEFAULT_BASE_URL = "https://api.congress.gov/v3"

    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None):
        config = RequestConfig(
            api_key=api_key or settings.congress_api_key,
            base_url=base_url or self.DEFAULT_BASE_URL,
        )
        super().__init__(config)

    def list_resources(
        self,
        resource: str,
        limit: int = 20,
        offset: int = 0,
        **filters: Any,
    ) -> Dict[str, Any]:
        """Fetch a paginated collection for a resource type."""

        url = self._resolve_url(resource)
        params = {"limit": limit, "offset": offset, **filters}
        if self.config.api_key:
            params["api_key"] = self.config.api_key
        return self._request("GET", url, params=params)

    def get_resource(self, resource: str, *path_segments: Iterable[Any], **filters: Any) -> Dict[str, Any]:
        """Fetch a specific resource using additional path segments."""

        url = self._resolve_url(resource, *path_segments)
        params = dict(filters)
        if self.config.api_key:
            params["api_key"] = self.config.api_key
        return self._request("GET", url, params=params)

    @staticmethod
    def normalize_items(resource: str, payload: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Normalize API collections into portable records."""

        items = payload.get(resource, [])
        if isinstance(items, dict) and "item" in items:
            items = items.get("item", [])
        if not isinstance(items, list):
            items = [items]

        normalized: List[Dict[str, Any]] = []
        for item in items:
            if not isinstance(item, dict):
                continue
            record_id = item.get("url") or item.get("billNumber") or item.get("bioguideId")
            normalized.append(
                {
                    "source": "congress.gov",
                    "resource": resource,
                    "record_id": record_id,
                    "title": item.get("title") or item.get("name") or record_id,
                    "updated": item.get("updateDate") or item.get("lastModifiedDate"),
                    "payload": item,
                }
            )
        return normalized
