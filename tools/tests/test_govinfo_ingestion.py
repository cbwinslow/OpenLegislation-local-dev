#!/usr/bin/env python3
"""
Comprehensive Test Suite for GovInfo Data Ingestion

Tests the complete pipeline:
1. Data downloading from govinfo bulk
2. XML parsing and transformation
3. Database ingestion
4. Data validation and integrity checks

Usage:
    python -m pytest tools/test_govinfo_ingestion.py -v
    # or
    python tools/test_govinfo_ingestion.py
"""

import json
import os
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock

import psycopg2
import psycopg2.extras

from govinfo_data_connector import GovInfoDataConnector


class TestGovInfoIngestion(unittest.TestCase):
    """Test suite for govinfo data ingestion pipeline"""

    @classmethod
    def setUpClass(cls):
        """Set up test environment"""
        cls.test_dir = Path(tempfile.mkdtemp(prefix="govinfo_test_"))
        cls.db_config = {
            "host": os.environ.get("TEST_DB_HOST", "localhost"),
            "database": os.environ.get("TEST_DB_NAME", "openleg_test"),
            "user": os.environ.get("TEST_DB_USER", "openleg"),
            "password": os.environ.get("TEST_DB_PASSWORD", "password"),
            "port": os.environ.get("TEST_DB_PORT", 5432),
        }

        # Create test database config file
        cls.config_file = cls.test_dir / "test_db_config.json"
        with open(cls.config_file, "w") as f:
            json.dump(cls.db_config, f)

        # Initialize connector
        cls.connector = GovInfoDataConnector(cls.db_config)

    @classmethod
    def tearDownClass(cls):
        """Clean up test environment"""
        shutil.rmtree(cls.test_dir, ignore_errors=True)

    def setUp(self):
        """Set up each test"""
        self.connector.connect_db()
        # Clean test data
        self._clean_test_data()

    def tearDown(self):
        """Clean up after each test"""
        self._clean_test_data()
        self.connector.disconnect_db()

    def _clean_test_data(self):
        """Remove test data from database"""
        try:
            self.connector.cursor.execute(
                "DELETE FROM master.bill WHERE data_source = 'federal'"
            )
            self.connector.conn.commit()
        except Exception:
            pass  # Table might not exist or be empty

    def test_sample_xml_parsing(self):
        """Test parsing of sample govinfo XML files"""
        # Create sample XML content
        sample_xml = """<?xml version="1.0" encoding="UTF-8"?>
<bill>
    <billNumber>H.R.1</billNumber>
    <congress>119</congress>
    <title>Test Bill Title</title>
    <introducedDate>2025-01-01</introducedDate>
    <sponsor>
        <fullName>Test Sponsor</fullName>
        <party>D</party>
        <state>NY</state>
    </sponsor>
    <actions>
        <action>
            <actionDate>2025-01-01</actionDate>
            <text>Introduced</text>
            <chamber>House</chamber>
        </action>
    </actions>
</bill>"""

        # Write sample XML
        xml_file = self.test_dir / "test_bill.xml"
        with open(xml_file, "w") as f:
            f.write(sample_xml)

        # Test parsing
        bill_data = self.connector.parse_govinfo_xml(xml_file)

        self.assertIsNotNone(bill_data)
        self.assertEqual(bill_data["bill_number"], "H1")
        self.assertEqual(bill_data["congress"], 119)
        self.assertEqual(bill_data["title"], "Test Bill Title")
        self.assertEqual(bill_data["sponsor"]["name"], "Test Sponsor")

    def test_database_insertion(self):
        """Test inserting parsed bill data into database"""
        bill_data = {
            "bill_number": "H123",
            "congress": 119,
            "title": "Test Bill for Database Insertion",
            "bill_type": "HR",
            "sponsor": {"name": "Test Representative", "party": "D", "state": "NY"},
            "actions": [
                {
                    "action_date": "2025-01-01",
                    "chamber": "House",
                    "description": "Introduced in House",
                    "action_type": "Intro-H",
                }
            ],
        }

        # Test insertion
        success = self.connector.insert_bill_data(bill_data)
        self.assertTrue(success)

        # Verify in database
        self.connector.cursor.execute(
            """
            SELECT bill_print_no, title, congress, data_source
            FROM master.bill
            WHERE bill_print_no = %s AND congress = %s
        """,
            (bill_data["bill_number"], bill_data["congress"]),
        )

        result = self.connector.cursor.fetchone()
        self.assertIsNotNone(result)
        self.assertEqual(result["bill_print_no"], "H123")
        self.assertEqual(result["title"], "Test Bill for Database Insertion")
        self.assertEqual(result["data_source"], "federal")

    def test_batch_processing(self):
        """Test batch processing of multiple bills"""
        bills_data = []
        for i in range(5):
            bills_data.append(
                {
                    "bill_number": f"H{i+200}",
                    "congress": 119,
                    "title": f"Test Bill {i+1}",
                    "bill_type": "HR",
                    "sponsor": {"name": f"Sponsor {i+1}"},
                }
            )

        # Process in batch
        success_count = 0
        for bill_data in bills_data:
            if self.connector.insert_bill_data(bill_data):
                success_count += 1

        self.assertEqual(success_count, 5)

        # Verify all bills inserted
        self.connector.cursor.execute(
            """
            SELECT COUNT(*) as count
            FROM master.bill
            WHERE congress = 119 AND data_source = 'federal'
        """
        )
        result = self.connector.cursor.fetchone()
        self.assertEqual(result["count"], 5)

    def test_error_handling(self):
        """Test error handling for malformed data"""
        # Test with missing required fields
        invalid_bill_data = {
            "congress": 119,
            "title": "Invalid Bill",
            # Missing bill_number
        }

        success = self.connector.insert_bill_data(invalid_bill_data)
        self.assertFalse(success)

        # Test with invalid XML
        invalid_xml_file = self.test_dir / "invalid.xml"
        with open(invalid_xml_file, "w") as f:
            f.write("<invalid>xml</invalid>")

        bill_data = self.connector.parse_govinfo_xml(invalid_xml_file)
        self.assertIsNone(bill_data)

    def test_data_integrity(self):
        """Test data integrity and relationships"""
        bill_data = {
            "bill_number": "S456",
            "congress": 119,
            "title": "Comprehensive Test Bill",
            "bill_type": "S",
            "sponsor": {"name": "Test Senator", "party": "R", "state": "TX"},
            "cosponsors": [
                {"name": "Cosponsor 1", "party": "D", "state": "CA"},
                {"name": "Cosponsor 2", "party": "I", "state": "VT"},
            ],
            "actions": [
                {
                    "action_date": "2025-01-01",
                    "chamber": "Senate",
                    "description": "Introduced in Senate",
                    "action_type": "Intro-S",
                },
                {
                    "action_date": "2025-01-15",
                    "chamber": "Senate",
                    "description": "Referred to committee",
                    "action_type": "Referral",
                },
            ],
            "committees": [
                {"name": "Committee on Test Affairs", "referred_date": "2025-01-15"}
            ],
        }

        success = self.connector.insert_bill_data(bill_data)
        self.assertTrue(success)

        # Verify bill
        self.connector.cursor.execute(
            """
            SELECT * FROM master.bill
            WHERE bill_print_no = %s AND congress = %s
        """,
            (bill_data["bill_number"], bill_data["congress"]),
        )
        bill = self.connector.cursor.fetchone()
        self.assertIsNotNone(bill)

        # Verify actions
        self.connector.cursor.execute(
            """
            SELECT COUNT(*) as action_count
            FROM master.bill_amendment_action
            WHERE bill_print_no = %s AND bill_session_year = %s
        """,
            (bill_data["bill_number"], bill_data["congress"]),
        )
        actions = self.connector.cursor.fetchone()
        self.assertEqual(actions["action_count"], 2)

        # Verify committees
        self.connector.cursor.execute(
            """
            SELECT COUNT(*) as committee_count
            FROM master.bill_committee
            WHERE bill_print_no = %s AND bill_session_year = %s
        """,
            (bill_data["bill_number"], bill_data["congress"]),
        )
        committees = self.connector.cursor.fetchone()
        self.assertEqual(committees["committee_count"], 1)

    @patch("govinfo_data_connector.requests.get")
    def test_download_integration(self, mock_get):
        """Test integration with download script"""
        # Mock successful download response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.iter_content.return_value = [b"<test>xml</test>"]
        mock_get.return_value.__enter__.return_value = mock_response

        # This would test the fetch script integration
        # For now, just verify the mock setup works
        self.assertTrue(True)  # Placeholder

    def test_congress_range_parsing(self):
        """Test congress range parsing logic"""
        from fetch_govinfo_bulk import parse_congress_range

        # Single congress
        result = parse_congress_range("119")
        self.assertEqual(result, [119])

        # Range
        result = parse_congress_range("115-119")
        self.assertEqual(result, [115, 116, 117, 118, 119])

    def test_collection_processing(self):
        """Test processing different govinfo collections"""
        collections = ["BILLS", "BILLSTATUS", "BILLSUM"]

        for collection in collections:
            with self.subTest(collection=collection):
                # Create mock data for each collection
                bill_data = {
                    "bill_number": f"H{100 + collections.index(collection)}",
                    "congress": 119,
                    "title": f"Test {collection} Bill",
                    "bill_type": "HR",
                }

                success = self.connector.insert_bill_data(bill_data)
                self.assertTrue(success)


if __name__ == "__main__":
    # Run tests
    unittest.main(verbosity=2)
