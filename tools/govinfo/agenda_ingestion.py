#!/usr/bin/env python3
"""GovInfo agenda ingestion.

Parses structured JSON exports and persists agenda information addenda via the
SQLAlchemy models introduced in ``src/db/models/agenda.py``.

The JSON payload is expected to contain keys such as ``agendaNumber``, ``year``,
``infoAddenda`` (list), and nested committee entries. See ``GovInfoAgendaRecord``
for the Python representation.
"""
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
    GovInfoAgendaRecord,
    GovInfoAgendaAddendum,
    GovInfoAgendaCommittee,
    GovInfoAgendaCommitteeItem,
)
from .persistence import persist_agenda_record
from db.session import session_scope

logger = logging.getLogger(__name__)


class GovInfoAgendaIngestor(BaseIngestionProcess):
    """Load GovInfo agenda JSON files into PostgreSQL."""

    def __init__(self, agenda_dir: Optional[str] = None, **kwargs):
        super().__init__(**kwargs)
        self.agenda_dir = agenda_dir or getattr(settings, "govinfo_agenda_dir", "staging/govinfo/agendas")
        Path(self.agenda_dir).mkdir(parents=True, exist_ok=True)

    def get_data_source(self) -> str:
        return "govinfo_agenda"

    def get_target_table(self) -> str:
        return "master.agenda"

    def get_record_id_column(self) -> str:
        return "agenda_no"

    def discover_records(self) -> List[Dict[str, str]]:
        pattern = os.path.join(self.agenda_dir, "AGENDAS-*.json")
        records: List[Dict[str, str]] = []
        for path in Path(self.agenda_dir).glob("AGENDAS-*.json"):
            agenda_id = path.stem.replace("AGENDAS-", "")
            records.append({"record_id": agenda_id, "path": str(path)})
        logger.info("Discovered %d agenda files", len(records))
        return records

    def process_record(self, record: Dict[str, str]) -> bool:
        filepath = record.get("path")
        if not filepath:
            logger.error("Missing path for record %s", record)
            return False

        try:
            agenda_record = self._load_agenda(Path(filepath))
            with session_scope() as session:
                persist_agenda_record(session, agenda_record)
            return True
        except Exception as exc:  # pylint: disable=broad-except
            logger.exception("Failed to ingest agenda %s: %s", record["record_id"], exc)
            return False

    # Parsing helpers -------------------------------------------------

    def _load_agenda(self, path: Path) -> GovInfoAgendaRecord:
        payload = json.loads(path.read_text(encoding="utf-8"))
        agenda_no = int(payload["agendaNumber"])
        year = int(payload["year"])
        published = _parse_datetime(payload.get("publishedDateTime"))
        modified = _parse_datetime(payload.get("modifiedDateTime"))

        info_addenda: List[GovInfoAgendaAddendum] = []
        for addendum in payload.get("infoAddenda", []):
            addendum_model = GovInfoAgendaAddendum(
                addendum_id=str(addendum.get("addendumId", "")),
                week_of=_parse_datetime(addendum.get("weekOf")),
                modified_date_time=_parse_datetime(addendum.get("modifiedDateTime")),
                published_date_time=_parse_datetime(addendum.get("publishedDateTime")),
            )

            for committee in addendum.get("committees", []):
                committee_model = GovInfoAgendaCommittee(
                    committee_name=str(committee.get("committeeName", "")),
                    committee_chamber=str(committee.get("committeeChamber", "senate")),
                    meeting_date_time=_parse_datetime(committee.get("meetingDateTime")),
                    chair=committee.get("chair"),
                    location=committee.get("location"),
                    notes=committee.get("notes"),
                )

                for item in committee.get("items", []):
                    committee_model.items.append(
                        GovInfoAgendaCommitteeItem(
                            bill_print_no=str(item.get("billPrintNo", "")),
                            session_year=int(item.get("billSessionYear", 0)),
                            amendment=str(item.get("billAmendVersion", "")),
                            message=item.get("message"),
                        )
                    )

                addendum_model.committees.append(committee_model)

            info_addenda.append(addendum_model)

        return GovInfoAgendaRecord(
            agenda_no=agenda_no,
            year=year,
            published_date_time=published,
            modified_date_time=modified,
            info_addenda=info_addenda,
        )


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
    ingestor = GovInfoAgendaIngestor()
    ingestor.run()
