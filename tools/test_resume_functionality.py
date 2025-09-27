#!/usr/bin/env python3
"""
Test Resume Functionality for Federal Member Ingestion

Tests the resume capability by simulating partial ingestion runs and verifying
that the system correctly tracks and resumes from previous state.
"""

import json
import sys
import time
from typing import Dict, List, Any

import psycopg2
import psycopg2.extras

from settings import settings
from member_ingestion_tracker import MemberIngestionTracker


class ResumeFunctionalityTester:
    """Tests resume functionality for member ingestion"""

    def __init__(self):
        self.db_config = settings.db_config
        self.session_id = "test_resume_session"
        self.tracker = MemberIngestionTracker(self.db_config, self.session_id)

        # Test data - simulate member summaries
        self.test_members = [
            {'bioguideId': 'T000001', 'name': 'Test Member 1'},
            {'bioguideId': 'T000002', 'name': 'Test Member 2'},
            {'bioguideId': 'T000003', 'name': 'Test Member 3'},
            {'bioguideId': 'T000004', 'name': 'Test Member 4'},
            {'bioguideId': 'T000005', 'name': 'Test Member 5'},
        ]

    def setup_test_data(self):
        """Initialize test members in tracker"""
        print("Setting up test data...")
        self.tracker.initialize_members(self.test_members, reset_existing=True)
        print("✓ Test data initialized")

    def simulate_partial_ingestion(self, members_to_process: int, simulate_failures: bool = False):
        """Simulate processing some members (some successful, some failed)"""
        print(f"Simulating partial ingestion of {members_to_process} members...")

        for i, member in enumerate(self.test_members[:members_to_process]):
            bioguide_id = member['bioguideId']

            # Mark as in progress
            self.tracker.mark_in_progress(bioguide_id)

            # Simulate processing time
            time.sleep(0.1)

            # Simulate success/failure
            if simulate_failures and i == 1:  # Fail the second member
                self.tracker.mark_failed(bioguide_id, "Simulated API failure")
                print(f"✗ Failed: {bioguide_id}")
            else:
                self.tracker.mark_completed(bioguide_id)
                print(f"✓ Completed: {bioguide_id}")

        print("Partial ingestion simulation complete")

    def test_resume_logic(self):
        """Test that resume correctly identifies members to process"""
        print("\nTesting resume logic...")

        # Get members that should be processed (pending ones)
        pending_members = self.tracker.get_pending_members()
        print(f"Pending members: {pending_members}")

        # Verify we get the expected count
        expected_pending = len(self.test_members) - 2  # 2 were completed in partial run
        if len(pending_members) == expected_pending:
            print(f"✓ Correct number of pending members: {len(pending_members)}")
        else:
            print(f"✗ Expected {expected_pending} pending, got {len(pending_members)}")
            return False

        # Test should_process_member for each
        for member in self.test_members:
            bioguide_id = member['bioguideId']
            should_process = self.tracker.should_process_member(bioguide_id)
            status = self.tracker.get_member_status(bioguide_id)

            expected = status['ingestion_status'] in ('pending', 'failed')
            if should_process == expected:
                print(f"✓ {bioguide_id}: should_process={should_process} (status: {status['ingestion_status']})")
            else:
                print(f"✗ {bioguide_id}: should_process={should_process}, expected {expected}")
                return False

        return True

    def test_status_reporting(self):
        """Test status reporting functionality"""
        print("\nTesting status reporting...")

        stats = self.tracker.get_ingestion_stats()
        print(f"Total members: {stats.total_members}")
        print(f"Completed: {stats.completed}")
        print(f"Failed: {stats.failed}")
        print(f"Pending: {stats.pending}")
        print(f"Success rate: {stats.success_rate:.1f}%")

        # Verify stats are correct
        expected_completed = 2  # From partial ingestion
        expected_failed = 1     # One simulated failure
        expected_pending = len(self.test_members) - expected_completed - expected_failed

        if (stats.completed == expected_completed and
            stats.failed == expected_failed and
            stats.pending == expected_pending):
            print("✓ Status reporting correct")
            return True
        else:
            print(f"✗ Status mismatch - Expected: {expected_completed} completed, {expected_failed} failed, {expected_pending} pending")
            return False

    def test_reset_functionality(self):
        """Test reset functionality"""
        print("\nTesting reset functionality...")

        # Reset all status
        self.tracker.reset_session()

        # Check that all members are now pending
        pending_members = self.tracker.get_pending_members()
        if len(pending_members) == len(self.test_members):
            print("✓ Reset successful - all members pending")
            return True
        else:
            print(f"✗ Reset failed - expected {len(self.test_members)} pending, got {len(pending_members)}")
            return False

    def run_all_tests(self):
        """Run the complete test suite"""
        print("=== RESUME FUNCTIONALITY TEST SUITE ===\n")

        try:
            # Setup
            self.setup_test_data()

            # Simulate partial run
            self.simulate_partial_ingestion(3, simulate_failures=True)

            # Test resume logic
            if not self.test_resume_logic():
                return False

            # Test status reporting
            if not self.test_status_reporting():
                return False

            # Test reset
            if not self.test_reset_functionality():
                return False

            print("\n=== ALL TESTS PASSED ===")
            print("Resume functionality is working correctly!")
            return True

        except Exception as e:
            print(f"\n✗ Test suite failed with error: {e}")
            return False
        finally:
            self.tracker.close()

    def cleanup(self):
        """Clean up test data"""
        try:
            # Remove test session data
            conn = psycopg2.connect(**self.db_config)
            cursor = conn.cursor()

            cursor.execute("""
                DELETE FROM master.federal_member_ingestion_status
                WHERE ingestion_session_id = %s
            """, (self.session_id,))

            conn.commit()
            conn.close()
            print("✓ Test data cleaned up")
        except Exception as e:
            print(f"Warning: Could not clean up test data: {e}")


def main():
    tester = ResumeFunctionalityTester()
    try:
        success = tester.run_all_tests()
        sys.exit(0 if success else 1)
    finally:
        tester.cleanup()


if __name__ == '__main__':
    main()</parameter>
