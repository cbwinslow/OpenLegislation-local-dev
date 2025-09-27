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

import os
import glob
import logging
from typing import List, Dict, Any, Optional, Union
from pathlib import Path
from lxml import etree

from base_ingestion_process import BaseIngestionProcess
from settings import settings

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class GovInfoBillIngestor(BaseIngestionProcess):
    """Ingestor for GovInfo bill XML data"""

    def __init__(self, xml_dir: Optional[str] = None, **kwargs):
        super().__init__(**kwargs)
        self.xml_dir = xml_dir or getattr(
            settings, "govinfo_xml_dir", "/tmp/govinfo_xml"
        )

        # Ensure XML directory exists
        Path(self.xml_dir).mkdir(parents=True, exist_ok=True)

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
        logger.info(f"Discovering XML files in {self.xml_dir}")

        # Find all XML files matching GovInfo pattern
        xml_pattern = os.path.join(self.xml_dir, "BILLS-*.xml")
        xml_files = glob.glob(xml_pattern)

        records = []
        for xml_file in xml_files:
            bill_id = self._extract_bill_id_from_path(xml_file)
            if bill_id:
                records.append(
                    {
                        "record_id": bill_id,
                        "xml_file": xml_file,
                        "metadata": {
                            "xml_file": xml_file,
                            "file_size": os.path.getsize(xml_file),
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

            title_elem = root.find(".//officialTitle")
            title = title_elem.text if title_elem is not None else ""

            # Extract sponsor
            sponsor = None
            sponsor_elem = root.find(".//sponsor")
            if sponsor_elem is not None:
                name_elem = sponsor_elem.find(".//fullName")
                party_elem = sponsor_elem.find(".//party")
                state_elem = sponsor_elem.find(".//state")

                sponsor = {
                    "name": name_elem.text if name_elem is not None else "",
                    "party": party_elem.text if party_elem is not None else "",
                    "state": state_elem.text if state_elem is not None else "",
                }

            # Extract actions
            actions = []
            action_elems = root.findall(".//actions/action")
            for action_elem in action_elems:
                action_date_elem = action_elem.find(".//actionDate")
                chamber_elem = action_elem.find(".//chamber")
                text_elem = action_elem.find(".//text")
                code_elem = action_elem.find(".//actionCode")

                if text_elem is not None:
                    actions.append(
                        {
                            "action_date": (
                                action_date_elem.text
                                if action_date_elem is not None
                                else ""
                            ),
                            "chamber": (
                                chamber_elem.text if chamber_elem is not None else ""
                            ),
                            "description": text_elem.text,
                            "action_type": (
                                code_elem.text if code_elem is not None else ""
                            ),
                        }
                    )

            # Validate that we have at least a bill number
            if not bill_number:
                logger.error(f"Missing bill number in XML: {xml_file}")
                return None

            return {
                "bill_number": bill_number,
                "congress": congress,
                "title": title,
                "bill_type": bill_type,
                "sponsor": sponsor,
                "actions": actions,
                "data_source": "govinfo",
            }

        except Exception as e:
            logger.error(f"XML parsing error for {xml_file}: {e}")
            return None

    def _insert_bill_data(self, bill_data: Dict[str, Any]) -> None:
        """Insert bill data into database"""
        conn = None
        try:
            import psycopg2

            conn = psycopg2.connect(**self.db_config)
            cursor = conn.cursor()

            # Insert/update bill
            bill_print_no = f"{bill_data['bill_type']}{bill_data['bill_number']}"

            bill_session_year = bill_data["congress"]
            cursor.execute(
                """
                INSERT INTO master.bill
                (bill_print_no, bill_session_year, congress, title, bill_type, data_source, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s, now())
                ON CONFLICT (bill_print_no, bill_session_year)
                DO UPDATE SET
                    title = EXCLUDED.title,
                    bill_type = EXCLUDED.bill_type,
                    data_source = EXCLUDED.data_source,
                    updated_at = now()
                RETURNING bill_id
            """,
                (
                    bill_print_no,
                    bill_session_year,
                    bill_data["congress"],
                    bill_data["title"],
                    bill_data["bill_type"],
                    bill_data["data_source"],
                ),
            )

            bill_id = cursor.fetchone()[0]

            # Insert sponsor if present
            if bill_data.get("sponsor"):
                sponsor = bill_data["sponsor"]
                cursor.execute(
                    """
                    INSERT INTO master.bill_sponsor
                    (bill_id, sponsor_name, party, state)
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT DO NOTHING
                """,
                    (bill_id, sponsor["name"], sponsor["party"], sponsor["state"]),
                )

            # Insert actions
            for action in bill_data.get("actions", []):
                cursor.execute(
                    """
                    INSERT INTO master.bill_amendment_action
                    (bill_print_no, bill_session_year, action_date, chamber, description, action_type)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    ON CONFLICT (bill_print_no, bill_session_year, action_date, description)
                    DO NOTHING
                """,
                    (
                        bill_print_no,
                        bill_session_year,
                        action["action_date"],
                        action["chamber"],
                        action["description"],
                        action["action_type"],
                    ),
                )

            conn.commit()

        except Exception as e:
            if conn:
                conn.rollback()
            raise e
        finally:
            if conn:
                conn.close()


if __name__ == "__main__":
    # Run as standalone script
    import argparse

    parser = argparse.ArgumentParser(description="Ingest GovInfo bill data")
    parser.add_argument("--xml-dir", help="Directory containing XML files")
    parser.add_argument("--db-config", help="Database config JSON file")

    args = parser.parse_args()

    # Load database config if provided
    db_config = None
    if args.db_config:
        import json

        with open(args.db_config, "r") as f:
            db_config = json.load(f)

    # Create and run ingestor
    ingestor = GovInfoBillIngestor(xml_dir=args.xml_dir, db_config=db_config)
    ingestor.run()
