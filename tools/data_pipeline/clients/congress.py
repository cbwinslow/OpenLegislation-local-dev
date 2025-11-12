"""Client wrapper for api.congress.gov."""
from __future__ import annotations

import os
from typing import Dict, Iterable, Optional

from .base import BaseApiClient
from ..models import CongressBill, CongressMember, CongressVote

API_BASE_URL = "https://api.congress.gov/v3"


class CongressGovClient(BaseApiClient):
    """Interact with api.congress.gov endpoints."""

    def __init__(self, api_key: Optional[str] = None, **kwargs):
        self.api_key = api_key or os.getenv("CONGRESS_GOV_API_KEY")
        if not self.api_key:
            raise ValueError("CONGRESS_GOV_API_KEY environment variable is required")
        super().__init__(API_BASE_URL, **kwargs)

    def _with_key(self, params: Optional[Dict[str, str]] = None) -> Dict[str, str]:
        merged = {"api_key": self.api_key}
        if params:
            merged.update({k: v for k, v in params.items() if v is not None})
        return merged

    def list_bills(self, congress: str, limit: int = 250) -> Iterable[CongressBill]:
        response = self.get("bill", params=self._with_key({"congress": congress, "format": "json", "limit": str(limit)}))
        data = response.json()
        for bill in data.get("bills", []):
            yield CongressBill(**bill)

    def get_bill(self, congress: str, bill_type: str, bill_number: str) -> CongressBill:
        path = f"bill/{congress}/{bill_type}/{bill_number}"
        response = self.get(path, params=self._with_key({"format": "json"}))
        bill = response.json().get("bill", {})
        return CongressBill(**bill)

    def list_members(self, congress: str, chamber: str, limit: int = 250) -> Iterable[CongressMember]:
        response = self.get(
            f"member/{congress}/{chamber}",
            params=self._with_key({"format": "json", "limit": str(limit)}),
        )
        data = response.json()
        for member in data.get("members", []):
            yield CongressMember(**member)

    def list_votes(self, congress: str, chamber: str, limit: int = 250) -> Iterable[CongressVote]:
        response = self.get(
            f"vote/{congress}/{chamber}",
            params=self._with_key({"format": "json", "limit": str(limit)}),
        )
        data = response.json()
        for vote in data.get("votes", []):
            yield CongressVote(**vote)

