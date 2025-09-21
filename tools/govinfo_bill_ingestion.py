#!/usr/bin/env python3
"""
GovInfo Bill Data Ingestion

Ingests bill data from GovInfo XML files using the generic ingestion framework.
This is a sample implementation showing how to use the BaseIngestionProcess.

Features:
- Parses GovInfo XML bill files
- Inserts bill data into database
- Resume capability from interruptions
- Progress tracking and error handling

Usage:
    python3 tools/govinfo_bill_ingestion.py --xml-dir /path/to/xml/files --db-config config.json
"""

import os
import glob
from pathlib import Path
from typing import Dict, List, Optional, Any
from lxml import etree

from settings import settings
from base_ingestion_process import BaseIngestionProcess, run_ingestion_process


class GovInfoBillIngestor(BaseIngestionProcess):
    """Ingests bill data from GovInfo XML files using generic framework"""

    def __init__(self, xml_dir: Optional[str] = None, **kwargs):
        super().__init__(**kwargs)
        self.xml_dir = xml_dir or getattr(settings, 'govinfo_xml_dir', '/tmp/govinfo')

    def get_data_source(self) -> str:
        """Return data source identifier"""
        return "govinfo"

    def get_target_table(self) -> str:
        """Return target table name"""
        return "master.bill"

    def get_record_id_column(self) -> str:
        """Return record ID column"""
        return "bill_print_no"

    def discover_records(self) -> List[Dict[str, Any]]:
        """Discover XML files to process"""
        xml_files = []

        # Find all XML files in the directory
        if os.path.exists(self.xml_dir):
            for xml_file in glob.glob(os.path.join(self.xml_dir, '**', '*.xml'), recursive=True):
                # Extract bill identifier from filename or path
                bill_id = self._extract_bill_id_from_path(xml_file)
                if bill_id:
                    xml_files.append({
                        'record_id': bill_id,
                        'file_path': xml_file,
                        'file_size': os.path.getsize(xml_file),
                        'metadata': {
                            'xml_file': xml_file,
                            'discovered_at': str(Path(xml_file).stat().st_mtime)
                        }
                    })

        print(f"Discovered {len(xml_files)} XML files in {self.xml_dir}")
        return xml_files

    def _extract_bill_id_from_path(self, file_path: str) -> Optional[str]:
        """Extract bill identifier from file path"""
        # Example: /path/to/BILLS-119hr1ih/BILLS-119hr1ih.xml -> H1-119
        filename = os.path.basename(file_path)
        if filename.startswith('BILLS-') and filename.endswith('.xml'):
            # Parse BILLS-119hr1ih.xml
            parts = filename.replace('BILLS-', '').replace('.xml', '').split('h')
            if len(parts) >= 2:
                congress = parts[0]
                bill_num = parts[1].rstrip('ih')
                bill_type = 'H'  # House bill
                return f"{bill_type}{bill_num}-{congress}"

        return None

    def process_record(self, record: Dict[str, Any]) -> bool:
        """Process a single XML file"""
        xml_file = record['metadata']['xml_file']
        bill_id = record['record_id']

        print(f"Processing bill {bill_id} from {xml_file}")

        try:
            # Parse XML file
            bill_data = self._parse_govinfo_xml(xml_file)
            if not bill_data:
                print(f"Failed to parse {xml_file}")
                return False

            # Insert bill data
            success = self._insert_bill_data(bill_data)
            if success:
                print(f"Successfully ingested bill {bill_id}")
            return success

        except Exception as e:
            print(f"Error processing {xml_file}: {e}")
            return False

    def _parse_govinfo_xml(self, xml_file: str) -> Optional[Dict[str, Any]]:
        """Parse GovInfo XML file into bill data structure"""
        try:
            tree = etree.parse(xml_file)
            root = tree.getroot()

            # Extract basic bill information
            bill_num = root.findtext('.//billNumber') or root.findtext('.//legislativeIdentifier') or 'UNKNOWN'
            congress_text = root.findtext('.//congress') or root.get('congress')
            congress = int(congress_text) if congress_text and congress_text.isdigit() else 119

            # Normalize bill number (e.g., "H.R. 1" -> "H1")
            if 'H.R.' in bill_num:
                bill_num = f"H{bill_num.replace('H.R.', '').strip()}"
            elif 'S.' in bill_num:
                bill_num = f"S{bill_num.replace('S.', '').strip()}"

            title = root.findtext('.//officialTitle') or root.findtext('.//title') or ''

            # Sponsor information
            sponsor_elem = root.find('.//sponsor')
            sponsor = None
            if sponsor_elem is not None:
                sponsor_name = sponsor_elem.findtext('fullName') or sponsor_elem.findtext('name')
                if sponsor_name:
                    sponsor = {
                        'name': sponsor_name,
                        'party': sponsor_elem.findtext('party'),
                        'state': sponsor_elem.findtext('state')
                    }

            # Actions
            actions = []
            for action_elem in root.findall('.//actions/action'):
                action_date = action_elem.findtext('actionDate')
                if action_date:
                    actions.append({
                        'action_date': action_date,
                        'chamber': action_elem.findtext('chamber') or '',
                        'description': action_elem.findtext('text') or '',
                        'action_type': action_elem.findtext('actionCode') or ''
                    })

            return {
                'bill_number': bill_num,
                'congress': congress,
                'title': title,
                'bill_type': bill_num[0] if bill_num else 'H',  # H or S
                'sponsor': sponsor,
                'actions': actions,
                'data_source': 'govinfo'
            }

        except Exception as e:
            print(f"XML parsing error for {xml_file}: {e}")
            return None

    def _insert_bill_data(self, bill_data: Dict[str, Any]) -> bool:
        """Insert parsed bill data into database"""
        try:
            # Insert bill
            self.cursor.execute("""
                INSERT INTO master.bill (
                    bill_print_no, congress, title, bill_type, data_source, created_at, updated_at
                ) VALUES (%s, %s, %s, %s, %s, now(), now())
                ON CONFLICT (bill_print_no, congress) DO UPDATE SET
                    title = EXCLUDED.title,
                    bill_type = EXCLUDED.bill_type,
                    updated_at = now()
                RETURNING bill_id
            """, (
                bill_data['bill_number'],
                bill_data['congress'],
                bill_data['title'],
                bill_data['bill_type'],
                bill_data['data_source']
            ))

            bill_result = self.cursor.fetchone()
            if not bill_result:
                return False

            bill_id = bill_result['bill_id']

            # Insert sponsor if available
            if bill_data.get('sponsor'):
                sponsor = bill_data['sponsor']
                self.cursor.execute("""
                    INSERT INTO master.bill_sponsor (
                        bill_id, sponsor_name, party, state, created_at
                    ) VALUES (%s, %s, %s, %s, now())
                    ON CONFLICT (bill_id) DO NOTHING
                """, (
                    bill_id,
                    sponsor['name'],
                    sponsor.get('party'),
                    sponsor.get('state')
                ))

            # Insert actions
            for action in bill_data.get('actions', []):
                self.cursor.execute("""
                    INSERT INTO master.bill_amendment_action (
                        bill_print_no, bill_session_year, action_date, chamber,
                        description, action_type, created_at
                    ) VALUES (%s, %s, %s, %s, %s, %s, now())
                    ON CONFLICT (bill_print_no, bill_session_year, action_date, description) DO NOTHING
                """, (
                    bill_data['bill_number'],
                    bill_data['congress'],
                    action['action_date'],
                    action['chamber'],
                    action['description'],
                    action['action_type']
                ))

            self.conn.commit()
            return True

        except Exception as e:
            print(f"Database insertion error: {e}")
            self.conn.rollback()
            return False

    def close(self):
        """Clean up resources"""
        super().close()


if __name__ == '__main__':
    run_ingestion_process(GovInfoBillIngestor, "GovInfo Bill")</parameter>