"""Utilities for converting API payloads to normalized database-friendly records."""
from __future__ import annotations

from datetime import date, datetime, timezone
from typing import TYPE_CHECKING, Any, Dict, Mapping, Sequence, TypedDict

from tools.data_pipeline.models import (
    CongressBill,
    CongressMember,
    CongressVote,
    GovInfoDownload,
    GovInfoPackage,
)

if TYPE_CHECKING:
    from .clients.govinfo_bulk import BulkResource


class NormalizedRecord(TypedDict):
    table: str
    unique_columns: Sequence[str]
    data: Dict[str, Any]


def _serialize_datetime(value: datetime | date | None) -> str | None:
    """
    Convert a date or datetime to an ISO 8601 UTC timestamp string ending with "Z".
    
    Parameters:
        value (datetime | date | None): The date or datetime to serialize; if `None`, the function returns `None`.
    
    Returns:
        str | None: The corresponding ISO 8601 UTC timestamp (e.g. "2025-11-04T12:34:56Z"), or `None` when `value` is `None`.
    """
    if value is None:
        return None
    if isinstance(value, datetime):
        # Convert timezone-aware datetimes to UTC, then strip tzinfo
        if value.tzinfo is not None:
            value = value.astimezone(timezone.utc)
        return value.replace(tzinfo=None).isoformat() + "Z"
    # For date values, create an aware midnight datetime in UTC
    aware_midnight = datetime.combine(value, datetime.min.time()).replace(tzinfo=timezone.utc)
    # Convert to UTC (no-op since already UTC) and strip tzinfo
    return aware_midnight.replace(tzinfo=None).isoformat() + "Z"


def _normalize_value(value: Any) -> Any:
    """
    Normalize common payload values into JSON-friendly primitives.
    
    Parameters:
        value (Any): The input value to normalize; may be a datetime/date, list, set, mapping, or any other type.
    
    Returns:
        Any: A normalized value:
          - datetime/date -> UTC ISO 8601 string ending with "Z" (or None if input is None)
          - list -> list with each element normalized
          - set -> sorted list with each element normalized
          - mapping -> dict with the same keys and normalized values
          - other -> returned unchanged
    """
    if isinstance(value, (datetime, date)):
        return _serialize_datetime(value)
    if isinstance(value, list):
        return [_normalize_value(item) for item in value]
    if isinstance(value, set):
        return [_normalize_value(item) for item in sorted(value)]
    if isinstance(value, Mapping):
        return {key: _normalize_value(val) for key, val in value.items()}
    return value


def _normalize_payload(raw: Mapping[str, Any]) -> Dict[str, Any]:
    """
    Normalize every value in the input mapping for storage-friendly serialization.
    
    Parameters:
        raw (Mapping[str, Any]): Mapping of string keys to values to be normalized. Values may contain datetimes, dates, lists, sets, or nested mappings; each value is recursively converted into a JSON/DB-friendly form (datetimes to UTC ISO strings ending with "Z", sets to sorted lists, nested mappings/lists normalized).
    
    Returns:
        Dict[str, Any]: A new dictionary with the same keys and normalized values suitable for storage or serialization.
    """
    return {key: _normalize_value(value) for key, value in raw.items()}


def congress_bill_to_record(bill: CongressBill) -> NormalizedRecord:
    """
    Convert a CongressBill model into a normalized database record.
    
    Ensures the payload includes a "bill_id" (populated from bill.bill_id if missing) and normalizes all values for storage.
    
    Returns:
        NormalizedRecord: A record targeting the "congress_bills" table with unique_columns ["bill_id"] and normalized data.
    """
    payload = bill.dict(exclude_none=True)
    payload.setdefault("bill_id", bill.bill_id)
    return NormalizedRecord(
        table="congress_bills",
        unique_columns=["bill_id"],
        data=_normalize_payload(payload),
    )


def congress_member_to_record(member: CongressMember) -> NormalizedRecord:
    """
    Convert a CongressMember model into a normalized database record.
    
    Parameters:
    	member (CongressMember): The source CongressMember model; None fields are excluded.
    
    Returns:
    	NormalizedRecord: A record for the "congress_members" table with unique_columns `["bioguide_id"]` and `data` containing the normalized payload.
    """
    payload = member.dict(exclude_none=True)
    return NormalizedRecord(
        table="congress_members",
        unique_columns=["bioguide_id"],
        data=_normalize_payload(payload),
    )


def congress_vote_to_record(vote: CongressVote) -> NormalizedRecord:
    """
    Convert a CongressVote into a NormalizedRecord suitable for insertion into the database.
    
    If the vote payload lacks an "id", one is constructed as "{chamber}-{congress}-{session or '1'}-{roll_call}".
    
    Parameters:
        vote (CongressVote): The vote model to convert; its dict representation (excluding None) is normalized.
    
    Returns:
        NormalizedRecord: Record for table "congress_votes" with unique_columns ["id"] and normalized data.
    """
    payload = vote.dict(exclude_none=True)
    payload.setdefault(
        "id",
        f"{vote.chamber}-{vote.congress}-{vote.session or '1'}-{vote.roll_call}",
    )
    return NormalizedRecord(
        table="congress_votes",
        unique_columns=["id"],
        data=_normalize_payload(payload),
    )


def govinfo_package_to_record(package: GovInfoPackage) -> NormalizedRecord:
    """
    Convert a GovInfoPackage into a NormalizedRecord targeting the `govinfo_packages` table.
    
    Parameters:
        package (GovInfoPackage): The package model to convert; fields with value `None` are omitted.
    
    Returns:
        NormalizedRecord: Record with `table` set to `"govinfo_packages"`, `unique_columns` set to `["package_id"]`, and `data` containing the package's fields with datetimes and collections normalized for storage.
    """
    payload = package.dict(exclude_none=True)
    return NormalizedRecord(
        table="govinfo_packages",
        unique_columns=["package_id"],
        data=_normalize_payload(payload),
    )


def govinfo_download_to_record(download: GovInfoDownload) -> NormalizedRecord:
    """
    Convert a GovInfoDownload model into a NormalizedRecord for the govinfo_downloads table.
    
    Parameters:
        download (GovInfoDownload): The source model to convert.
    
    Returns:
        NormalizedRecord: Record with `table` set to "govinfo_downloads", `unique_columns` set to ["package_id", "format"], and `data` containing the payload from `download` with datetimes and nested values normalized.
    """
    payload = download.dict(exclude_none=True)
    return NormalizedRecord(
        table="govinfo_downloads",
        unique_columns=["package_id", "format"],
        data=_normalize_payload(payload),
    )


def govinfo_bulk_resource_to_record(resource: "BulkResource") -> NormalizedRecord:
    """
    Convert a BulkResource into a NormalizedRecord targeting the govinfo_bulk_resources table.
    
    Parameters:
        resource (BulkResource): The bulk resource to convert; its `collection`, optional `congress`, `resource_path`, and `url` are used.
    
    Returns:
        NormalizedRecord: A record with table "govinfo_bulk_resources", unique_columns ["resource_key"], and data containing:
            - resource_key: string formed by joining `collection`, `congress` (if present), and `resource_path` with ':'.
            - collection, congress, resource_path: source fields from the resource.
            - download_url: the resource `url`.
            - retrieved_at: the UTC timestamp when the record was created.
            - raw_payload: original fields (`url`, `collection`, `congress`, `resource_path`) for traceability.
    """
    resource_key = ":".join(
        part for part in [resource.collection, resource.congress or "", resource.resource_path] if part
    )
    payload = {
        "resource_key": resource_key,
        "collection": resource.collection,
        "congress": resource.congress,
        "resource_path": resource.resource_path,
        "download_url": resource.url,
        "retrieved_at": datetime.now(timezone.utc),
        "raw_payload": {
            "url": resource.url,
            "collection": resource.collection,
            "congress": resource.congress,
            "resource_path": resource.resource_path,
        },
    }
    return NormalizedRecord(
        table="govinfo_bulk_resources",
        unique_columns=["resource_key"],
        data=_normalize_payload(payload),
    )


__all__ = [
    "NormalizedRecord",
    "congress_bill_to_record",
    "congress_member_to_record",
    "congress_vote_to_record",
    "govinfo_package_to_record",
    "govinfo_download_to_record",
    "govinfo_bulk_resource_to_record",
]