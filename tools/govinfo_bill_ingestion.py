#!/usr/bin/env python3
"""
GovInfo Bill Data Ingestion

Ingests bill data from GovInfo XML files into the database with resume capability.
Parses XML files, extracts bill metadata, sponsors, and amendment actions.
Supports incremental updates and error recovery.

Features:
- XML parsing from GovInfo bulk data
- Bill metadata extraction (title, sponsors, actions)
- Database insertion with UPSERT logic
- Resume capability for interrupted processing
- Error handling and validation

Usage:
    from govinfo_bill_ingestion import GovInfoBillIngestor

    ingestor = GovInfoBillIngestor(xml_dir="/path/to/xml/files")
    ingestor.run()
"""

import argparse
import os
import sys
import logging
from datetime import datetime
from typing import Iterable, List, Dict, Any, Optional, Union
from pathlib import Path
from lxml import etree

from base_ingestion_process import BaseIngestionProcess
from settings import settings

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from govinfo.models import GovInfoAction, GovInfoBillRecord, GovInfoSponsor
from govinfo.persistence import persist_bill_record
from db.session import session_scope

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class GovInfoBillIngestor(BaseIngestionProcess):
    """Ingestor for GovInfo bill XML data"""

    def __init__(
        self,
        xml_dir: Optional[Union[str, Iterable[str]]] = None,
        patterns: Optional[Iterable[str]] = None,
        files: Optional[Iterable[str]] = None,
        recursive: bool = False,
        **kwargs,
    ):
        super().__init__(**kwargs)

        if xml_dir is None:
            xml_dir = getattr(settings, "govinfo_xml_dir", "staging/govinfo/bills")
        if isinstance(xml_dir, str):
            xml_dir = [xml_dir]
        self.xml_dirs = [Path(p) for p in xml_dir]
        self.patterns = list(patterns or ["BILLS-*.xml", "BILLSTATUS-*.xml"])
        self.extra_files = [Path(f) for f in files] if files else []
        self.recursive = recursive

        for directory in self.xml_dirs:
            directory.mkdir(parents=True, exist_ok=True)

    def get_data_source(self) -> str:
        """Return the data source identifier"""
        return "govinfo"

    def get_target_table(self) -> str:
        """Return the target database table name"""
        return "master.bill"

    def get_record_id_column(self) -> str:
        """Return the column name that uniquely identifies records"""
        return "bill_print_no"

    def discover_records(self) -> List[Dict[str, Any]]:
        """Discover XML files to process"""
        logger.info("Discovering XML files from configured locations")

        candidate_files: List[Path] = []
        for directory in self.xml_dirs:
            for pattern in self.patterns:
                iterator = directory.rglob(pattern) if self.recursive else directory.glob(pattern)
                candidate_files.extend(iterator)

        candidate_files.extend(self.extra_files)

        records = []
        for xml_path in candidate_files:
            if not xml_path.is_file():
                continue
            bill_id = self._extract_bill_id_from_path(str(xml_path))
            if bill_id:
                records.append(
                    {
                        "record_id": bill_id,
                        "xml_file": str(xml_path),
                        "metadata": {
                            "xml_file": str(xml_path),
                            "file_size": xml_path.stat().st_size,
                        },
                    }
                )

        logger.info(f"Discovered {len(records)} XML files")
        return records

    def process_record(self, record: Dict[str, Any]) -> bool:
        """Process a single bill record"""
        bill_id = record["record_id"]
        xml_file = record["xml_file"]

        logger.info(f"Processing bill {bill_id} from {xml_file}")

        try:
            # Parse XML
            bill_data = self._parse_govinfo_xml(xml_file)
            if not bill_data:
                logger.error(f"Failed to parse XML for {bill_id}")
                return False

            # Insert into database
            self._insert_bill_data(bill_data)
            logger.info(f"Successfully processed bill {bill_id}")
            return True

        except Exception as e:
            logger.error(f"Error processing bill {bill_id}: {e}")
            return False

    def _extract_bill_id_from_path(self, file_path: str) -> Optional[str]:
        """Extract bill ID from file path (e.g., BILLS-119hr1ih.xml -> H1-119)"""
        filename = os.path.basename(file_path)

        # Match pattern: BILLS-{congress}{type}{number}{stage}.xml
        if not filename.startswith("BILLS-") or not filename.endswith(".xml"):
            return None

        # Remove BILLS- and .xml
        parts = filename[6:-4]  # Remove 'BILLS-' and '.xml'

        try:
            # Parse congress number
            congress_end = 0
            while congress_end < len(parts) and parts[congress_end].isdigit():
                congress_end += 1

            congress = int(parts[:congress_end])
            remaining = parts[congress_end:]

            # Parse bill type (h or s)
            if remaining.startswith("h"):
                bill_type = "H"
                remaining = remaining[1:]
            elif remaining.startswith("s"):
                bill_type = "S"
                remaining = remaining[1:]
            else:
                return None

            # Skip any additional type indicators (like 'r' in 'hr1ih')
            if remaining.startswith("r"):
                remaining = remaining[1:]

            # Parse bill number
            number_end = 0
            while number_end < len(remaining) and remaining[number_end].isdigit():
                number_end += 1

            bill_number = remaining[:number_end]

            return f"{bill_type}{bill_number}-{congress}"

        except (ValueError, IndexError):
            return None

    def _parse_govinfo_xml(self, xml_file: str) -> Optional[Dict[str, Any]]:
        """Parse GovInfo XML file and extract bill data"""
        try:
            tree = etree.parse(xml_file)
            root = tree.getroot()

            # Extract basic bill info
            bill_number_elem = root.find(".//billNumber")
            bill_number = ""
            bill_type = "H"  # default

            if bill_number_elem is not None:
                bill_number_text = bill_number_elem.text.strip()
                # Parse bill number like "H.R. 1" or "S. 2"
                if bill_number_text.startswith("H.R."):
                    bill_type = "H"
                    bill_number = "H" + bill_number_text.replace("H.R.", "").strip()
                elif bill_number_text.startswith("S."):
                    bill_type = "S"
                    bill_number = "S" + bill_number_text.replace("S.", "").strip()
                else:
                    bill_number = bill_number_text

            congress_elem = root.get("congress")
            congress = int(congress_elem) if congress_elem else 0

            title = self._text(root.find(".//officialTitle"))
            short_title = self._text(root.find(".//shortTitle"))
            summary = self._text(root.find(".//summaryText"))

            sponsor = None
            sponsor_elem = root.find(".//sponsor")
            if sponsor_elem is not None:
                sponsor = GovInfoSponsor(
                    name=self._text(sponsor_elem.find(".//fullName")) or "",
                    party=self._text(sponsor_elem.find(".//party")),
                    state=self._text(sponsor_elem.find(".//state")),
                )

            cosponsors: List[GovInfoSponsor] = []
            for cosponsor_elem in root.findall(".//cosponsors/cosponsor"):
                name = self._text(cosponsor_elem.find(".//fullName"))
                if not name:
                    continue
                cosponsors.append(
                    GovInfoSponsor(
                        name=name,
                        party=self._text(cosponsor_elem.find(".//party")),
                        state=self._text(cosponsor_elem.find(".//state")),
                        role="cosponsor",
                    )
                )

            actions: List[GovInfoAction] = []
            for action_elem in root.findall(".//actions/action"):
                text_value = self._text(action_elem.find(".//text"))
                if not text_value:
                    continue
                actions.append(
                    GovInfoAction(
                        description=text_value,
                        action_code=self._text(action_elem.find(".//actionCode")),
                        chamber=self._text(action_elem.find(".//chamber")),
                        action_date=self._parse_datetime(self._text(action_elem.find(".//actionDate"))),
                    )
                )

            introduced_date = self._parse_datetime(self._text(root.find(".//introducedDate")))

            bill_print_no = bill_number.replace(" ", "")
            if not bill_print_no:
                logger.error(f"Missing bill number in XML: {xml_file}")
                return None

            return GovInfoBillRecord(
                bill_print_no=bill_print_no,
                session_year=congress,
                bill_type=bill_type,
                title=title,
                short_title=short_title,
                summary=summary,
                congress=congress,
                sponsor=sponsor,
                cosponsors=cosponsors,
                actions=actions,
                introduced_date=introduced_date,
                active_version="",
            )

        except Exception as e:
            logger.error(f"XML parsing error for {xml_file}: {e}")
            return None

    def _insert_bill_data(self, record: GovInfoBillRecord) -> None:
        """Persist bill data using SQLAlchemy ORM."""

        with session_scope() as session:
            persist_bill_record(session, record)

    @staticmethod
    def _text(element: Optional[etree._Element]) -> Optional[str]:
        if element is None or element.text is None:
            return None
        value = element.text.strip()
        return value or None

    @staticmethod
    def _parse_datetime(value: Optional[str]) -> Optional[datetime]:
        if not value:
            return None
        value = value.strip()
        if not value:
            return None
        try:
            return datetime.fromisoformat(value.replace("Z", ""))
        except ValueError:
            for fmt in ("%Y-%m-%d", "%m/%d/%Y"):
                try:
                    return datetime.strptime(value, fmt)
                except ValueError:
                    continue
        logger.warning("Unable to parse datetime '%s'", value)
        return None


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Ingest GovInfo bill XML files")
    parser.add_argument("--xml-dir", dest="xml_dirs", nargs="*", help="Directory/directories containing XML files")
    parser.add_argument(
        "--pattern",
        dest="patterns",
        nargs="*",
        help="Filename patterns to include (default: BILLS-*.xml BILLSTATUS-*.xml)",
    )
    parser.add_argument("--file", dest="files", nargs="*", help="Explicit XML files to ingest")
    parser.add_argument("--recursive", action="store_true", help="Recursively search directories for XML files")
    parser.add_argument("--reset", action="store_true", help="Reset ingestion tracker before running")
    parser.add_argument("--limit", type=int, help="Limit number of files processed")
    parser.add_argument("--log-level", default="INFO", help="Logging level (default: INFO)")
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    logging.basicConfig(level=getattr(logging, args.log_level.upper(), logging.INFO))
    ingestor = GovInfoBillIngestor(
        xml_dir=args.xml_dirs,
        patterns=args.patterns,
        files=args.files,
        recursive=args.recursive,
    )
    ingestor.run(resume=not args.reset, reset=args.reset, limit=args.limit)
