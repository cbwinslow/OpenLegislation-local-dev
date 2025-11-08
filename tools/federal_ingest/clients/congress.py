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
        """
        Yield bills for a given congressional session as normalized records or raw bill objects.
        
        Parameters:
        	congress (str): Congressional session identifier (e.g., "118").
        	normalized (bool): If `True`, yield a `NormalizedRecord` for each bill; if `False`, yield the original `CongressBill` objects.
        
        Returns:
        	Each iteration yields a `NormalizedRecord` when `normalized` is `True`, otherwise a `CongressBill`.
        """
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
        """
        Yield members for the specified Congress and chamber, optionally converted to normalized records.
        
        Parameters:
            congress (str): Congress session identifier.
            chamber (str): Chamber name (for example, "house" or "senate").
            limit (int): Maximum number of members to request (default 250).
            normalized (bool): If `True`, yield `NormalizedRecord` objects; if `False`, yield raw `CongressMember` objects.
        
        Returns:
            `NormalizedRecord` objects when `normalized` is `True`, `CongressMember` objects otherwise.
        """
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
        """
        Yield votes for a specific Congress and chamber, optionally normalized to records.
        
        Parameters:
            congress (str): Congress identifier (e.g., "118").
            chamber (str): Chamber name (e.g., "house" or "senate").
            limit (int): Maximum number of votes to retrieve. Defaults to 250.
            normalized (bool): If `True`, yield normalized `NormalizedRecord` objects; if `False`, yield raw `CongressVote` models.
        
        Returns:
            Iterator[NormalizedRecord | CongressVote]: An iterator that yields a normalized record for each vote when `normalized` is `True`, otherwise yields the original `CongressVote` objects.
        """
        votes: Iterable[CongressVote] = super().list_votes(
            congress=congress, chamber=chamber, limit=limit
        )
        for vote in votes:
            yield congress_vote_to_record(vote) if normalized else vote


__all__ = ["CongressGovIngestClient"]