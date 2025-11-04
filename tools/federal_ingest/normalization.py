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
    return {key: _normalize_value(value) for key, value in raw.items()}


def congress_bill_to_record(bill: CongressBill) -> NormalizedRecord:
    payload = bill.dict(exclude_none=True)
    payload.setdefault("bill_id", bill.bill_id)
    return NormalizedRecord(
        table="congress_bills",
        unique_columns=["bill_id"],
        data=_normalize_payload(payload),
    )


def congress_member_to_record(member: CongressMember) -> NormalizedRecord:
    payload = member.dict(exclude_none=True)
    return NormalizedRecord(
        table="congress_members",
        unique_columns=["bioguide_id"],
        data=_normalize_payload(payload),
    )


def congress_vote_to_record(vote: CongressVote) -> NormalizedRecord:
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
    payload = package.dict(exclude_none=True)
    return NormalizedRecord(
        table="govinfo_packages",
        unique_columns=["package_id"],
        data=_normalize_payload(payload),
    )


def govinfo_download_to_record(download: GovInfoDownload) -> NormalizedRecord:
    payload = download.dict(exclude_none=True)
    return NormalizedRecord(
        table="govinfo_downloads",
        unique_columns=["package_id", "format"],
        data=_normalize_payload(payload),
    )


def govinfo_bulk_resource_to_record(resource: "BulkResource") -> NormalizedRecord:
    resource_key = ":".join(
        part for part in [resource.collection, resource.congress or "", resource.resource_path] if part
    )
    payload = {
        "resource_key": resource_key,
        "collection": resource.collection,
        "congress": resource.congress,
        "resource_path": resource.resource_path,
        "download_url": resource.url,
        "retrieved_at": datetime.utcnow(),
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
