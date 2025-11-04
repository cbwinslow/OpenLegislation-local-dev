"""Congress.gov REST API ingestion client with normalization helpers."""
from __future__ import annotations

from typing import Iterable, Iterator

from tools.data_pipeline.clients.congress import CongressGovClient as _BaseCongressGovClient
from tools.data_pipeline.models import CongressBill, CongressMember, CongressVote

from ..normalization import (
    congress_bill_to_record,
    congress_member_to_record,
    congress_vote_to_record,
    NormalizedRecord,
)


class CongressGovIngestClient(_BaseCongressGovClient):
    """Extend the shared Congress.gov client with normalized iterators."""

    def iter_bills(
        self,
        *,
        congress: str,
        limit: int = 250,
        normalized: bool = True,
    ) -> Iterator[NormalizedRecord | CongressBill]:
        bills: Iterable[CongressBill] = super().list_bills(congress=congress, limit=limit)
        for bill in bills:
            yield congress_bill_to_record(bill) if normalized else bill

    def iter_members(
        self,
        *,
        congress: str,
        chamber: str,
        limit: int = 250,
        normalized: bool = True,
    ) -> Iterator[NormalizedRecord | CongressMember]:
        members: Iterable[CongressMember] = super().list_members(
            congress=congress, chamber=chamber, limit=limit
        )
        for member in members:
            yield congress_member_to_record(member) if normalized else member

    def iter_votes(
        self,
        *,
        congress: str,
        chamber: str,
        limit: int = 250,
        normalized: bool = True,
    ) -> Iterator[NormalizedRecord | CongressVote]:
        votes: Iterable[CongressVote] = super().list_votes(
            congress=congress, chamber=chamber, limit=limit
        )
        for vote in votes:
            yield congress_vote_to_record(vote) if normalized else vote


__all__ = ["CongressGovIngestClient"]
