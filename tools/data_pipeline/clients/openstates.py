"""Client for OpenStates v3 API."""
from __future__ import annotations

import os
from typing import Dict, Iterable, Optional

from .base import BaseApiClient
from ..models import OpenStatesBill, OpenStatesPerson, OpenStatesVoteEvent

API_BASE_URL = "https://v3.openstates.org"


class OpenStatesClient(BaseApiClient):
    def __init__(self, api_key: Optional[str] = None, **kwargs):
        self.api_key = api_key or os.getenv("OPENSTATES_API_KEY")
        if not self.api_key:
            raise ValueError("OPENSTATES_API_KEY environment variable is required")
        headers = kwargs.pop("headers", {})
        headers.setdefault("X-API-KEY", self.api_key)
        super().__init__(API_BASE_URL, default_headers=headers, **kwargs)

    @staticmethod
    def _clean(params: Dict[str, Optional[str]]) -> Dict[str, str]:
        return {k: v for k, v in params.items() if v is not None}

    def list_people(self, state: Optional[str] = None, chamber: Optional[str] = None) -> Iterable[OpenStatesPerson]:
        params: Dict[str, Optional[str]] = {"jurisdiction": state, "chamber": chamber}
        response = self.get("people", params=self._clean(params))
        data = response.json()
        for person in data.get("results", []):
            yield OpenStatesPerson(**person)

    def list_bills(
        self,
        state: Optional[str] = None,
        session: Optional[str] = None,
        classification: Optional[str] = None,
    ) -> Iterable[OpenStatesBill]:
        params: Dict[str, Optional[str]] = {
            "jurisdiction": state,
            "session": session,
            "classification": classification,
        }
        response = self.get("bills", params=self._clean(params))
        data = response.json()
        for bill in data.get("results", []):
            yield OpenStatesBill(**bill)

    def list_votes(self, bill_id: str) -> Iterable[OpenStatesVoteEvent]:
        response = self.get("votesevents", params={"bill": bill_id})
        data = response.json()
        for vote in data.get("results", []):
            yield OpenStatesVoteEvent(**vote)

