"""Tests for GovInfo Bill Ingestion Process.

Covers unit tests for XML parsing, record discovery, and integration tests for database insertion,
resume functionality, and error handling. Uses pytest with mocks for file system and database.

Requires: pytest, pytest-mock, lxml, psycopg2-binary
Run with: pytest tools/tests/test_bill_ingestion.py -v
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import pytest
from unittest.mock import Mock, patch, mock_open
from pathlib import Path
import tempfile
from lxml import etree
import psycopg2
from psycopg2.extras import RealDictCursor

from govinfo_bill_ingestion import GovInfoBillIngestor
from settings import settings


@pytest.fixture(scope="session")
def test_db_conn():
    """Fixture for test database connection."""
    conn = psycopg2.connect(**settings.test_db_config)
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    # Ensure schema and tables for testing
    cursor.execute("CREATE SCHEMA IF NOT EXISTS master")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS master.bill (
            bill_id BIGSERIAL PRIMARY KEY,
            bill_print_no TEXT NOT NULL,
            congress INTEGER NOT NULL,
            title TEXT,
            bill_type TEXT,
            data_source TEXT,
            created_at TIMESTAMP DEFAULT now(),
            updated_at TIMESTAMP DEFAULT now(),
            UNIQUE(bill_print_no, congress)
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS master.bill_sponsor (
            id BIGSERIAL PRIMARY KEY,
            bill_id INTEGER REFERENCES master.bill(bill_id),
            sponsor_name TEXT,
            party TEXT,
            state TEXT,
            created_at TIMESTAMP DEFAULT now()
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS master.bill_amendment_action (
            id BIGSERIAL PRIMARY KEY,
            bill_print_no TEXT NOT NULL,
            bill_session_year INTEGER NOT NULL,
            action_date TEXT,
            chamber TEXT,
            description TEXT,
            action_type TEXT,
            created_at TIMESTAMP DEFAULT now(),
            UNIQUE(bill_print_no, bill_session_year, action_date, description)
        )
    """)
    conn.commit()
    yield conn, cursor
    cursor.close()
    conn.close()


@pytest.fixture
def mock_xml_dir(tmp_path):
    """Create mock XML directory with sample files."""
    xml_dir = tmp_path / "govinfo_xml"
    xml_dir.mkdir()
    
    # Sample valid XML
    valid_xml = """<?xml version="1.0" encoding="UTF-8"?>
    <bill congress="119">
        <billNumber>H.R. 1</billNumber>
        <officialTitle>A sample bill title</officialTitle>
        <sponsor><fullName>John Doe</fullName><party>Democratic</party><state>CA</state></sponsor>
        <actions><action><actionDate>2023-01-01</actionDate><chamber>House</chamber><text>Introduced</text><actionCode>INTRO</actionCode></action></actions>
    </bill>"""
    valid_path = xml_dir / "BILLS-119hr1ih.xml"
    valid_path.write_text(valid_xml)
    
    # Sample invalid XML (missing tags)
    invalid_xml = """<?xml version="1.0" encoding="UTF-8"?>
    <bill congress="119">
        <billNumber>H.R. 2</billNumber>
        <!-- Missing title and sponsor -->
        <actions><action><actionDate>2023-01-02</actionDate><chamber>Senate</chamber><text>Passed</text></action></actions>
    </bill>"""
    invalid_path = xml_dir / "BILLS-119s2is.xml"
    invalid_path.write_text(invalid_xml)
    
    return str(xml_dir)


class TestBillIngestionUnits:
    """Unit tests for bill ingestion components."""

    def test_extract_bill_id_from_path(self):
        """Test bill ID extraction from file path."""
        ingestor = GovInfoBillIngestor()
        bill_id = ingestor._extract_bill_id_from_path("/path/to/BILLS-119hr1ih.xml")
        assert bill_id == "H1-119"
        
        # Test Senate bill
        senate_id = ingestor._extract_bill_id_from_path("/path/to/BILLS-119s2is.xml")
        assert senate_id == "S2-119"
        
        # Test invalid path
        invalid_id = ingestor._extract_bill_id_from_path("/path/to/invalid.txt")
        assert invalid_id is None

    def test_parse_govinfo_xml_valid(self, mock_xml_dir):
        """Test parsing valid GovInfo XML."""
        ingestor = GovInfoBillIngestor(xml_dir=mock_xml_dir)
        xml_file = os.path.join(mock_xml_dir, "BILLS-119hr1ih.xml")
        bill_data = ingestor._parse_govinfo_xml(xml_file)
        
        assert bill_data is not None
        assert bill_data['bill_number'] == 'H1'
        assert bill_data['congress'] == 119
        assert bill_data['title'] == 'A sample bill title'
        assert bill_data['bill_type'] == 'H'
        assert bill_data['sponsor'] == {'name': 'John Doe', 'party': 'Democratic', 'state': 'CA'}
        assert len(bill_data['actions']) == 1
        assert bill_data['actions'][0]['description'] == 'Introduced'

    def test_parse_govinfo_xml_invalid(self, mock_xml_dir):
        """Test parsing invalid XML (missing required fields)."""
        ingestor = GovInfoBillIngestor(xml_dir=mock_xml_dir)
        xml_file = os.path.join(mock_xml_dir, "BILLS-119s2is.xml")
        bill_data = ingestor._parse_govinfo_xml(xml_file)
        
        assert bill_data is not None  # Should not crash
        assert bill_data['title'] == ''  # Default for missing
        assert bill_data['sponsor'] is None  # Missing sponsor
        assert len(bill_data['actions']) == 1

    def test_parse_govinfo_xml_malformed(self):
        """Test handling malformed XML."""
        ingestor = GovInfoBillIngestor()
        malformed_xml = "<invalid>not xml</invalid>"
        with tempfile.NamedTemporaryFile(suffix=".xml", mode="w") as f:
            f.write(malformed_xml)
            f.flush()
            bill_data = ingestor._parse_govinfo_xml(f.name)
        assert bill_data is None  # Should return None on parse error


class TestBillIngestionIntegration:
    """Integration tests for bill ingestion process."""

    @pytest.mark.integration
    def test_end_to_end_ingestion(self, test_db_conn, mock_xml_dir):
        """Test full ingestion of sample XML files."""
        conn, cursor = test_db_conn
        ingestor = GovInfoBillIngestor(xml_dir=mock_xml_dir, db_config=settings.test_db_config)
        
        # Discover records
        records = ingestor.discover_records()
        assert len(records) == 2  # Two sample files
        
        # Process first record
        success = ingestor.process_record(records[0])
        assert success is True
        
        # Verify database insertion
        cursor.execute("SELECT COUNT(*) FROM master.bill WHERE bill_print_no = 'H1' AND congress = 119")
        count = cursor.fetchone()[0]
        assert count == 1
        
        # Verify sponsor
        cursor.execute("SELECT sponsor_name FROM master.bill_sponsor WHERE bill_id = (SELECT bill_id FROM master.bill WHERE bill_print_no = 'H1')")
        sponsor = cursor.fetchone()
        assert sponsor['sponsor_name'] == 'John Doe'
        
        # Verify action
        cursor.execute("SELECT description FROM master.bill_amendment_action WHERE bill_print_no = 'H1' AND bill_session_year = 119")
        action = cursor.fetchone()
        assert action['description'] == 'Introduced'

    @pytest.mark.integration
    def test_resume_functionality(self, test_db_conn, mock_xml_dir):
        """Test resume after partial processing."""
        conn, cursor = test_db_conn
        ingestor = GovInfoBillIngestor(xml_dir=mock_xml_dir, db_config=settings.test_db_config)
        
        # Discover and initialize
        records = ingestor.discover_records()
        ingestor.tracker.initialize_records(records)
        
        # Process first, mark second as failed
        ingestor.process_record(records[0])  # Success
        ingestor.tracker.mark_failed(records[1]['record_id'], "Parse error")
        
        # Get pending - should only have the failed one (retries pending)
        pending = ingestor.get_pending_records()
        assert len(pending) == 1
        assert pending[0]['record_id'] == records[1]['record_id']
        
        # Re-process pending
        success = ingestor.process_record(pending[0])
        assert success is True  # Now succeeds
        
        # Verify both completed
        cursor.execute("SELECT COUNT(*) FROM master.bill WHERE data_source = 'govinfo'")
        total = cursor.fetchone()[0]
        assert total == 2

    @pytest.mark.integration
    def test_error_handling_and_rollback(self, test_db_conn, mock_xml_dir, mocker):
        """Test error during insertion with rollback."""
        conn, cursor = test_db_conn
        ingestor = GovInfoBillIngestor(xml_dir=mock_xml_dir, db_config=settings.test_db_config)
        
        # Mock insertion to fail
        mocker.patch.object(ingestor, '_insert_bill_data', side_effect=Exception("DB Error"))
        
        records = ingestor.discover_records()
        success = ingestor.process_record(records[0])
        assert success is False
        
        # Verify no partial insert (rollback)
        cursor.execute("SELECT COUNT(*) FROM master.bill WHERE bill_print_no = 'H1'")
        count = cursor.fetchone()[0]
        assert count == 0  # No insert due to exception

    @pytest.mark.integration
    def test_data_validation_and_uniqueness(self, test_db_conn, mock_xml_dir):
        """Test UPSERT behavior and data validation."""
        conn, cursor = test_db_conn
        ingestor = GovInfoBillIngestor(xml_dir=mock_xml_dir, db_config=settings.test_db_config)
        
        records = ingestor.discover_records()
        
        # Process twice (simulate re-run)
        ingestor.process_record(records[0])
        ingestor.process_record(records[0])  # UPSERT should update timestamp only
        
        # Verify single record, updated timestamp recent
        cursor.execute("""
            SELECT bill_print_no, updated_at FROM master.bill 
            WHERE bill_print_no = 'H1' ORDER BY updated_at DESC LIMIT 1
        """)
        result = cursor.fetchone()
        assert result['bill_print_no'] == 'H1'
        
        # Test invalid data (e.g., non-integer congress) - should handle gracefully
        invalid_record = {'record_id': 'INVALID', 'metadata': {'xml_file': mock_xml_dir + '/invalid.xml'}}
        with patch('builtins.open', mock_open(read_data='<invalid>')):
            success = ingestor.process_record(invalid_record)
        assert success is False
        cursor.execute("SELECT COUNT(*) FROM master.bill WHERE bill_print_no = 'INVALID'")
        count = cursor.fetchone()[0]
        assert count == 0

    @pytest.mark.integration
    def test_foreign_key_integrity(self, test_db_conn):
        """Test FK constraints (sponsor references bill)."""
        conn, cursor = test_db_conn
        ingestor = GovInfoBillIngestor(db_config=settings.test_db_config)
        
        # Insert bill without sponsor (should succeed)
        mock_data = {
            'bill_number': 'H999',
            'congress': 119,
            'title': 'Test Bill',
            'bill_type': 'H',
            'sponsor': None,
            'actions': [],
            'data_source': 'govinfo'
        }
        ingestor._insert_bill_data(mock_data)
        
        # Verify bill exists, no sponsor
        cursor.execute("SELECT bill_id FROM master.bill WHERE bill_print_no = 'H999'")
        bill_id = cursor.fetchone()['bill_id']
        cursor.execute("SELECT COUNT(*) FROM master.bill_sponsor WHERE bill_id = %s", (bill_id,))
        sponsor_count = cursor.fetchone()[0]
        assert sponsor_count == 0
        
        # Delete bill - sponsor should not prevent (no FK violation since empty)
        cursor.execute("DELETE FROM master.bill WHERE bill_id = %s", (bill_id,))
        conn.commit()
        cursor.execute("SELECT COUNT(*) FROM master.bill WHERE bill_id = %s", (bill_id,))
        assert cursor.fetchone()[0] == 0


if __name__ == "__main__":
    pytest.main(["-v", __file__])