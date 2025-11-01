"""Client for the NY OpenLegislation API."""
from __future__ import annotations

import os
from typing import Dict, Iterable, Optional

from .base import BaseApiClient
from ..models import OpenLegislationAgenda, OpenLegislationBill

API_BASE_URL = "https://legislation.nysenate.gov/api/3"


class OpenLegislationClient(BaseApiClient):
    def __init__(self, api_key: Optional[str] = None, **kwargs):
        self.api_key = api_key or os.getenv("NY_OPENLEG_API_KEY")
        if not self.api_key:
            raise ValueError("NY_OPENLEG_API_KEY environment variable is required")
        super().__init__(API_BASE_URL, **kwargs)

    def _with_key(self, params: Optional[Dict[str, str]] = None) -> Dict[str, str]:
        merged = dict(params or {})
        merged["key"] = self.api_key
        return merged

    def list_bills(self, session: str, limit: int = 200) -> Iterable[OpenLegislationBill]:
        response = self.get(
            "bills/",
            params=self._with_key({"sessionYear": session, "limit": str(limit)}),
        )
        data = response.json().get("result", {}).get("items", [])
        for item in data:
            bill_data = item.get("result", {}).get("data", {}).get("bill", {})
            if bill_data:
                yield OpenLegislationBill(**bill_data)

    def get_bill(self, session: str, print_no: str) -> OpenLegislationBill:
        response = self.get(
            f"bills/{session}/{print_no}",
            params=self._with_key(),
        )
        bill_data = response.json().get("result", {}).get("data", {}).get("bill", {})
        return OpenLegislationBill(**bill_data)

    def list_agendas(self, year: str, limit: int = 200) -> Iterable[OpenLegislationAgenda]:
        response = self.get(
            f"agendas/{year}",
            params=self._with_key({"limit": str(limit)}),
        )
        data = response.json().get("result", {}).get("items", [])
        for item in data:
            agenda_data = item.get("result", {}).get("data", {}).get("committeeAgenda", {})
            if agenda_data:
                yield OpenLegislationAgenda(**agenda_data)

