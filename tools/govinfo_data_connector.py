#!/usr/bin/env python3
"""
GovInfo Data Connector - Universal Database Integration

Transforms govinfo bulk XML data into the unified OpenLegislation database schema.
Maps federal legislative data to work alongside existing state legislative data.

Usage:
    python govinfo_data_connector.py --input-dir /path/to/govinfo/xml --db-config config.json
"""

import argparse
import json
import logging
import os
import sys
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
import psycopg2
import psycopg2.extras
from psycopg2 import sql

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class GovInfoDataConnector:
    """Data connector for transforming govinfo XML to unified database schema"""

    def __init__(self, db_config: Dict[str, Any]):
        self.db_config = db_config
        self.conn = None
        self.cursor = None

    def connect_db(self):
        """Establish database connection"""
        try:
            self.conn = psycopg2.connect(**self.db_config)
            self.cursor = self.conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            logger.info("Database connection established")
        except Exception as e:
            logger.error(f"Failed to connect to database: {e}")
            raise

    def disconnect_db(self):
        """Close database connection"""
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()
        logger.info("Database connection closed")

    def parse_govinfo_xml(self, xml_file: Path) -> Optional[Dict[str, Any]]:
        """Parse govinfo XML file and extract bill or status data"""
        try:
            tree = ET.parse(xml_file)
            root = tree.getroot()

            # Detect XML type based on root tag
            root_tag = root.tag.split('}')[-1]  # Remove namespace
            if root_tag == 'bill':
                # Existing BILLS parsing
                bill_data = {
                    'xml_type': 'bill',
                    'congress': self._extract_congress(root),
                    'bill_number': self._extract_bill_number(root),
                    'bill_type': self._extract_bill_type(root),
                    'title': self._extract_title(root),
                    'short_title': self._extract_short_title(root),
                    'introduced_date': self._extract_introduced_date(root),
                    'sponsor': self._extract_sponsor(root),
                    'cosponsors': self._extract_cosponsors(root),
                    'actions': self._extract_actions(root),
                    'committees': self._extract_committees(root),
                    'subjects': self._extract_subjects(root),
                    'text_versions': self._extract_text_versions(root),
                    'relationships': self._extract_relationships(root)
                }
            elif root_tag == 'billStatus':
                # BILLSTATUS parsing
                bill_data = {
                    'xml_type': 'billStatus',
                    'congress': self._extract_congress(root),
                    'bill_number': self._extract_bill_number_from_status(root),
                    'bill_type': self._extract_bill_type_from_status(root),
                    'current_status': self._extract_current_status(root),
                    'status_date': self._extract_status_date(root),
                    'last_action': self._extract_last_action(root),
                    'actions': self._extract_status_actions(root),  # Additional status history
                    'summary': self._extract_summary(root)
                }
            else:
                logger.warning(f"Unknown XML root tag: {root_tag} in {xml_file}")
                return None

            return bill_data

        except Exception as e:
            logger.error(f"Failed to parse XML file {xml_file}: {e}")
            return None

    def _extract_congress(self, root: ET.Element) -> Optional[int]:
        """Extract congress number"""
        congress_elem = root.find('.//congress')
        return int(congress_elem.text) if congress_elem is not None else None

    def _extract_bill_number(self, root: ET.Element) -> Optional[str]:
        """Extract bill number (e.g., 'H.R. 1' -> 'H1')"""
        number_elem = root.find('.//number')
        if number_elem is not None:
            bill_num = number_elem.text
            # Convert H.R. 123 to H123, S. 456 to S456
            if '.' in bill_num:
                parts = bill_num.replace('.', '').split()
                if len(parts) >= 2:
                    return f"{parts[0]}{parts[1]}"
        return None

    def _extract_bill_type(self, root: ET.Element) -> Optional[str]:
        """Extract bill type"""
        type_elem = root.find('.//billType')
        return type_elem.text if type_elem is not None else None

    def _extract_title(self, root: ET.Element) -> Optional[str]:
        """Extract bill title"""
        title_elem = root.find('.//title')
        return title_elem.text if title_elem is not None else None

    def _extract_short_title(self, root: ET.Element) -> Optional[str]:
        """Extract short title"""
        short_title_elem = root.find('.//shortTitle')
        return short_title_elem.text if short_title_elem is not None else None

    def _extract_introduced_date(self, root: ET.Element) -> Optional[datetime]:
        """Extract introduced date"""
        date_elem = root.find('.//introducedDate')
        if date_elem is not None and date_elem.text:
            try:
                return datetime.fromisoformat(date_elem.text.replace('Z', '+00:00'))
            except ValueError:
                logger.warning(f"Invalid date format: {date_elem.text}")
        return None

    def _extract_sponsor(self, root: ET.Element) -> Optional[Dict[str, Any]]:
        """Extract sponsor information"""
        sponsor_elem = root.find('.//sponsor')
        if sponsor_elem is not None:
            return {
                'name': self._extract_text(sponsor_elem, './/fullName'),
                'party': self._extract_text(sponsor_elem, './/party'),
                'state': self._extract_text(sponsor_elem, './/state'),
                'district': self._extract_text(sponsor_elem, './/district')
            }
        return None

    def _extract_cosponsors(self, root: ET.Element) -> List[Dict[str, Any]]:
        """Extract cosponsors"""
        cosponsors = []
        for cosponsor_elem in root.findall('.//cosponsor'):
            cosponsor = {
                'name': self._extract_text(cosponsor_elem, './/fullName'),
                'party': self._extract_text(cosponsor_elem, './/party'),
                'state': self._extract_text(cosponsor_elem, './/state'),
                'district': self._extract_text(cosponsor_elem, './/district'),
                'sponsor_type': 'cosponsor',
                'date_added': self._extract_date(cosponsor_elem, './/dateAdded')
            }
            cosponsors.append(cosponsor)
        return cosponsors

    def _extract_actions(self, root: ET.Element) -> List[Dict[str, Any]]:
        """Extract bill actions"""
        actions = []
        for action_elem in root.findall('.//action'):
            action = {
                'action_date': self._extract_date(action_elem, './/actionDate'),
                'chamber': self._extract_text(action_elem, './/chamber'),
                'description': self._extract_text(action_elem, './/text'),
                'action_type': self._extract_text(action_elem, './/actionType'),
                'sequence_no': self._extract_int(action_elem, './/sequence')
            }
            actions.append(action)
        return actions

    def _extract_committees(self, root: ET.Element) -> List[Dict[str, Any]]:
        """Extract committee references"""
        committees = []
        for committee_elem in root.findall('.//committee'):
            committee = {
                'name': self._extract_text(committee_elem, './/name'),
                'referred_date': self._extract_date(committee_elem, './/referredDate')
            }
            committees.append(committee)
        return committees

    def _extract_subjects(self, root: ET.Element) -> List[str]:
        """Extract legislative subjects"""
        subjects = []
        for subject_elem in root.findall('.//subject'):
            if subject_elem.text:
                subjects.append(subject_elem.text)
        return subjects

    def _extract_text_versions(self, root: ET.Element) -> List[Dict[str, Any]]:
        """Extract text versions"""
        versions = []
        for version_elem in root.findall('.//textVersion'):
            version = {
                'version_id': self._extract_text(version_elem, './/versionId'),
                'format': self._extract_text(version_elem, './/format'),
                'content': self._extract_text(version_elem, './/content')
            }
            versions.append(version)
        return versions

    def _extract_relationships(self, root: ET.Element) -> List[Dict[str, Any]]:
        """Extract bill relationships"""
        relationships = []
        for rel_elem in root.findall('.//relationship'):
            relationship = {
                'related_bill': self._extract_text(rel_elem, './/billNumber'),
                'type': self._extract_text(rel_elem, './/type')
            }
            relationships.append(relationship)
        return relationships

    def _extract_bill_number_from_status(self, root: ET.Element) -> Optional[str]:
        """Extract bill number from BILLSTATUS XML"""
        # BILLSTATUS has <bill> child with number
        bill_elem = root.find('.//bill')
        if bill_elem is not None:
            number_elem = bill_elem.find('.//number')
            if number_elem is not None:
                bill_num = number_elem.text
                if '.' in bill_num:
                    parts = bill_num.replace('.', '').split()
                    if len(parts) >= 2:
                        return f"{parts[0]}{parts[1]}"
        return None

    def _extract_bill_type_from_status(self, root: ET.Element) -> Optional[str]:
        """Extract bill type from BILLSTATUS XML"""
        bill_elem = root.find('.//bill')
        if bill_elem is not None:
            type_elem = bill_elem.find('.//type')
            return type_elem.text if type_elem is not None else None
        return None

    def _extract_current_status(self, root: ET.Element) -> Optional[str]:
        """Extract current bill status"""
        status_elem = root.find('.//currentStatus')
        return status_elem.text if status_elem is not None else None

    def _extract_status_date(self, root: ET.Element) -> Optional[datetime]:
        """Extract status update date"""
        date_elem = root.find('.//statusDate')
        if date_elem is not None and date_elem.text:
            try:
                return datetime.fromisoformat(date_elem.text.replace('Z', '+00:00'))
            except ValueError:
                logger.warning(f"Invalid status date format: {date_elem.text}")
        return None

    def _extract_last_action(self, root: ET.Element) -> Optional[Dict[str, Any]]:
        """Extract last action details"""
        last_action_elem = root.find('.//lastAction')
        if last_action_elem is not None:
            return {
                'date': self._extract_date(last_action_elem, './/date'),
                'text': self._extract_text(last_action_elem, './/text'),
                'chamber': self._extract_text(last_action_elem, './/chamber')
            }
        return None

    def _extract_status_actions(self, root: ET.Element) -> List[Dict[str, Any]]:
        """Extract status history actions"""
        actions = []
        action_elems = root.findall('.//action')
        for action_elem in action_elems:
            action = {
                'action_date': self._extract_date(action_elem, './/date'),
                'chamber': self._extract_text(action_elem, './/chamber'),
                'description': self._extract_text(action_elem, './/text'),
                'status_type': self._extract_text(action_elem, './/statusType')
            }
            actions.append(action)
        return actions

    def _extract_summary(self, root: ET.Element) -> Optional[str]:
        """Extract bill summary from status"""
        summary_elem = root.find('.//summary')
        return summary_elem.text if summary_elem is not None else None

    def _extract_text(self, element: ET.Element, xpath: str) -> Optional[str]:
        """Extract text content from XML element"""
        found = element.find(xpath)
        return found.text if found is not None else None

    def _extract_date(self, element: ET.Element, xpath: str) -> Optional[datetime]:
        """Extract and parse date from XML element"""
        text = self._extract_text(element, xpath)
        if text:
            try:
                return datetime.fromisoformat(text.replace('Z', '+00:00'))
            except ValueError:
                logger.warning(f"Invalid date format: {text}")
        return None

    def _extract_int(self, element: ET.Element, xpath: str) -> Optional[int]:
        """Extract and parse integer from XML element"""
        text = self._extract_text(element, xpath)
        if text:
            try:
                return int(text)
            except ValueError:
                logger.warning(f"Invalid integer format: {text}")
        return None

    def insert_bill_data(self, bill_data: Dict[str, Any]) -> bool:
        """Insert or update bill data based on XML type"""
        try:
            self.conn.autocommit = False
            xml_type = bill_data.get('xml_type')

            if xml_type == 'bill':
                # Existing bill insertion logic
                bill_id = self._insert_main_bill(bill_data)
                if bill_id:
                    self._insert_sponsor(bill_data, bill_id)
                    self._insert_cosponsors(bill_data, bill_id)
                    self._insert_actions(bill_data, bill_id)
                    self._insert_committees(bill_data, bill_id)
                    self._insert_subjects(bill_data, bill_id)
                    self._insert_text_versions(bill_data, bill_id)
                    self._insert_relationships(bill_data, bill_id)
            elif xml_type == 'billStatus':
                # Status update: UPSERT on bill record with status info
                bill_id = self._update_bill_status(bill_data)
                if bill_id:
                    # Update actions if new ones present
                    self._insert_status_actions(bill_data, bill_id)
                    logger.info(f"Updated status for bill {bill_data.get('bill_number')}")
                else:
                    logger.warning(f"Bill not found for status update: {bill_data.get('bill_number')}")
                    return False
            else:
                logger.error(f"Unknown XML type: {xml_type}")
                return False

            self.conn.commit()
            return True

        except Exception as e:
            self.conn.rollback()
            logger.error(f"Failed to insert bill data: {e}")
            return False
        finally:
            self.conn.autocommit = True

    def _insert_main_bill(self, bill_data: Dict[str, Any]) -> Optional[int]:
        """Insert main bill record"""
        query = """
            INSERT INTO master.bill (
                bill_print_no, bill_session_year, title, data_source, congress,
                bill_type, short_title, status_date, sponsor_party, sponsor_state, sponsor_district
            ) VALUES (%s, %s, %s, 'federal', %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (bill_print_no, bill_session_year)
            DO UPDATE SET
                title = EXCLUDED.title,
                congress = EXCLUDED.congress,
                bill_type = EXCLUDED.bill_type,
                short_title = EXCLUDED.short_title,
                status_date = EXCLUDED.status_date,
                sponsor_party = EXCLUDED.sponsor_party,
                sponsor_state = EXCLUDED.sponsor_state,
                sponsor_district = EXCLUDED.sponsor_district
            RETURNING bill_print_no, bill_session_year
        """

        sponsor = bill_data.get('sponsor', {})
        introduced_date = bill_data.get('introduced_date')

        self.cursor.execute(query, (
            bill_data.get('bill_number'),
            bill_data.get('congress'),  # Use congress as session year for federal
            bill_data.get('title'),
            bill_data.get('congress'),
            bill_data.get('bill_type'),
            """

            self.cursor.execute(query, (
                bill_id,
                bill_data.get('congress'),
                action.get('action_date'),
                action.get('chamber'),
                action.get('description'),
                action.get('action_type'),
                action.get('sequence_no')
            ))

    def _insert_committees(self, bill_data: Dict[str, Any], bill_id: str):
        """Insert committee references"""
        committees = bill_data.get('committees', [])
        for committee in committees:
            if committee.get('name'):
                query = """
                    INSERT INTO master.bill_committee (
                        bill_print_no, bill_session_year, committee_name,
                        action_date, data_source
                    ) VALUES (%s, %s, %s, %s, 'federal')
                """

                self.cursor.execute(query, (
                    bill_id,
                    bill_data.get('congress'),
                    committee.get('name'),
                    committee.get('referred_date')
                ))

    def _insert_subjects(self, bill_data: Dict[str, Any], bill_id: str):
        """Insert legislative subjects"""
        subjects = bill_data.get('subjects', [])
        for subject in subjects:
            query = """
                INSERT INTO master.federal_bill_subject (
                    bill_print_no, bill_session_year, subject
                ) VALUES (%s, %s, %s)
            """

            self.cursor.execute(query, (
                bill_id,
                bill_data.get('congress'),
                subject
            ))

    def _insert_text_versions(self, bill_data: Dict[str, Any], bill_id: str):
        """Insert text versions"""
        versions = bill_data.get('text_versions', [])
        for version in versions:
            if version.get('content'):
                query = """
                    INSERT INTO master.federal_bill_text (
                        bill_print_no, bill_session_year, bill_amend_version,
                        version_id, text_format, content
                    ) VALUES (%s, %s, '', %s, %s, %s)
                """

                self.cursor.execute(query, (
                    bill_id,
                    bill_data.get('congress'),
                    version.get('version_id'),
                    version.get('format'),
                    version.get('content')
                ))

    def _insert_relationships(self, bill_data: Dict[str, Any], bill_id: str):
        """Insert bill relationships"""
        relationships = bill_data.get('relationships', [])
        for rel in relationships:
            if rel.get('related_bill'):
                query = """
                    INSERT INTO master.federal_bill_relationship (
                        bill_print_no, bill_session_year, related_bill_print_no,
                        related_session_year, relationship_type
                    ) VALUES (%s, %s, %s, %s, %s)
                """

                self.cursor.execute(query, (
                    bill_id,
                    bill_data.get('congress'),
                    rel.get('related_bill'),
                    bill_data.get('congress'),  # Assume same congress
                    rel.get('type', 'related')
                ))

    def process_directory(self, input_dir: Path, batch_size: int = 100, continue_on_error: bool = True):
        """Process all XML files in directory with batching and error handling"""
        # Detect collection type
        collection_type = input_dir.name.lower()
        is_billstatus = 'billstatus' in collection_type
        is_billsum = 'billsum' in collection_type
        
        xml_files = list(input_dir.glob('**/*.xml'))
        logger.info(f"Found {len(xml_files)} XML files to process ({'BILLSTATUS' if is_billstatus else 'BILLSUM' if is_billsum else 'BILLS'} mode)")

        processed = 0
        errors = 0
        batch = []

        for xml_file in xml_files:
            try:
                if is_billstatus:
                    # BILLSTATUS: typically one large file per congress/session
                    status_data = self._parse_billstatus_xml(xml_file)
                    if status_data:
                        # status_data is list of bill dicts
                        batch.extend(status_data)
                elif is_billsum:
                    # BILLSUM: one file with multiple summaries
                    summary_data = self._parse_billsum_xml(xml_file)
                    if summary_data:
                        batch.extend(summary_data)
                else:
                    # BILLS: individual files
                    bill_data = self.parse_govinfo_xml(xml_file)
                    if bill_data:
                        batch.append(bill_data)
                        
                if len(batch) >= batch_size:
                    success_count = self._process_batch(batch)
                    processed += success_count
                    errors += len(batch) - success_count
                    batch = []
                    logger.info(f"Progress: {processed + errors}/{len(xml_files)} processed")
            except Exception as e:
                logger.error(f"Failed to process {xml_file}: {e}")
                if not continue_on_error:
                    raise
                errors += 1

        # Process remaining batch
        if batch:
            success_count = self._process_batch(batch)
            processed += success_count
            errors += len(batch) - success_count

        logger.info(f"Processing complete: {processed} successful, {errors} errors")

    def _parse_billstatus_xml(self, xml_file: Path) -> Optional[List[Dict[str, Any]]]:
        """Parse BILLSTATUS XML file and extract status data for multiple bills"""
        try:
            tree = ET.parse(xml_file)
            root = tree.getroot()
            
            congress = self._extract_congress(root)
            if not congress:
                logger.warning(f"No congress found in {xml_file}")
                return None

            bills = []
            for bill_elem in root.findall('.//bill'):
                bill_data = {
                    'congress': congress,
                    'bill_number': self._extract_bill_number_from_status(bill_elem),
                    'bill_type': self._extract_bill_type_from_status(bill_elem),
                    'title': self._extract_title_from_status(bill_elem),
                    'introduced_date': self._extract_introduced_date_from_status(bill_elem),
                    'last_action_date': self._extract_last_action_date(bill_elem),
                    'status_code': self._extract_status_code(bill_elem),
                    'sponsor': self._extract_sponsor_from_status(bill_elem),
                    'actions': self._extract_actions_from_status(bill_elem),
                    'data_source': 'govinfo_billstatus'
                }
                
                # Only add if we have a valid bill number
                if bill_data['bill_number']:
                    bills.append(bill_data)
                else:
                    logger.warning(f"Skipping invalid bill in {xml_file}")

            logger.info(f"Parsed {len(bills)} bills from BILLSTATUS file {xml_file}")
            return bills

        except Exception as e:
            logger.error(f"Failed to parse BILLSTATUS XML {xml_file}: {e}")
            return None

    def _extract_bill_number_from_status(self, bill_elem: ET.Element) -> Optional[str]:
        """Extract bill number from BILLSTATUS bill element"""
        number_elem = bill_elem.find('number')
        if number_elem is not None and number_elem.text:
            bill_num = number_elem.text.strip()
            # Convert H.R. 123 to H123 format (consistent with BILLS)
            if '.' in bill_num:
                parts = bill_num.replace('.', '').split()
                if len(parts) >= 2:
                    return f"{parts[0]}{parts[1]}"
        return None

    def _extract_bill_type_from_status(self, bill_elem: ET.Element) -> Optional[str]:
        """Extract bill type from BILLSTATUS"""
        type_elem = bill_elem.find('type')
        return type_elem.text if type_elem is not None else None

    def _extract_title_from_status(self, bill_elem: ET.Element) -> Optional[str]:
        """Extract title from BILLSTATUS"""
        title_elem = bill_elem.find('.//title[@type="official"]')
        return title_elem.text if title_elem is not None else None

    def _extract_introduced_date_from_status(self, bill_elem: ET.Element) -> Optional[datetime]:
        """Extract introduced date from status"""
        date_elem = bill_elem.find('.//introduced/date')
        if date_elem is not None and date_elem.text:
            try:
                # BILLSTATUS dates often in YYYY-MM-DD format
                return datetime.strptime(date_elem.text, '%Y-%m-%d')
            except ValueError:
                logger.warning(f"Invalid introduced date: {date_elem.text}")
        return None

    def _extract_last_action_date(self, bill_elem: ET.Element) -> Optional[datetime]:
        """Extract last action date from status"""
        # Find the most recent action date
        action_dates = bill_elem.findall('.//action/date')
        if action_dates:
            dates = []
            for date_elem in action_dates:
                if date_elem.text:
                    try:
                        dates.append(datetime.strptime(date_elem.text, '%Y-%m-%d'))
                    except ValueError:
                        pass
            if dates:
                return max(dates)
        return None

    def _extract_status_code(self, bill_elem: ET.Element) -> Optional[str]:
        """Extract current status code"""
        status_elem = bill_elem.find('.//status')
        if status_elem is not None:
            # Common status types: introduced, reported, passed, enacted, vetoed
            introduced = status_elem.find('introduced')
            if introduced is not None:
                return 'introduced'
            reported = status_elem.find('reported')
            if reported is not None:
                return 'reported'
            # Add more as needed
        return 'unknown'

    def _extract_sponsor_from_status(self, bill_elem: ET.Element) -> Optional[Dict[str, Any]]:
        """Extract sponsor from BILLSTATUS (simplified)"""
        sponsor_elem = bill_elem.find('.//sponsor')
        if sponsor_elem is not None:
            return {
                'name': self._extract_text(sponsor_elem, 'name'),
                'party': self._extract_text(sponsor_elem, 'party'),
                'state': self._extract_text(sponsor_elem, 'state')
            }
        return None

    def _extract_actions_from_status(self, bill_elem: ET.Element) -> List[Dict[str, Any]]:
        """Extract actions from BILLSTATUS"""
        actions = []
        for action_elem in bill_elem.findall('.//action'):
            action = {
                'action_date': self._extract_date(action_elem, 'date'),
                'chamber': self._extract_text(action_elem, 'chamber'),
                'description': self._extract_text(action_elem, 'text'),
                'action_type': self._extract_text(action_elem, 'type')
            }
            actions.append(action)
        return actions

    def _parse_billsum_xml(self, xml_file: Path) -> Optional[List[Dict[str, Any]]]:
        """Parse BILLSUM XML file and extract summary data for multiple bills"""
        try:
            tree = ET.parse(xml_file)
            root = tree.getroot()
            
            congress = self._extract_congress(root)
            if not congress:
                logger.warning(f"No congress found in {xml_file}")
                return None

            summaries = []
            # BILLSUM structure: often <billSummaries> containing <billSummary> for each bill
            for summary_elem in root.findall('.//billSummary'):
                summary_data = {
                    'congress': congress,
                    'bill_number': self._extract_bill_number_from_summary(summary_elem),
                    'bill_type': self._extract_bill_type_from_summary(summary_elem),
                    'summary_text': self._extract_summary_text(summary_elem),
                    'update_date': self._extract_update_date(summary_elem),
                    'committees': self._extract_committees_from_summary(summary_elem),
                    'legislative_history': self._extract_legislative_history(summary_elem),
                    'data_source': 'govinfo_billsum'
                }
                
                # Only add if we have a valid bill number and summary text
                if summary_data['bill_number'] and summary_data['summary_text']:
                    summaries.append(summary_data)
                else:
                    logger.warning(f"Skipping invalid summary in {xml_file}")

            logger.info(f"Parsed {len(summaries)} bill summaries from BILLSUM file {xml_file}")
            return summaries

        except Exception as e:
            logger.error(f"Failed to parse BILLSUM XML {xml_file}: {e}")
            return None

    def _extract_bill_number_from_summary(self, summary_elem: ET.Element) -> Optional[str]:
        """Extract bill number from BILLSUM summary element"""
        # Common paths: billNumber or within billReference
        number_elem = summary_elem.find('.//billNumber') or summary_elem.find('.//number')
        if number_elem is not None and number_elem.text:
            bill_num = number_elem.text.strip()
            # Normalize to H123 format if needed
            if '.' in bill_num:
                parts = bill_num.replace('.', '').split()
                if len(parts) >= 2:
                    return f"{parts[0]}{parts[1]}"
        return None

    def _extract_bill_type_from_summary(self, summary_elem: ET.Element) -> Optional[str]:
        """Extract bill type from BILLSUM"""
        type_elem = summary_elem.find('.//billType') or summary_elem.find('.//type')
        return type_elem.text if type_elem is not None else None

    def _extract_summary_text(self, summary_elem: ET.Element) -> Optional[str]:
        """Extract main summary text"""
        # Look for summary content, often in <summary> or <text>
        text_elem = summary_elem.find('.//summary') or summary_elem.find('.//text')
        if text_elem is not None:
            # Handle mixed content or paragraphs
            text_parts = []
            for child in text_elem.itertext():
                text_parts.append(child.strip())
            return ' '.join(text_parts).strip()[:5000]  # Truncate if too long
        return None

    def _extract_update_date(self, summary_elem: ET.Element) -> Optional[datetime]:
        """Extract last update date for summary"""
        date_elem = summary_elem.find('.//updateDate') or summary_elem.find('.//lastUpdated')
        if date_elem is not None and date_elem.text:
            try:
                return datetime.strptime(date_elem.text, '%Y-%m-%d')
            except ValueError:
                logger.warning(f"Invalid update date: {date_elem.text}")
        return None

    def _extract_committees_from_summary(self, summary_elem: ET.Element) -> List[Dict[str, Any]]:
        """Extract committees referenced in summary"""
        committees = []
        for comm_elem in summary_elem.findall('.//committee'):
            committee = {
                'name': self._extract_text(comm_elem, './/name'),
                'action': self._extract_text(comm_elem, './/action')
            }
            committees.append(committee)
        return committees

    def _extract_legislative_history(self, summary_elem: ET.Element) -> List[str]:
        """Extract legislative history items"""
        history = []
        for hist_elem in summary_elem.findall('.//legislativeHistory/item'):
            item_text = self._extract_text(hist_elem, './/text')
            if item_text:
                history.append(item_text)
        return history

    def insert_bill_data(self, bill_data: Dict[str, Any]) -> bool:
        """Insert or update bill data based on XML type"""
        try:
            self.conn.autocommit = False
            xml_type = bill_data.get('xml_type')

            if xml_type == 'bill':
                # Existing bill insertion logic
                bill_id = self._insert_main_bill(bill_data)
                if bill_id:
                    self._insert_sponsor(bill_data, bill_id)
                    self._insert_cosponsors(bill_data, bill_id)
                    self._insert_actions(bill_data, bill_id)
                    self._insert_committees(bill_data, bill_id)
                    self._insert_subjects(bill_data, bill_id)
                    self._insert_text_versions(bill_data, bill_id)
                    self._insert_relationships(bill_data, bill_id)
            elif xml_type == 'billStatus':
                # Status update: UPSERT on bill record with status info
                bill_id = self._update_bill_status(bill_data)
                if bill_id:
                    # Update actions if new ones present
                    self._insert_status_actions(bill_data, bill_id)
                    logger.info(f"Updated status for bill {bill_data.get('bill_number')}")
                else:
                    logger.warning(f"Bill not found for status update: {bill_data.get('bill_number')}")
                    return False
            else:
                logger.error(f"Unknown XML type: {xml_type}")
                return False

            self.conn.commit()
            return True

        except Exception as e:
            self.conn.rollback()
            logger.error(f"Failed to insert bill data: {e}")
            return False
        finally:
            self.conn.autocommit = True

    def _insert_main_bill(self, bill_data: Dict[str, Any]) -> Optional[int]:
        """Insert main bill record"""
        query = """
            INSERT INTO master.bill (
                bill_print_no, bill_session_year, title, data_source, congress,
                bill_type, short_title, status_date, sponsor_party, sponsor_state, sponsor_district
            ) VALUES (%s, %s, %s, 'federal', %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (bill_print_no, bill_session_year)
            DO UPDATE SET
                title = EXCLUDED.title,
                congress = EXCLUDED.congress,
                bill_type = EXCLUDED.bill_type,
                short_title = EXCLUDED.short_title,
                status_date = EXCLUDED.status_date,
                sponsor_party = EXCLUDED.sponsor_party,
                sponsor_state = EXCLUDED.sponsor_state,
                sponsor_district = EXCLUDED.sponsor_district
            RETURNING bill_print_no, bill_session_year
        """

        sponsor = bill_data.get('sponsor', {})
        introduced_date = bill_data.get('introduced_date')

        self.cursor.execute(query, (
            bill_data.get('bill_number'),
            bill_data.get('congress'),  # Use congress as session year for federal
            bill_data.get('title'),
            bill_data.get('congress'),
            bill_data.get('bill_type'),
            """

            self.cursor.execute(query, (
                bill_id,
                bill_data.get('congress'),
                action.get('action_date'),
                action.get('chamber'),
                action.get('description'),
                action.get('action_type'),
                action.get('sequence_no')
            ))

    def _insert_committees(self, bill_data: Dict[str, Any], bill_id: str):
        """Insert committee references"""
        committees = bill_data.get('committees', [])
        for committee in committees:
            if committee.get('name'):
                query = """
                    INSERT INTO master.bill_committee (
                        bill_print_no, bill_session_year, committee_name,
                        action_date, data_source
                    ) VALUES (%s, %s, %s, %s, 'federal')
                """

                self.cursor.execute(query, (
                    bill_id,
                    bill_data.get('congress'),
                    committee.get('name'),
                    committee.get('referred_date')
                ))

    def _insert_subjects(self, bill_data: Dict[str, Any], bill_id: str):
        """Insert legislative subjects"""
        subjects = bill_data.get('subjects', [])
        for subject in subjects:
            query = """
                INSERT INTO master.federal_bill_subject (
                    bill_print_no, bill_session_year, subject
                ) VALUES (%s, %s, %s)
            """

            self.cursor.execute(query, (
                bill_id,
                bill_data.get('congress'),
                subject
            ))

    def _insert_text_versions(self, bill_data: Dict[str, Any], bill_id: str):
        """Insert text versions"""
        versions = bill_data.get('text_versions', [])
        for version in versions:
            if version.get('content'):
                query = """
                    INSERT INTO master.federal_bill_text (
                        bill_print_no, bill_session_year, bill_amend_version,
                        version_id, text_format, content
                    ) VALUES (%s, %s, '', %s, %s, %s)
                """

                self.cursor.execute(query, (
                    bill_id,
                    bill_data.get('congress'),
                    version.get('version_id'),
                    version.get('format'),
                    version.get('content')
                ))

    def _insert_relationships(self, bill_data: Dict[str, Any], bill_id: str):
        """Insert bill relationships"""
        relationships = bill_data.get('relationships', [])
        for rel in relationships:
            if rel.get('related_bill'):
                query = """
                    INSERT INTO master.federal_bill_relationship (
                        bill_print_no, bill_session_year, related_bill_print_no,
                        related_session_year, relationship_type
                    ) VALUES (%s, %s, %s, %s, %s)
                """

                self.cursor.execute(query, (
                    bill_id,
                    bill_data.get('congress'),
                    rel.get('related_bill'),
                    bill_data.get('congress'),  # Assume same congress
                    rel.get('type', 'related')
                ))

    def process_directory(self, input_dir: Path, batch_size: int = 100, continue_on_error: bool = True):
        """Process all XML files in directory with batching and error handling"""
        # Detect collection type
        collection_type = input_dir.name.lower()
        is_billstatus = 'billstatus' in collection_type
        is_billsum = 'billsum' in collection_type
        
        xml_files = list(input_dir.glob('**/*.xml'))
        logger.info(f"Found {len(xml_files)} XML files to process ({'BILLSTATUS' if is_billstatus else 'BILLSUM' if is_billsum else 'BILLS'} mode)")

        processed = 0
        errors = 0
        batch = []

        for xml_file in xml_files:
            try:
                if is_billstatus:
                    # BILLSTATUS: typically one large file per congress/session
                    status_data = self._parse_billstatus_xml(xml_file)
                    if status_data:
                        # status_data is list of bill dicts
                        batch.extend(status_data)
                elif is_billsum:
                    # BILLSUM: one file with multiple summaries
                    summary_data = self._parse_billsum_xml(xml_file)
                    if summary_data:
                        batch.extend(summary_data)
                else:
                    # BILLS: individual files
                    bill_data = self.parse_govinfo_xml(xml_file)
                    if bill_data:
                        batch.append(bill_data)
                        
                if len(batch) >= batch_size:
                    success_count = self._process_batch(batch)
                    processed += success_count
                    errors += len(batch) - success_count
                    batch = []
                    logger.info(f"Progress: {processed + errors}/{len(xml_files)} processed")
            except Exception as e:
                logger.error(f"Failed to process {xml_file}: {e}")
                if not continue_on_error:
                    raise
                errors += 1

        # Process remaining batch
        if batch:
            success_count = self._process_batch(batch)
            processed += success_count
            errors += len(batch) - success_count

        logger.info(f"Processing complete: {processed} successful, {errors} errors")

    def _parse_billstatus_xml(self, xml_file: Path) -> Optional[List[Dict[str, Any]]]:
        """Parse BILLSTATUS XML file and extract status data for multiple bills"""
        try:
            tree = ET.parse(xml_file)
            root = tree.getroot()
            
            congress = self._extract_congress(root)
            if not congress:
                logger.warning(f"No congress found in {xml_file}")
                return None

            bills = []
            for bill_elem in root.findall('.//bill'):
                bill_data = {
                    'congress': congress,
                    'bill_number': self._extract_bill_number_from_status(bill_elem),
                    'bill_type': self._extract_bill_type_from_status(bill_elem),
                    'title': self._extract_title_from_status(bill_elem),
                    'introduced_date': self._extract_introduced_date_from_status(bill_elem),
                    'last_action_date': self._extract_last_action_date(bill_elem),
                    'status_code': self._extract_status_code(bill_elem),
                    'sponsor': self._extract_sponsor_from_status(bill_elem),
                    'actions': self._extract_actions_from_status(bill_elem),
                    'data_source': 'govinfo_billstatus'
                }
                
                # Only add if we have a valid bill number
                if bill_data['bill_number']:
                    bills.append(bill_data)
                else:
                    logger.warning(f"Skipping invalid bill in {xml_file}")

            logger.info(f"Parsed {len(bills)} bills from BILLSTATUS file {xml_file}")
            return bills

        except Exception as e:
            logger.error(f"Failed to parse BILLSTATUS XML {xml_file}: {e}")
            return None

    def _extract_bill_number_from_status(self, bill_elem: ET.Element) -> Optional[str]:
        """Extract bill number from BILLSTATUS bill element"""
        number_elem = bill_elem.find('number')
        if number_elem is not None and number_elem.text:
            bill_num = number_elem.text.strip()
            # Convert H.R. 123 to H123 format (consistent with BILLS)
            if '.' in bill_num:
                parts = bill_num.replace('.', '').split()
                if len(parts) >= 2:
                    return f"{parts[0]}{parts[1]}"
        return None

    def _extract_bill_type_from_status(self, bill_elem: ET.Element) -> Optional[str]:
        """Extract bill type from BILLSTATUS"""
        type_elem = bill_elem.find('type')
        return type_elem.text if type_elem is not None else None

    def _extract_title_from_status(self, bill_elem: ET.Element) -> Optional[str]:
        """Extract title from BILLSTATUS"""
        title_elem = bill_elem.find('.//title[@type="official"]')
        return title_elem.text if title_elem is not None else None

    def _extract_introduced_date_from_status(self, bill_elem: ET.Element) -> Optional[datetime]:
        """Extract introduced date from status"""
        date_elem = bill_elem.find('.//introduced/date')
        if date_elem is not None and date_elem.text:
            try:
                # BILLSTATUS dates often in YYYY-MM-DD format
                return datetime.strptime(date_elem.text, '%Y-%m-%d')
            except ValueError:
                logger.warning(f"Invalid introduced date: {date_elem.text}")
        return None

    def _extract_last_action_date(self, bill_elem: ET.Element) -> Optional[datetime]:
        """Extract last action date from status"""
        # Find the most recent action date
        action_dates = bill_elem.findall('.//action/date')
        if action_dates:
            dates = []
            for date_elem in action_dates:
                if date_elem.text:
                    try:
                        dates.append(datetime.strptime(date_elem.text, '%Y-%m-%d'))
                    except ValueError:
                        pass
            if dates:
                return max(dates)
        return None

    def _extract_status_code(self, bill_elem: ET.Element) -> Optional[str]:
        """Extract current status code"""
        status_elem = bill_elem.find('.//status')
        if status_elem is not None:
            # Common status types: introduced, reported, passed, enacted, vetoed
            introduced = status_elem.find('introduced')
            if introduced is not None:
                return 'introduced'
            reported = status_elem.find('reported')
            if reported is not None:
                return 'reported'
            # Add more as needed
        return 'unknown'

    def _extract_sponsor_from_status(self, bill_elem: ET.Element) -> Optional[Dict[str, Any]]:
        """Extract sponsor from BILLSTATUS (simplified)"""
        sponsor_elem = bill_elem.find('.//sponsor')
        if sponsor_elem is not None:
            return {
                'name': self._extract_text(sponsor_elem, 'name'),
                'party': self._extract_text(sponsor_elem, 'party'),
                'state': self._extract_text(sponsor_elem, 'state')
            }
        return None

    def _extract_actions_from_status(self, bill_elem: ET.Element) -> List[Dict[str, Any]]:
        """Extract actions from BILLSTATUS"""
        actions = []
        for action_elem in bill_elem.findall('.//action'):
            action = {
                'action_date': self._extract_date(action_elem, 'date'),
                'chamber': self._extract_text(action_elem, 'chamber'),
                'description': self._extract_text(action_elem, 'text'),
                'action_type': self._extract_text(action_elem, 'type')
            }
            actions.append(action)
        return actions

    def _parse_billsum_xml(self, xml_file: Path) -> Optional[List[Dict[str, Any]]]:
        """Parse BILLSUM XML file and extract summary data for multiple bills"""
        try:
            tree = ET.parse(xml_file)
            root = tree.getroot()
            
            congress = self._extract_congress(root)
            if not congress:
                logger.warning(f"No congress found in {xml_file}")
                return None

            summaries = []
            # BILLSUM structure: often <billSummaries> containing <billSummary> for each bill
            for summary_elem in root.findall('.//billSummary'):
                summary_data = {
                    'congress': congress,
                    'bill_number': self._extract_bill_number_from_summary(summary_elem),
                    'bill_type': self._extract_bill_type_from_summary(summary_elem),
                    'summary_text': self._extract_summary_text(summary_elem),
                    'update_date': self._extract_update_date(summary_elem),
                    'committees': self._extract_committees_from_summary(summary_elem),
                    'legislative_history': self._extract_legislative_history(summary_elem),
                    'data_source': 'govinfo_billsum'
                }
                
                # Only add if we have a valid bill number and summary text
                if summary_data['bill_number'] and summary_data['summary_text']:
                    summaries.append(summary_data)
                else:
                    logger.warning(f"Skipping invalid summary in {xml_file}")

            logger.info(f"Parsed {len(summaries)} bill summaries from BILLSUM file {xml_file}")
            return summaries

        except Exception as e:
            logger.error(f"Failed to parse BILLSUM XML {xml_file}: {e}")
            return None

    def _extract_bill_number_from_summary(self, summary_elem: ET.Element) -> Optional[str]:
        """Extract bill number from BILLSUM summary element"""
        # Common paths: billNumber or within billReference
        number_elem = summary_elem.find('.//billNumber') or summary_elem.find('.//number')
        if number_elem is not None and number_elem.text:
            bill_num = number_elem.text.strip()
            # Normalize to H123 format if needed
            if '.' in bill_num:
                parts = bill_num.replace('.', '').split()
                if len(parts) >= 2:
                    return f"{parts[0]}{parts[1]}"
        return None

    def _extract_bill_type_from_summary(self, summary_elem: ET.Element) -> Optional[str]:
        """Extract bill type from BILLSUM"""
        type_elem = summary_elem.find('.//billType') or summary_elem.find('.//type')
        return type_elem.text if type_elem is not None else None

    def _extract_summary_text(self, summary_elem: ET.Element) -> Optional[str]:
        """Extract main summary text"""
        # Look for summary content, often in <summary> or <text>
        text_elem = summary_elem.find('.//summary') or summary_elem.find('.//text')
        if text_elem is not None:
            # Handle mixed content or paragraphs
            text_parts = []
            for child in text_elem.itertext():
                text_parts.append(child.strip())
            return ' '.join(text_parts).strip()[:5000]  # Truncate if too long
        return None

    def _extract_update_date(self, summary_elem: ET.Element) -> Optional[datetime]:
        """Extract last update date for summary"""
        date_elem = summary_elem.find('.//updateDate') or summary_elem.find('.//lastUpdated')
        if date_elem is not None and date_elem.text:
            try:
                return datetime.strptime(date_elem.text, '%Y-%m-%d')
            except ValueError:
                logger.warning(f"Invalid update date: {date_elem.text}")
        return None

    def _extract_committees_from_summary(self, summary_elem: ET.Element) -> List[Dict[str, Any]]:
        """Extract committees referenced in summary"""
        committees = []
        for comm_elem in summary_elem.findall('.//committee'):
            committee = {
                'name': self._extract_text(comm_elem, './/name'),
                'action': self._extract_text(comm_elem, './/action')
            }
            committees.append(committee)
        return committees

    def _extract_legislative_history(self, summary_elem: ET.Element) -> List[str]:
        """Extract legislative history items"""
        history = []
        for hist_elem in summary_elem.findall('.//legislativeHistory/item'):
            item_text = self._extract_text(hist_elem, './/text')
            if item_text:
                history.append(item_text)
        return history

    def insert_bill_data(self, bill_data: Dict[str, Any]) -> bool:
        """Insert or update bill data based on XML type"""
        try:
            self.conn.autocommit = False
            xml_type = bill_data.get('xml_type')

            if xml_type == 'bill':
                # Existing bill insertion logic
                bill_id = self._insert_main_bill(bill_data)
                if bill_id:
                    self._insert_sponsor(bill_data, bill_id)
                    self._insert_cosponsors(bill_data, bill_id)
                    self._insert_actions(bill_data, bill_id)
                    self._insert_committees(bill_data, bill_id)
                    self._insert_subjects(bill_data, bill_id)
                    self._insert_text_versions(bill_data, bill_id)
                    self._insert_relationships(bill_data, bill_id)
            elif xml_type == 'billStatus':
                # Status update: UPSERT on bill record with status info
                bill_id = self._update_bill_status(bill_data)
                if bill_id:
                    # Update actions if new ones present
                    self._insert_status_actions(bill_data, bill_id)
                    logger.info(f"Updated status for bill {bill_data.get('bill_number')}")
                else:
                    logger.warning(f"Bill not found for status update: {bill_data.get('bill_number')}")
                    return False
            else:
                logger.error(f"Unknown XML type: {xml_type}")
                return False

            self.conn.commit()
            return True

        except Exception as e:
            self.conn.rollback()
            logger.error(f"Failed to insert bill data: {e}")
            return False
        finally:
            self.conn.autocommit = True

    def _insert_main_bill(self, bill_data: Dict[str, Any]) -> Optional[int]:
        """Insert main bill record"""
        query = """
            INSERT INTO master.bill (
                bill_print_no, bill_session_year, title, data_source, congress,
                bill_type, short_title, status_date, sponsor_party, sponsor_state, sponsor_district
            ) VALUES (%s, %s, %s, 'federal', %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (bill_print_no, bill_session_year)
            DO UPDATE SET
                title = EXCLUDED.title,
                congress = EXCLUDED.congress,
                bill_type = EXCLUDED.bill_type,
                short_title = EXCLUDED.short_title,
                status_date = EXCLUDED.status_date,
                sponsor_party = EXCLUDED.sponsor_party,
                sponsor_state = EXCLUDED.sponsor_state,
                sponsor_district = EXCLUDED.sponsor_district
            RETURNING bill_print_no, bill_session_year
        """

        sponsor = bill_data.get('sponsor', {})
        introduced_date = bill_data.get('introduced_date')

        self.cursor.execute(query, (
            bill_data.get('bill_number'),
            bill_data.get('congress'),  # Use congress as session year for federal
            bill_data.get('title'),
            bill_data.get('congress'),
            bill_data.get('bill_type'),
            """

            self.cursor.execute(query, (
                bill_id,
                bill_data.get('congress'),
                action.get('action_date'),
                action.get('chamber'),
                action.get('description'),
                action.get('action_type'),
                action.get('sequence_no')
            ))

    def _insert_committees(self, bill_data: Dict[str, Any], bill_id: str):
        """Insert committee references"""
        committees = bill_data.get('committees', [])
        for committee in committees:
            if committee.get('name'):
                query = """
                    INSERT INTO master.bill_committee (
                        bill_print_no, bill_session_year, committee_name,
                        action_date, data_source
                    ) VALUES (%s, %s, %s, %s, 'federal')
                """

                self.cursor.execute(query, (
                    bill_id,
                    bill_data.get('congress'),
                    committee.get('name'),
                    committee.get('referred_date')
                ))

    def _insert_subjects(self, bill_data: Dict[str, Any], bill_id: str):
        """Insert legislative subjects"""
        subjects = bill_data.get('subjects', [])
        for subject in subjects:
            query = """
                INSERT INTO master.federal_bill_subject (
                    bill_print_no, bill_session_year, subject
                ) VALUES (%s, %s, %s)
            """

            self.cursor.execute(query, (
                bill_id,
                bill_data.get('congress'),
                subject
            ))

    def _insert_text_versions(self, bill_data: Dict[str, Any], bill_id: str):
        """Insert text versions"""
        versions = bill_data.get('text_versions', [])
        for version in versions:
            if version.get('content'):
                query = """
                    INSERT INTO master.federal_bill_text (
                        bill_print_no, bill_session_year, bill_amend_version,
                        version_id, text_format, content
                    ) VALUES (%s, %s, '', %s, %s, %s)
                """

                self.cursor.execute(query, (
                    bill_id,
                    bill_data.get('congress'),
                    version.get('version_id'),
                    version.get('format'),
                    version.get('content')
                ))

    def _insert_relationships(self, bill_data: Dict[str, Any], bill_id: str):
        """Insert bill relationships"""
        relationships = bill_data.get('relationships', [])
        for rel in relationships:
            if rel.get('related_bill'):
                query = """
                    INSERT INTO master.federal_bill_relationship (
                        bill_print_no, bill_session_year, related_bill_print_no,
                        related_session_year, relationship_type
                    ) VALUES (%s, %s, %s, %s, %s)
                """

                self.cursor.execute(query, (
                    bill_id,
                    bill_data.get('congress'),
                    rel.get('related_bill'),
                    bill_data.get('congress'),  # Assume same congress
                    rel.get('type', 'related')
                ))

    def process_directory(self, input_dir: Path, batch_size: int = 100, continue_on_error: bool = True):
        """Process all XML files in directory with batching and error handling"""
        # Detect collection type
        collection_type = input_dir.name.lower()
        is_billstatus = 'billstatus' in collection_type
        is_billsum = 'billsum' in collection_type
        
        xml_files = list(input_dir.glob('**/*.xml'))
        logger.info(f"Found {len(xml_files)} XML files to process ({'BILLSTATUS' if is_billstatus else 'BILLSUM' if is_billsum else 'BILLS'} mode)")

        processed = 0
        errors = 0
        batch = []

        for xml_file in xml_files:
            try:
                if is_billstatus:
                    # BILLSTATUS: typically one large file per congress/session
                    status_data = self._parse_billstatus_xml(xml_file)
                    if status_data:
                        # status_data is list of bill dicts
                        batch.extend(status_data)
                elif is_billsum:
                    # BILLSUM: one file with multiple summaries
                    summary_data = self._parse_billsum_xml(xml_file)
                    if summary_data:
                        batch.extend(summary_data)
                else:
                    # BILLS: individual files
                    bill_data = self.parse_govinfo_xml(xml_file)
                    if bill_data:
                        batch.append(bill_data)
                        
                if len(batch) >= batch_size:
                    success_count = self._process_batch(batch)
                    processed += success_count
                    errors += len(batch) - success_count
                    batch = []
                    logger.info(f"Progress: {processed + errors}/{len(xml_files)} processed")
            except Exception as e:
                logger.error(f"Failed to process {xml_file}: {e}")
                if not continue_on_error:
                    raise
                errors += 1

        # Process remaining batch
        if batch:
            success_count = self._process_batch(batch)
            processed += success_count
            errors += len(batch) - success_count

        logger.info(f"Processing complete: {processed} successful, {errors} errors")

    def _parse_billstatus_xml(self, xml_file: Path) -> Optional[List[Dict[str, Any]]]:
        """Parse BILLSTATUS XML file and extract status data for multiple bills"""
        try:
            tree = ET.parse(xml_file)
            root = tree.getroot()
            
            congress = self._extract_congress(root)
            if not congress:
                logger.warning(f"No congress found in {xml_file}")
                return None

            bills = []
            for bill_elem in root.findall('.//bill'):
                bill_data = {
                    'congress': congress,
                    'bill_number': self._extract_bill_number_from_status(bill_elem),
                    'bill_type': self._extract_bill_type_from_status(bill_elem),
                    'title': self._extract_title_from_status(bill_elem),
                    'introduced_date': self._extract_introduced_date_from_status(bill_elem),
                    'last_action_date': self._extract_last_action_date(bill_elem),
                    'status_code': self._extract_status_code(bill_elem),
                    'sponsor': self._extract_sponsor_from_status(bill_elem),
                    'actions': self._extract_actions_from_status(bill_elem),
                    'data_source': 'govinfo_billstatus'
                }
                
                # Only add if we have a valid bill number
                if bill_data['bill_number']:
                    bills.append(bill_data)
                else:
                    logger.warning(f"Skipping invalid bill in {xml_file}")

            logger.info(f"Parsed {len(bills)} bills from BILLSTATUS file {xml_file}")
            return bills

        except Exception as e:
            logger.error(f"Failed to parse BILLSTATUS XML {xml_file}: {e}")
            return None

    def _extract_bill_number_from_status(self, bill_elem: ET.Element) -> Optional[str]:
        """Extract bill number from BILLSTATUS bill element"""
        number_elem = bill_elem.find('number')
        if number_elem is not None and number_elem.text:
            bill_num = number_elem.text.strip()
            # Convert H.R. 123 to H123 format (consistent with BILLS)
            if '.' in bill_num:
                parts = bill_num.replace('.', '').split()
                if len(parts) >= 2:
                    return f"{parts[0]}{parts[1]}"
        return None

    def _extract_bill_type_from_status(self, bill_elem: ET.Element) -> Optional[str]:
        """Extract bill type from BILLSTATUS"""
        bill_elem = root.find('.//bill')
        if bill_elem is not None:
            type_elem = bill_elem.find('.//type')
            return type_elem.text if type_elem is not None else None
        return None

    def _extract_current_status(self, root: ET.Element) -> Optional[str]:
        """Extract current bill status"""
        status_elem = root.find('.//currentStatus')
        return status_elem.text if status_elem is not None else None

    def _extract_status_date(self, root: ET.Element) -> Optional[datetime]:
        """Extract status update date"""
        date_elem = root.find('.//statusDate')
        if date_elem is not None and date_elem.text:
            try:
                return datetime.fromisoformat(date_elem.text.replace('Z', '+00:00'))
            except ValueError:
                logger.warning(f"Invalid status date format: {date_elem.text}")
        return None

    def _extract_last_action(self, root: ET.Element) -> Optional[Dict[str, Any]]:
        """Extract last action details"""
        last_action_elem = root.find('.//lastAction')
        if last_action_elem is not None:
            return {
                'date': self._extract_date(last_action_elem, './/date'),
                'text': self._extract_text(last_action_elem, './/text'),
                'chamber': self._extract_text(last_action_elem, './/chamber')
            }
        return None

    def _extract_status_actions(self, root: ET.Element) -> List[Dict[str, Any]]:
        """Extract status history actions"""
        actions = []
        action_elems = root.findall('.//action')
        for action_elem in action_elems:
            action = {
                'action_date': self._extract_date(action_elem, './/date'),
                'chamber': self._extract_text(action_elem, './/chamber'),
                'description': self._extract_text(action_elem, './/text'),
                'status_type': self._extract_text(action_elem, './/statusType')
            }
            actions.append(action)
        return actions

    def _extract_summary(self, root: ET.Element) -> Optional[str]:
        """Extract bill summary from status"""
        summary_elem = root.find('.//summary')
        return summary_elem.text if summary_elem is not None else None

    def _extract_text(self, element: ET.Element, xpath: str) -> Optional[str]:
        """Extract text content from XML element"""
        found = element.find(xpath)
        return found.text if found is not None else None

    def _extract_date(self, element: ET.Element, xpath: str) -> Optional[datetime]:
        """Extract and parse date from XML element"""
        text = self._extract_text(element, xpath)
        if text:
            try:
                return datetime.fromisoformat(text.replace('Z', '+00:00'))
            except ValueError:
                logger.warning(f"Invalid date format: {text}")
        return None

    def _extract_int(self, element: ET.Element, xpath: str) -> Optional[int]:
        """Extract and parse integer from XML element"""
        text = self._extract_text(element, xpath)
        if text:
            try:
                return int(text)
            except ValueError:
                logger.warning(f"Invalid integer format: {text}")
        return None

    def insert_bill_data(self, bill_data: Dict[str, Any]) -> bool:
        """Insert or update bill data based on XML type"""
        try:
            self.conn.autocommit = False
            xml_type = bill_data.get('xml_type')

            if xml_type == 'bill':
                # Existing bill insertion logic
                bill_id = self._insert_main_bill(bill_data)
                if bill_id:
                    self._insert_sponsor(bill_data, bill_id)
                    self._insert_cosponsors(bill_data, bill_id)
                    self._insert_actions(bill_data, bill_id)
                    self._insert_committees(bill_data, bill_id)
                    self._insert_subjects(bill_data, bill_id)
                    self._insert_text_versions(bill_data, bill_id)
                    self._insert_relationships(bill_data, bill_id)
            elif xml_type == 'billStatus':
                # Status update: UPSERT on bill record with status info
                bill_id = self._update_bill_status(bill_data)
                if bill_id:
                    # Update actions if new ones present
                    self._insert_status_actions(bill_data, bill_id)
                    logger.info(f"Updated status for bill {bill_data.get('bill_number')}")
                else:
                    logger.warning(f"Bill not found for status update: {bill_data.get('bill_number')}")
                    return False
            else:
                logger.error(f"Unknown XML type: {xml_type}")
                return False

            self.conn.commit()
            return True

        except Exception as e:
            self.conn.rollback()
            logger.error(f"Failed to insert bill data: {e}")
            return False
        finally:
            self.conn.autocommit = True

    def _insert_main_bill(self, bill_data: Dict[str, Any]) -> Optional[int]:
        """Insert main bill record"""
        query = """
            INSERT INTO master.bill (
                bill_print_no, bill_session_year, title, data_source, congress,
                bill_type, short_title, status_date, sponsor_party, sponsor_state, sponsor_district
            ) VALUES (%s, %s, %s, 'federal', %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (bill_print_no, bill_session_year)
            DO UPDATE SET
                title = EXCLUDED.title,
                congress = EXCLUDED.congress,
                bill_type = EXCLUDED.bill_type,
                short_title = EXCLUDED.short_title,
                status_date = EXCLUDED.status_date,
                sponsor_party = EXCLUDED.sponsor_party,
                sponsor_state = EXCLUDED.sponsor_state,
                sponsor_district = EXCLUDED.sponsor_district
            RETURNING bill_print_no, bill_session_year
        """

        sponsor = bill_data.get('sponsor', {})
        introduced_date = bill_data.get('introduced_date')

        self.cursor.execute(query, (
            bill_data.get('bill_number'),
            bill_data.get('congress'),  # Use congress as session year for federal
            bill_data.get('title'),
            bill_data.get('congress'),
            bill_data.get('bill_type'),
            """

            self.cursor.execute(query, (
                bill_id,
                bill_data.get('congress'),
                action.get('action_date'),
                action.get('chamber'),
                action.get('description'),
                action.get('action_type'),
                action.get('sequence_no')
            ))

    def _insert_committees(self, bill_data: Dict[str, Any], bill_id: str):
        """Insert committee references"""
        committees = bill_data.get('committees', [])
        for committee in committees:
            if committee.get('name'):
                query = """
                    INSERT INTO master.bill_committee (
                        bill_print_no, bill_session_year, committee_name,
                        action_date, data_source
                    ) VALUES (%s, %s, %s, %s, 'federal')
                """

                self.cursor.execute(query, (
                    bill_id,
                    bill_data.get('congress'),
                    committee.get('name'),
                    committee.get('referred_date')
                ))

    def _insert_subjects(self, bill_data: Dict[str, Any], bill_id: str):
        """Insert legislative subjects"""
        subjects = bill_data.get('subjects', [])
        for subject in subjects:
            query = """
                INSERT INTO master.federal_bill_subject (
                    bill_print_no, bill_session_year, subject
                ) VALUES (%s, %s, %s)
            """

            self.cursor.execute(query, (
                bill_id,
                bill_data.get('congress'),
                subject
            ))

    def _insert_text_versions(self, bill_data: Dict[str, Any], bill_id: str):
        """Insert text versions"""
        versions = bill_data.get('text_versions', [])
        for version in versions:
            if version.get('content'):
                query = """
                    INSERT INTO master.federal_bill_text (
                        bill_print_no, bill_session_year, bill_amend_version,
                        version_id, text_format, content
                    ) VALUES (%s, %s, '', %s, %s, %s)
                """

                self.cursor.execute(query, (
                    bill_id,
                    bill_data.get('congress'),
                    version.get('version_id'),
                    version.get('format'),
                    version.get('content')
                ))

    def _insert_relationships(self, bill_data: Dict[str, Any], bill_id: str):
        """Insert bill relationships"""
        relationships = bill_data.get('relationships', [])
        for rel in relationships:
            if rel.get('related_bill'):
                query = """
                    INSERT INTO master.federal_bill_relationship (
                        bill_print_no, bill_session_year, related_bill_print_no,
                        related_session_year, relationship_type
                    ) VALUES (%s, %s, %s, %s, %s)
                """

                self.cursor.execute(query, (
                    bill_id,
                    bill_data.get('congress'),
                    rel.get('related_bill'),
                    bill_data.get('congress'),  # Assume same congress
                    rel.get('type', 'related')
                ))

    def process_directory(self, input_dir: Path, batch_size: int = 100, continue_on_error: bool = True):
        """Process all XML files in directory with batching and error handling"""
        # Detect collection type
        collection_type = input_dir.name.lower()
        is_billstatus = 'billstatus' in collection_type
        is_billsum = 'billsum' in collection_type
        
        xml_files = list(input_dir.glob('**/*.xml'))
        logger.info(f"Found {len(xml_files)} XML files to process ({'BILLSTATUS' if is_billstatus else 'BILLSUM' if is_billsum else 'BILLS'} mode)")

        processed = 0
        errors = 0
        batch = []

        for xml_file in xml_files:
            try:
                if is_billstatus:
                    # BILLSTATUS: typically one large file per congress/session
                    status_data = self._parse_billstatus_xml(xml_file)
                    if status_data:
                        # status_data is list of bill dicts
                        batch.extend(status_data)
                elif is_billsum:
                    # BILLSUM: one file with multiple summaries
                    summary_data = self._parse_billsum_xml(xml_file)
                    if summary_data:
                        batch.extend(summary_data)
                else:
                    # BILLS: individual files
                    bill_data = self.parse_govinfo_xml(xml_file)
                    if bill_data:
                        batch.append(bill_data)
                        
                if len(batch) >= batch_size:
                    success_count = self._process_batch(batch)
                    processed += success_count
                    errors += len(batch) - success_count
                    batch = []
                    logger.info(f"Progress: {processed + errors}/{len(xml_files)} processed")
            except Exception as e:
                logger.error(f"Failed to process {xml_file}: {e}")
                if not continue_on_error:
                    raise
                errors += 1

        # Process remaining batch
        if batch:
            success_count = self._process_batch(batch)
            processed += success_count
            errors += len(batch) - success_count

        logger.info(f"Processing complete: {processed} successful, {errors} errors")

    def _parse_billstatus_xml(self, xml_file: Path) -> Optional[List[Dict[str, Any]]]:
        """Parse BILLSTATUS XML file and extract status data for multiple bills"""
        try:
            tree = ET.parse(xml_file)
            root = tree.getroot()
            
            congress = self._extract_congress(root)
            if not congress:
                logger.warning(f"No congress found in {xml_file}")
                return None

            bills = []
            for bill_elem in root.findall('.//bill'):
                bill_data = {
                    'congress': congress,
                    'bill_number': self._extract_bill_number_from_status(bill_elem),
                    'bill_type': self._extract_bill_type_from_status(bill_elem),
                    'title': self._extract_title_from_status(bill_elem),
                    'introduced_date': self._extract_introduced_date_from_status(bill_elem),
                    'last_action_date': self._extract_last_action_date(bill_elem),
                    'status_code': self._extract_status_code(bill_elem),
                    'sponsor': self._extract_sponsor_from_status(bill_elem),
                    'actions': self._extract_actions_from_status(bill_elem),
                    'data_source': 'govinfo_billstatus'
                }
                
                # Only add if we have a valid bill number
                if bill_data['bill_number']:
                    bills.append(bill_data)
                else:
                    logger.warning(f"Skipping invalid bill in {xml_file}")

            logger.info(f"Parsed {len(bills)} bills from BILLSTATUS file {xml_file}")
            return bills

        except Exception as e:
            logger.error(f"Failed to parse BILLSTATUS XML {xml_file}: {e}")
            return None

    def _extract_bill_number_from_status(self, bill_elem: ET.Element) -> Optional[str]:
        """Extract bill number from BILLSTATUS bill element"""
        number_elem = bill_elem.find('number')
        if number_elem is not None and number_elem.text:
            bill_num = number_elem.text.strip()
            # Convert H.R. 123 to H123 format (consistent with BILLS)
            if '.' in bill_num:
                parts = bill_num.replace('.', '').split()
                if len(parts) >= 2:
                    return f"{parts[0]}{parts[1]}"
        return None

    def _extract_bill_type_from_status(self, bill_elem: ET.Element) -> Optional[str]:
        """Extract bill type from BILLSTATUS"""
        bill_elem = root.find('.//bill')
        if bill_elem is not None:
            type_elem = bill_elem.find('.//type')
            return type_elem.text if type_elem is not None else None
        return None

    def _extract_current_status(self, root: ET.Element) -> Optional[str]:
        """Extract current bill status"""
        status_elem = root.find('.//currentStatus')
        return status_elem.text if status_elem is not None else None

    def _extract_status_date(self, root: ET.Element) -> Optional[datetime]:
        """Extract status update date"""
        date_elem = root.find('.//statusDate')
        if date_elem is not None and date_elem.text:
            try:
                return datetime.fromisoformat(date_elem.text.replace('Z', '+00:00'))
            except ValueError:
                logger.warning(f"Invalid status date format: {date_elem.text}")
        return None

    def _extract_last_action(self, root: ET.Element) -> Optional[Dict[str, Any]]:
        """Extract last action details"""
        last_action_elem = root.find('.//lastAction')
        if last_action_elem is not None:
            return {
                'date': self._extract_date(last_action_elem, './/date'),
                'text': self._extract_text(last_action_elem, './/text'),
                'chamber': self._extract_text(last_action_elem, './/chamber')
            }
        return None

    def _extract_status_actions(self, root: ET.Element) -> List[Dict[str, Any]]:
        """Extract status history actions"""
        actions = []
        action_elems = root.findall('.//action')
        for action_elem in action_elems:
            action = {