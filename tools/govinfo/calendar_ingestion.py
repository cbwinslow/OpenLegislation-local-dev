#!/usr/bin/env python3
"""GovInfo calendar ingestion using the shared ORM persistence helpers."""
from __future__ import annotations

import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, Iterable, List, Optional

from base_ingestion_process import BaseIngestionProcess
from settings import settings

from .models import (
    GovInfoCalendarRecord,
    GovInfoCalendarActiveList,
    GovInfoCalendarEntry,
    GovInfoCalendarSupplemental,
)
from .persistence import persist_calendar_record
from db.session import session_scope

logger = logging.getLogger(__name__)


class GovInfoCalendarIngestor(BaseIngestionProcess):
    def __init__(self, calendar_dir: Optional[str] = None, **kwargs):
        super().__init__(**kwargs)
        self.calendar_dir = calendar_dir or getattr(
            settings, "govinfo_calendar_dir", "staging/govinfo/calendars"
        )
        Path(self.calendar_dir).mkdir(parents=True, exist_ok=True)

    def get_data_source(self) -> str:
        return "govinfo_calendar"

    def get_target_table(self) -> str:
        return "master.calendar"

    def get_record_id_column(self) -> str:
        return "calendar_no"

    def discover_records(self) -> List[Dict[str, str]]:
        records: List[Dict[str, str]] = []
        for path in Path(self.calendar_dir).glob("CALENDARS-*.json"):
            calendar_id = path.stem.replace("CALENDARS-", "")
            records.append({"record_id": calendar_id, "path": str(path)})
        logger.info("Discovered %d calendar files", len(records))
        return records

    def process_record(self, record: Dict[str, str]) -> bool:
        filepath = record.get("path")
        if not filepath:
            logger.error("Missing path for calendar record %s", record)
            return False
        try:
            calendar_record = self._load_calendar(Path(filepath))
            with session_scope() as session:
                persist_calendar_record(session, calendar_record)
            return True
        except Exception as exc:  # pylint: disable=broad-except
            logger.exception("Failed to ingest calendar %s: %s", record["record_id"], exc)
            return False

    def _load_calendar(self, path: Path) -> GovInfoCalendarRecord:
        payload = json.loads(path.read_text(encoding="utf-8"))
        calendar_no = int(payload["calendarNumber"])
        calendar_year = int(payload["year"])

        record = GovInfoCalendarRecord(
            calendar_no=calendar_no,
            calendar_year=calendar_year,
            published_date_time=_parse_datetime(payload.get("publishedDateTime")),
            modified_date_time=_parse_datetime(payload.get("modifiedDateTime")),
        )

        for active in payload.get("activeLists", []):
            active_model = GovInfoCalendarActiveList(
                sequence_no=active.get("sequenceNumber"),
                calendar_date=_parse_datetime(active.get("calendarDate")),
                release_date_time=_parse_datetime(active.get("releaseDateTime")),
                notes=active.get("notes"),
            )
            for entry in active.get("entries", []):
                active_model.entries.append(_entry_from_payload(entry))
            record.active_lists.append(active_model)

        for supplemental in payload.get("supplements", []):
            supplement_model = GovInfoCalendarSupplemental(
                sup_version=str(supplemental.get("version", "")),
                release_date_time=_parse_datetime(supplemental.get("releaseDateTime")),
                notes=supplemental.get("notes"),
            )
            for entry in supplemental.get("entries", []):
                supplement_model.entries.append(_entry_from_payload(entry))
            record.supplements.append(supplement_model)

        return record


def _entry_from_payload(payload: Dict[str, object]) -> GovInfoCalendarEntry:
    return GovInfoCalendarEntry(
        bill_calendar_no=int(payload.get("billCalendarNumber", 0)),
        bill_print_no=payload.get("billPrintNo"),
        bill_session_year=_safe_int(payload.get("billSessionYear")),
        bill_amend_version=str(payload.get("billAmendVersion", "")),
        high=payload.get("high"),
    )


def _safe_int(value: Optional[object]) -> Optional[int]:
    if value is None or value == "":
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _parse_datetime(value: Optional[str]) -> Optional[datetime]:
    if not value:
        return None
    value = value.strip()
    if not value:
        return None
    for fmt in ("%Y-%m-%dT%H:%M:%S", "%Y-%m-%d", "%Y-%m-%dT%H:%M:%SZ"):
        try:
            return datetime.strptime(value.replace("Z", ""), fmt)
        except ValueError:
            continue
    logger.warning("Unable to parse datetime '%s'", value)
    return None


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    ingestor = GovInfoCalendarIngestor()
    ingestor.run()
