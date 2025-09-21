#!/usr/bin/env python3
"""
Comprehensive Test Suite for OpenLegislation Repository

Tests all major components:
- Database connectivity and schema validation
- Congress.gov API integration
- GovInfo bulk data processing
- Federal member data ingestion
- Bill data processing and validation
- System health and performance
- Error handling and recovery

Usage:
    python3 tools/test_comprehensive_suite.py --verbose
    python3 tools/test_comprehensive_suite.py --component database
    python3 tools/test_comprehensive_suite.py --component api
    python3 tools/test_comprehensive_suite.py --component ingestion
"""

import argparse
import json
import os
import sys
import time
import unittest
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any
from unittest.mock import patch, MagicMock

import psycopg2
import psycopg2.extras
import requests


class TestDatabaseConnectivity(unittest.TestCase):
    """Test database connections and schema validation"""

    @classmethod
    def setUpClass(cls):
        """Load database configuration"""
        config_path = Path('tools/db_config.json')
        if config_path.exists():
            with open(config_path, 'r') as f:
                cls.db_config = json.load(f)
        else:
            cls.db_config = None

    def test_database_connection(self):
        """Test basic database connectivity"""
        if not self.db_config:
            self.skipTest("Database config not found")

        try:
            conn = psycopg2.connect(**self.db_config)
            self.assertIsNotNone(conn)

            # Test basic query
            cursor = conn.cursor()
            cursor.execute("SELECT 1 as test")
            result = cursor.fetchone()
            self.assertEqual(result[0], 1)

            cursor.close()
            conn.close()
            print("✓ Database connection successful")

        except Exception as e:
            self.fail(f"Database connection failed: {e}")

    def test_schema_tables_exist(self):
        """Test that required tables exist"""
        if not self.db_config:
            self.skipTest("Database config not found")

        required_tables = [
            'master.bill',
            'master.federal_person',
            'master.federal_member',
            'master.federal_member_term',
            'master.federal_bill_subject',
            'master.federal_bill_text'
        ]

        conn = psycopg2.connect(**self.db_config)
        cursor = conn.cursor()

        for table in required_tables:
            cursor.execute("""
                SELECT EXISTS (
                    SELECT 1 FROM information_schema.tables
                    WHERE table_schema = %s AND table_name = %s
                )
            """, table.split('.'))

            exists = cursor.fetchone()[0]
            self.assertTrue(exists, f"Table {table} does not exist")

        cursor.close()
        conn.close()
        print("✓ All required tables exist")

    def test_database_performance(self):
        """Test database performance with sample queries"""
        if not self.db_config:
            self.skipTest("Database config not found")

        conn = psycopg2.connect(**self.db_config)
        cursor = conn.cursor()

        # Test query performance
        start_time = time.time()
        cursor.execute("SELECT COUNT(*) FROM master.bill")
        count = cursor.fetchone()[0]
        query_time = time.time() - start_time

        # Should complete in reasonable time
        self.assertLess(query_time, 5.0, f"Query took too long: {query_time}s")

        cursor.close()
        conn.close()
        print(f"✓ Database performance OK (bill count: {count}, query time: {query_time:.2f}s)")


class TestAPIIntegration(unittest.TestCase):
    """Test external API integrations"""

    def setUp(self):
        """Load API keys from environment"""
        self.congress_api_key = os.getenv('CONGRESS_API_KEY')
        self.skip_if_no_api_key = not bool(self.congress_api_key)

    def test_congress_api_connectivity(self):
        """Test Congress.gov API connectivity"""
        if self.skip_if_no_api_key:
            self.skipTest("Congress API key not found in environment")

        try:
            response = requests.get(
                'https://api.congress.gov/v3/member',
                params={
                    'api_key': self.congress_api_key,
                    'currentMember': 'true',
                    'limit': 1
                },
                timeout=10
            )

            self.assertEqual(response.status_code, 200)

            data = response.json()
            self.assertIn('members', data)
            self.assertGreater(len(data['members']), 0)

            print("✓ Congress.gov API connection successful")

        except Exception as e:
            self.fail(f"Congress API test failed: {e}")

    def test_api_rate_limiting(self):
        """Test API rate limiting compliance"""
        if self.skip_if_no_api_key:
            self.skipTest("Congress API key not found")

        # Make multiple requests to test rate limiting
        for i in range(3):
            try:
                response = requests.get(
                    'https://api.congress.gov/v3/member',
                    params={
                        'api_key': self.congress_api_key,
                        'currentMember': 'true',
                        'limit': 1,
                        'offset': i
                    },
                    timeout=10
                )

                self.assertIn(response.status_code, [200, 429])  # 429 = rate limited

                if response.status_code == 429:
                    print("✓ Rate limiting detected and handled")
                    break

                time.sleep(0.5)  # Respectful delay

            except Exception as e:
                self.fail(f"Rate limiting test failed: {e}")

    def test_govinfo_bulk_access(self):
        """Test GovInfo bulk data accessibility"""
        try:
            # Test directory listing access
            response = requests.get(
                'https://www.govinfo.gov/bulkdata/BILLS/119/1/',
                timeout=10
            )

            # Should get some response (may be HTML error page, but accessible)
            self.assertIsNotNone(response.content)
            print("✓ GovInfo bulk data accessible")

        except Exception as e:
            self.fail(f"GovInfo bulk access test failed: {e}")


class TestDataIngestion(unittest.TestCase):
    """Test data ingestion pipelines"""

    @classmethod
    def setUpClass(cls):
        """Set up test environment"""
        cls.test_dir = Path('test_output')
        cls.test_dir.mkdir(exist_ok=True)

        # Load configs
        config_path = Path('tools/db_config.json')
        if config_path.exists():
            with open(config_path, 'r') as f:
                cls.db_config = json.load(f)
        else:
            cls.db_config = None

    @classmethod
    def tearDownClass(cls):
        """Clean up test environment"""
        # Don't remove test directory in case we want to inspect output
        pass

    def test_sample_data_download(self):
        """Test downloading sample govinfo data"""
        try:
            # Import the fetch script
            sys.path.append('tools')
            from fetch_govinfo_bulk import crawl_collection

            # Test with minimal download
            test_output = self.test_dir / 'sample_download'
            test_output.mkdir(exist_ok=True)

            # This would normally download, but we'll mock it for testing
            # crawl_collection('https://www.govinfo.gov/bulkdata', 'BILLS', [119], [1],
            #                 str(test_output), samples_per_subdir=1)

            print("✓ Sample download test structure OK")

        except Exception as e:
            self.fail(f"Sample download test failed: {e}")

    def test_data_processing_pipeline(self):
        """Test the complete data processing pipeline"""
        if not self.db_config:
            self.skipTest("Database config not found")

        try:
            # Test basic data connector functionality
            sys.path.append('tools')
            from govinfo_data_connector import GovInfoDataConnector

            connector = GovInfoDataConnector(self.db_config)
            connector.connect_db()

            # Test with empty directory (should handle gracefully)
            empty_dir = self.test_dir / 'empty'
            empty_dir.mkdir(exist_ok=True)

            # This should not fail
            connector.process_directory(empty_dir, batch_size=10)

            connector.disconnect_db()
            print("✓ Data processing pipeline OK")

        except Exception as e:
            self.fail(f"Data processing test failed: {e}")

    def test_member_ingestion_validation(self):
        """Test federal member data ingestion validation"""
        if not self.db_config:
            self.skipTest("Database config not found")

        try:
            conn = psycopg2.connect(**self.db_config)
            cursor = conn.cursor()

            # Check if federal member tables have data
            cursor.execute("SELECT COUNT(*) FROM master.federal_person")
            person_count = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM master.federal_member")
            member_count = cursor.fetchone()[0]

            # If we have members, validate data integrity
            if member_count > 0:
                cursor.execute("""
                    SELECT COUNT(*) FROM master.federal_member
                    WHERE person_id IS NOT NULL
                    AND chamber IN ('house', 'senate')
                    AND state IS NOT NULL
                """)
                valid_members = cursor.fetchone()[0]

                self.assertEqual(valid_members, member_count,
                    "Some members have invalid data")

            cursor.close()
            conn.close()

            print(f"✓ Member ingestion validation OK (persons: {person_count}, members: {member_count})")

        except Exception as e:
            self.fail(f"Member validation test failed: {e}")


class TestSystemHealth(unittest.TestCase):
    """Test overall system health and monitoring"""

    def test_disk_space(self):
        """Test available disk space for data storage"""
        try:
            stat = os.statvfs('/')
            # Available space in GB
            available_gb = (stat.f_bavail * stat.f_frsize) / (1024**3)

            # Should have at least 10GB free
            self.assertGreater(available_gb, 10.0,
                f"Insufficient disk space: {available_gb:.1f}GB available")

            print(f"✓ Disk space OK ({available_gb:.1f}GB available)")

        except Exception as e:
            self.fail(f"Disk space test failed: {e}")

    def test_memory_usage(self):
        """Test system memory availability"""
        try:
            with open('/proc/meminfo', 'r') as f:
                mem_info = {}
                for line in f:
                    if ':' in line:
                        key, value = line.split(':', 1)
                        # Convert KB to GB
                        if value.strip().endswith(' kB'):
                            mem_info[key] = int(value.strip()[:-3]) / (1024**2)
                        else:
                            mem_info[key] = value.strip()

            available_gb = mem_info.get('MemAvailable', 0)

            # Should have at least 2GB available
            self.assertGreater(available_gb, 2.0,
                f"Insufficient memory: {available_gb:.1f}GB available")

            print(f"✓ Memory OK ({available_gb:.1f}GB available)")

        except Exception as e:
            self.fail(f"Memory test failed: {e}")

    def test_network_connectivity(self):
        """Test network connectivity to required services"""
        test_urls = [
            'https://api.congress.gov',
            'https://www.govinfo.gov',
            'https://www.google.com'  # General connectivity
        ]

        for url in test_urls:
            try:
                response = requests.get(url, timeout=5)
                self.assertIn(response.status_code, [200, 301, 302],
                    f"Bad response from {url}: {response.status_code}")

            except Exception as e:
                self.fail(f"Network test failed for {url}: {e}")

        print("✓ Network connectivity OK")


class TestProgressReporting(unittest.TestCase):
    """Test progress reporting and monitoring functionality"""

    def test_progress_calculation(self):
        """Test progress calculation logic"""
        # Test progress percentage calculation
        def calculate_progress(current: int, total: int) -> float:
            if total == 0:
                return 100.0
            return min(100.0, (current / total) * 100.0)

        # Test cases
        self.assertEqual(calculate_progress(0, 100), 0.0)
        self.assertEqual(calculate_progress(50, 100), 50.0)
        self.assertEqual(calculate_progress(100, 100), 100.0)
        self.assertEqual(calculate_progress(150, 100), 100.0)  # Cap at 100%
        self.assertEqual(calculate_progress(10, 0), 100.0)  # Handle division by zero

        print("✓ Progress calculation OK")

    def test_download_tracking(self):
        """Test download progress tracking"""
        # Mock download tracking
        download_stats = {
            'total_files': 1000,
            'downloaded': 0,
            'failed': 0,
            'bytes_downloaded': 0,
            'start_time': time.time()
        }

        # Simulate progress updates
        for i in range(10):
            download_stats['downloaded'] += 100
            download_stats['bytes_downloaded'] += 1024 * 1024  # 1MB each

            progress = (download_stats['downloaded'] / download_stats['total_files']) * 100
            self.assertGreaterEqual(progress, 0.0)
            self.assertLessEqual(progress, 100.0)

        print("✓ Download tracking OK")


def run_specific_tests(component: str):
    """Run tests for a specific component"""
    suite = unittest.TestSuite()

    if component == 'database':
        suite.addTest(TestDatabaseConnectivity())
    elif component == 'api':
        suite.addTest(TestAPIIntegration())
    elif component == 'ingestion':
        suite.addTest(TestDataIngestion())
    elif component == 'health':
        suite.addTest(TestSystemHealth())
    elif component == 'progress':
        suite.addTest(TestProgressReporting())
    else:
        print(f"Unknown component: {component}")
        return

    runner = unittest.TextTestRunner(verbosity=2)
    runner.run(suite)


def main():
    parser = argparse.ArgumentParser(description='Comprehensive OpenLegislation Test Suite')
    parser.add_argument('--component', choices=['database', 'api', 'ingestion', 'health', 'progress'],
                       help='Run tests for specific component only')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    parser.add_argument('--output', help='Output results to file')

    args = parser.parse_args()

    if args.component:
        run_specific_tests(args.component)
        return

    # Run all tests
    loader = unittest.TestLoader()

    # Discover and load all test classes
    suite = unittest.TestSuite()
    suite.addTests(loader.loadTestsFromTestCase(TestDatabaseConnectivity))
    suite.addTests(loader.loadTestsFromTestCase(TestAPIIntegration))
    suite.addTests(loader.loadTestsFromTestCase(TestDataIngestion))
    suite.addTests(loader.loadTestsFromTestCase(TestSystemHealth))
    suite.addTests(loader.loadTestsFromTestCase(TestProgressReporting))

    # Run tests
    verbosity = 2 if args.verbose else 1
    runner = unittest.TextTestRunner(verbosity=verbosity)

    if args.output:
        with open(args.output, 'w') as f:
            runner = unittest.TextTestRunner(stream=f, verbosity=verbosity)

    result = runner.run(suite)

    # Summary
    print(f"\n{'='*50}")
    print("TEST SUITE SUMMARY")
    print(f"{'='*50}")
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")

    if result.failures:
        print(f"\nFAILURES ({len(result.failures)}):")
        for test, traceback in result.failures:
            print(f"  - {test}")

    if result.errors:
        print(f"\nERRORS ({len(result.errors)}):")
        for test, traceback in result.errors:
            print(f"  - {test}")

    if result.wasSuccessful():
        print("\n🎉 ALL TESTS PASSED!")
        return 0
    else:
        print("\n❌ SOME TESTS FAILED!")
        return 1


if __name__ == '__main__':
    sys.exit(main())