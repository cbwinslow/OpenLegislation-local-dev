#!/usr/bin/env python3
"""
Test Federal Member Data Ingestion

Simple script to test ingesting a few federal members from congress.gov API.
This demonstrates the member data ingestion capability.

Usage:
    python3 tools/test_member_ingestion.py [--api-key YOUR_API_KEY] [--limit 5]
"""

import argparse
import sys
import time
from typing import Dict, List, Optional, Any

import psycopg2
import psycopg2.extras
import requests

from settings import settings


class TestMemberIngestor:
    """Simple test ingestor for federal member data"""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or settings.congress_api_key
        if not self.api_key:
            print(
                "Error: Congress API key not provided. Set CONGRESS_API_KEY in .env or pass --api-key"
            )
            sys.exit(1)

        self.db_config = settings.db_config
        self.base_url = "https://api.congress.gov/v3"
        self.session = requests.Session()
        self.error_count = 0
        self.max_errors = settings.max_errors

        # Connect to database
        try:
            self.conn = psycopg2.connect(**self.db_config)
            self.cursor = self.conn.cursor(
                cursor_factory=psycopg2.extras.RealDictCursor
            )
            print("✓ Database connection established")
        except Exception as e:
            self._handle_error(f"Database connection failed: {e}", fatal=True)

    def _handle_error(self, message: str, fatal: bool = False):
        """Handle an error, increment count, and exit if too many."""
        self.error_count += 1
        print(f"✗ {message} (Error {self.error_count}/{self.max_errors})")
        if fatal or self.error_count >= self.max_errors:
            print(f"Too many errors ({self.error_count}), exiting.")
            sys.exit(1)

    def _api_request(
        self, endpoint: str, params: Optional[Dict] = None
    ) -> Optional[Dict]:
        """Make API request with error handling"""
        url = f"{self.base_url}{endpoint}"
        request_params = {"api_key": self.api_key, "format": "json"}
        if params:
            request_params.update(params)

        try:
            response = self.session.get(
                url, params=request_params, timeout=settings.request_timeout
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            self._handle_error(f"API request failed: {e}")
            return None

    def test_api_connection(self) -> bool:
        """Test basic API connectivity"""
        print("Testing Congress.gov API connection...")
        data = self._api_request("/member", {"limit": 1, "currentMember": "true"})
        if data and "members" in data:
            print("✓ API connection successful")
            return True
        else:
            self._handle_error("API connection failed")
            return False

    def get_sample_members(self, limit: int = 5) -> List[Dict]:
        """Get a small sample of current members"""
        print(f"Fetching {limit} sample members...")
        data = self._api_request("/member", {"currentMember": "true", "limit": limit})

        if data and "members" in data:
            members = data["members"]
            print(f"✓ Retrieved {len(members)} members")
            return members
        else:
            self._handle_error("Failed to retrieve members")
            return []

    def create_test_tables(self):
        """Create minimal test tables if they don't exist"""
        try:
            # Simple federal person table for testing
            self.cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS test_federal_person (
                    id SERIAL PRIMARY KEY,
                    bioguide_id TEXT UNIQUE NOT NULL,
                    full_name TEXT NOT NULL,
                    chamber TEXT,
                    state TEXT,
                    party TEXT,
                    created_at TIMESTAMP DEFAULT now()
                )
            """
            )

            # Simple federal member table
            self.cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS test_federal_member (
                    id SERIAL PRIMARY KEY,
                    person_id INTEGER REFERENCES test_federal_person(id),
                    chamber TEXT NOT NULL,
                    state TEXT,
                    district TEXT,
                    party TEXT,
                    current_member BOOLEAN DEFAULT true,
                    created_at TIMESTAMP DEFAULT now()
                )
            """
            )

            self.conn.commit()
            print("✓ Test tables created")
        except Exception as e:
            self._handle_error(f"Failed to create test tables: {e}")
            self.conn.rollback()

    def insert_sample_member(self, member_data: Dict) -> bool:
        """Insert a sample member into test tables"""
        try:
            bioguide_id = member_data.get("bioguideId")
            if not bioguide_id:
                return False

            # Insert person
            self.cursor.execute(
                """
                INSERT INTO test_federal_person (bioguide_id, full_name, chamber, state, party)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (bioguide_id) DO NOTHING
                RETURNING id
            """,
                (
                    bioguide_id,
                    member_data.get("name", "Unknown"),
                    member_data.get("chamber", "").lower(),
                    member_data.get("state"),
                    member_data.get("partyName", member_data.get("party")),
                ),
            )

            result = self.cursor.fetchone()
            if result:
                person_id = result["id"]

                # Insert member record
                self.cursor.execute(
                    """
                    INSERT INTO test_federal_member (person_id, chamber, state, district, party)
                    VALUES (%s, %s, %s, %s, %s)
                """,
                    (
                        person_id,
                        member_data.get("chamber", "").lower(),
                        member_data.get("state"),
                        member_data.get("district"),
                        member_data.get("partyName", member_data.get("party")),
                    ),
                )

                self.conn.commit()
                return True
            else:
                # Person already exists, just add member record if needed
                self.cursor.execute(
                    """
                    SELECT id FROM test_federal_person WHERE bioguide_id = %s
                """,
                    (bioguide_id,),
                )

                person_result = self.cursor.fetchone()
                if person_result:
                    person_id = person_result["id"]
                    self.cursor.execute(
                        """
                        INSERT INTO test_federal_member (person_id, chamber, state, district, party)
                        VALUES (%s, %s, %s, %s, %s)
                        ON CONFLICT DO NOTHING
                    """,
                        (
                            person_id,
                            member_data.get("chamber", "").lower(),
                            member_data.get("state"),
                            member_data.get("district"),
                            member_data.get("partyName", member_data.get("party")),
                        ),
                    )
                    self.conn.commit()
                    return True

        except Exception as e:
            print(f"✗ Failed to insert member {bioguide_id}: {e}")
            self.conn.rollback()
            return False

        return False

    def show_results(self):
        """Display ingestion results"""
        try:
            # Count persons
            self.cursor.execute("SELECT COUNT(*) as count FROM test_federal_person")
            person_count = self.cursor.fetchone()["count"]

            # Count members
            self.cursor.execute("SELECT COUNT(*) as count FROM test_federal_member")
            member_count = self.cursor.fetchone()["count"]

            # Show sample data
            self.cursor.execute(
                """
                SELECT p.full_name, p.chamber, p.state, p.party, m.district
                FROM test_federal_person p
                JOIN test_federal_member m ON p.id = m.person_id
                LIMIT 5
            """
            )
            samples = self.cursor.fetchall()

            print("\n=== INGESTION RESULTS ===")
            print(f"Persons ingested: {person_count}")
            print(f"Member records: {member_count}")
            print("\nSample members:")
            for sample in samples:
                district = (
                    f" (District {sample['district']})" if sample["district"] else ""
                )
                print(
                    f"  {sample['full_name']} - {sample['chamber'].title()} {sample['state']}{district} ({sample['party']})"
                )

        except Exception as e:
            print(f"✗ Error displaying results: {e}")

    def run_test(self, limit: int = 5):
        """Run the complete test"""
        print("=== Federal Member Data Ingestion Test ===\n")

        # Test API connection
        if not self.test_api_connection():
            return

        # Create test tables
        self.create_test_tables()

        # Get sample members
        members = self.get_sample_members(limit)
        if not members:
            return

        # Insert members
        successful = 0
        for member in members:
            if self.insert_sample_member(member):
                successful += 1
                print(f"✓ Ingested: {member.get('name', 'Unknown')}")
            else:
                self._handle_error(f"Failed to ingest: {member.get('name', 'Unknown')}")

            time.sleep(settings.rate_limit_delay)  # Rate limiting

        print(f"\nSuccessfully ingested {successful}/{len(members)} members")

        # Show results
        self.show_results()

        print("\n=== Test Complete ===")
        print("The federal member ingestion system is working!")
        print("To ingest all members, use the full ingest_federal_members.py script")

    def close(self):
        """Clean up"""
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()


def main():
    parser = argparse.ArgumentParser(description="Test federal member data ingestion")
    parser.add_argument(
        "--api-key", help="Congress.gov API key (overrides CONGRESS_API_KEY from .env)"
    )
    parser.add_argument(
        "--limit", type=int, default=5, help="Number of members to test (default: 5)"
    )

    args = parser.parse_args()

    # Run test
    ingestor = TestMemberIngestor(args.api_key)
    try:
        ingestor.run_test(args.limit)
    finally:
        ingestor.close()


if __name__ == "__main__":
    main()
