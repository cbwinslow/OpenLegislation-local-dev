"""Client for GovInfo bulk data API."""
from __future__ import annotations

import os
from typing import Dict, Iterable, Optional

from .base import BaseApiClient
from ..models import GovInfoDownload, GovInfoPackage

API_BASE_URL = "https://api.govinfo.gov"


class GovInfoClient(BaseApiClient):
    def __init__(self, api_key: Optional[str] = None, **kwargs):
        self.api_key = api_key or os.getenv("GOVINFO_API_KEY")
        if not self.api_key:
            raise ValueError("GOVINFO_API_KEY environment variable is required")
        super().__init__(API_BASE_URL, **kwargs)

    def _with_key(self, params: Optional[Dict[str, str]] = None) -> Dict[str, str]:
        merged = {"api_key": self.api_key}
        if params:
            merged.update({k: v for k, v in params.items() if v is not None})
        return merged

    def list_packages(self, collection: str, page_size: int = 100) -> Iterable[GovInfoPackage]:
        params = self._with_key({"pageSize": str(page_size)})
        response = self.get(f"collections/{collection}", params=params)
        data = response.json()
        for package in data.get("packages", []):
            yield GovInfoPackage(**package)

    def get_package(self, package_id: str) -> GovInfoPackage:
        response = self.get(f"packages/{package_id}", params=self._with_key())
        return GovInfoPackage(**response.json())

    def list_downloads(self, package_id: str) -> Iterable[GovInfoDownload]:
        response = self.get(f"packages/{package_id}/download", params=self._with_key())
        downloads = response.json().get("download", {})
        for fmt, info in downloads.items():
            yield GovInfoDownload(package_id=package_id, format=fmt, **info)

