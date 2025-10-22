"""Client for the GovInfo REST API (api.govinfo.gov)."""

from __future__ import annotations

from typing import Any, Dict, Iterable, List, Optional

from tools.settings import settings

from .base_client import BaseAPIClient, RequestConfig


class GovInfoAPIClient(BaseAPIClient):
    """GovInfo API client supporting collection and package endpoints."""

    DEFAULT_BASE_URL = "https://api.govinfo.gov"

    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None):
        config = RequestConfig(
            api_key=api_key or settings.govinfo_api_key,
            base_url=base_url or self.DEFAULT_BASE_URL,
        )
        super().__init__(config)

    def list_packages(
        self,
        collection: str,
        offset: int = 0,
        page_size: int = 100,
        **filters: Any,
    ) -> Dict[str, Any]:
        url = self._resolve_url("collections", collection, "packages")
        params = {"offset": offset, "pageSize": page_size, **filters}
        if self.config.api_key:
            params["api_key"] = self.config.api_key
        return self._request("GET", url, params=params)

    def get_package(self, package_id: str) -> Dict[str, Any]:
        url = self._resolve_url("packages", package_id)
        params = {}
        if self.config.api_key:
            params["api_key"] = self.config.api_key
        return self._request("GET", url, params=params)

    @staticmethod
    def normalize_packages(collection: str, payload: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Normalize package list results."""

        items = payload.get("packages", [])
        normalized: List[Dict[str, Any]] = []
        for item in items:
            if not isinstance(item, dict):
                continue
            package_id = item.get("packageId")
            normalized.append(
                {
                    "source": "govinfo.api",
                    "collection": collection,
                    "record_id": package_id,
                    "title": item.get("title"),
                    "updated": item.get("lastModified"),
                    "payload": item,
                }
            )
        return normalized

    @staticmethod
    def normalize_package_detail(payload: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "source": "govinfo.api",
            "record_id": payload.get("packageId"),
            "title": payload.get("title"),
            "updated": payload.get("lastModified"),
            "payload": payload,
        }
