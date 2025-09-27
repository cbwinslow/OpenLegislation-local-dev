"""Comprehensive tests for federal member data ingestion.

These tests cover unit tests for individual functions (API mocking, data parsing, validation)
and integration tests using the test database to verify end-to-end ingestion, analysis, and
data manipulation processes. Tests ensure schema compliance, foreign key integrity, trigger
firing (audit logs), and data quality.

Requires: pytest, pytest-mock, psycopg2-binary
Run with: pytest tools/tests/test_federal_ingestion.py -v
"""

import json
import os
import pytest
from unittest.mock import Mock, patch
from datetime import datetime

import pytest
from pytest_mock import MockFixture

import psycopg2
from psycopg2.extras import RealDictCursor

from ingest_federal_members import CongressMemberIngestor  # Import the ingestor class
from settings import settings


@pytest.fixture(scope="session")
def test_db_conn():
    """Fixture for test database connection."""
    conn = psycopg2.connect(**settings.test_db_config)
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    # Ensure schema exists in test DB
    cursor.execute("CREATE SCHEMA IF NOT EXISTS master")
    cursor.execute("CREATE EXTENSION IF NOT EXISTS pgvector")
    # Apply federal schema if not present (simplified for test)
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS master.federal_person (
            id BIGSERIAL PRIMARY KEY,
            bioguide_id TEXT UNIQUE NOT NULL,
            full_name TEXT NOT NULL,
            first_name TEXT, middle_name TEXT, last_name TEXT, suffix TEXT, nickname TEXT,
            birth_year INTEGER, death_year INTEGER, gender TEXT,
            created_at TIMESTAMP DEFAULT now(), updated_at TIMESTAMP DEFAULT now()
        )
    """
    )
    # Add other tables similarly for test
    # ... (add federal_member, terms, etc. for complete test)
    conn.commit()
    yield conn, cursor
    cursor.close()
    conn.close()


@pytest.fixture
def mock_api(mocker: MockFixture):
    """Mock Congress.gov API responses."""
    mock_data = {
        "member/Y000064": {
            "member": {
                "bioguideId": "Y000064",
                "name": "Young, Todd",
                "firstName": "Todd",
                "lastName": "Young",
                "chamber": "senate",
                "state": "IN",
                "partyName": "Republican",
                "birthYear": "1972",
                "twitterAccount": "@SenToddYoung",
                "terms": [
                    {
                        "congress": 118,
                        "startYear": 2017,
                        "endYear": 2025,
                        "party": "Republican",
                    }
                ],
            }
        },
        "member/W000779": {  # Example with empty chamber in summary, but details have it
            "member": {
                "bioguideId": "W000779",
                "name": "Washington, Harold",
                "firstName": "Harold",
                "lastName": "Washington",
                "chamber": "house",
                "state": "IL",
                "partyName": "Democratic",
                "birthYear": "1922",
                "deathYear": "1987",
            }
        },
        # Add more sample data
    }
    mocker.patch(
        "requests.Session.get",
        return_value=Mock(
            status_code=200, json=lambda: mock_data.get(f"member/{bioguide_id}", {})
        ),
    )
    return mocker


class TestIngestionUnits:
    """Unit tests for ingestion functions."""

    def test_name_parsing(self):
        """Test full name and component parsing."""
        member_data = {
            "name": "Doe, John Q. Jr.",
            "firstName": "John",
            "middleName": "Quincy",
            "lastName": "Doe",
            "suffix": "Jr.",
            "nickname": "Jack",
        }
        # Call the parsing logic from insert_person (extract logic if needed)
        from ingest_federal_members import parse_name  # Assume extracted

        full_name, first, middle, last, suffix, nickname = parse_name(member_data)
        assert full_name == 'John Quincy "Jack" Doe Jr.'
        assert first == "John"
        assert middle == "Quincy"
        assert last == "Doe"
        assert suffix == "Jr."
        assert nickname == '"Jack"'

    @patch("ingest_federal_members.requests.Session.get")
    def test_party_normalization(self, mock_get):
        """Test party code normalization."""
        mock_get.return_value.json.return_value = {
            "member": {"partyName": "DEMOCRATIC"}
        }
        ingestor = CongressMemberIngestor()
        party = ingestor.normalize_party("DEMOCRATIC")
        assert party == "D"

    def test_gender_inference(self):
        """Test gender inference from honorific."""
        ingestor = CongressMemberIngestor()
        assert ingestor.infer_gender("Mr.") == "M"
        assert ingestor.infer_gender("Mrs.") == "F"
        assert ingestor.infer_gender("Senator") == "M"  # Default
        assert ingestor.infer_gender("") == None

    def test_social_media_url_construction(self):
        """Test social media URL building."""
        ingestor = CongressMemberIngestor()
        url, handle = ingestor.build_social_url("twitter", "SenToddYoung")
        assert url == "https://twitter.com/SenToddYoung"
        assert handle == "SenToddYoung"
        url_fb, handle_fb = ingestor.build_social_url(
            "facebook", "https://fb.com/SenatorYoung"
        )
        assert url_fb == "https://fb.com/SenatorYoung"
        assert handle_fb == "SenatorYoung"


class TestIngestionIntegration:
    """Integration tests using test database."""

    @pytest.mark.integration
    def test_end_to_end_ingestion(self, test_db_conn, mock_api):
        """Test full ingestion of sample members."""
        conn, cursor = test_db_conn
        ingestor = CongressMemberIngestor(db_config=settings.test_db_config)
        sample_records = [{"record_id": "Y000064", "metadata": {}}]
        ingestor.tracker.initialize_records(sample_records)

        # Process record
        success = ingestor.process_record(sample_records[0])
        assert success is True

        # Verify insert
        cursor.execute(
            "SELECT COUNT(*) FROM master.federal_person WHERE bioguide_id = 'Y000064'"
        )
        count = cursor.fetchone()[0]
        assert count == 1

        # Verify member insert (chamber should be 'senate' from details)
        cursor.execute(
            "SELECT * FROM master.federal_member WHERE person_id = (SELECT id FROM master.federal_person WHERE bioguide_id = 'Y000064')"
        )
        member = cursor.fetchone()
        assert member["chamber"] == "senate"
        assert member["state"] == "IN"
        assert member["party"] == "R"

        # Verify triggers fired (audit log)
        cursor.execute(
            "SELECT COUNT(*) FROM master.audit_log WHERE table_name = 'federal_member'"
        )
        audit_count = cursor.fetchone()[0]
        assert audit_count >= 1

        # Verify foreign key
        cursor.execute("SELECT person_id FROM master.federal_member LIMIT 1")
        pid = cursor.fetchone()[0]
        cursor.execute(f"SELECT id FROM master.federal_person WHERE id = {pid}")
        assert cursor.fetchone() is not None

    @pytest.mark.integration
    def test_error_handling_and_skips(self, test_db_conn, mock_api, mocker):
        """Test skipping invalid members and error recovery."""
        conn, cursor = test_db_conn
        ingestor = CongressMemberIngestor(db_config=settings.test_db_config)
        # Mock detail API to return empty chamber
        mocker.patch.object(
            ingestor,
            "get_member_details",
            return_value={"bioguideId": "INVALID", "chamber": ""},
        )
        sample_record = {"record_id": "INVALID", "metadata": {}}
        success = ingestor.process_record(sample_record)
        assert success is False  # Should fail gracefully

        # Verify person inserted but member skipped
        cursor.execute(
            "SELECT COUNT(*) FROM master.federal_person WHERE bioguide_id = 'INVALID'"
        )
        person_count = cursor.fetchone()[0]
        assert person_count == 1  # Person always inserted
        cursor.execute(
            "SELECT COUNT(*) FROM master.federal_member WHERE person_id = (SELECT id FROM master.federal_person WHERE bioguide_id = 'INVALID')"
        )
        member_count = cursor.fetchone()[0]
        assert member_count == 0  # Member skipped

        # Verify audit log for insert and failure
        cursor.execute(
            "SELECT COUNT(*) FROM master.audit_log WHERE record_id = 'INVALID'"
        )
        audit_count = cursor.fetchone()[0]
        assert audit_count > 0

    @pytest.mark.integration
    def test_analysis_queries(self, test_db_conn):
        """Test analysis queries after ingestion."""
        conn, cursor = test_db_conn
        # Assume sample data inserted in fixture or previous test
        # Test party distribution
        cursor.execute(
            "SELECT party, COUNT(*) FROM master.federal_member GROUP BY party ORDER BY COUNT(*) DESC"
        )
        parties = cursor.fetchall()
        assert len(parties) > 0
        assert parties[0]["party"] in ["D", "R", "I"]
        assert sum(row["count"] for row in parties) > 0

        # Test state coverage
        cursor.execute(
            "SELECT state, COUNT(*) FROM master.federal_member WHERE current_member = true GROUP BY state"
        )
        states = cursor.fetchall()
        assert len(states) >= 50  # At least all states represented

        # Test social media completeness
        cursor.execute(
            """
            SELECT COUNT(DISTINCT member_id) as total_with_social
            FROM master.federal_member_social_media
        """
        )
        social_count = cursor.fetchone()["total_with_social"]
        cursor.execute(
            "SELECT COUNT(*) as total_members FROM master.federal_member WHERE current_member = true"
        )
        total_members = cursor.fetchone()["total_members"]
        completeness = (social_count / total_members * 100) if total_members > 0 else 0
        assert completeness > 70  # Based on doc expectation

    @pytest.mark.integration
    def test_data_manipulation_and_audit(self, test_db_conn):
        """Test manipulating records and verifying audit logs."""
        import uuid

        conn, cursor = test_db_conn
        # Insert sample record
        cursor.execute(
            """
            INSERT INTO master.federal_person (bioguide_id, full_name) VALUES (%s, %s) RETURNING id
        """,
            ("TEST123", "Test Member"),
        )
        person_id = cursor.fetchone()["id"]
        conn.commit()

        # Manipulate data (update)
        cursor.execute(
            """
            UPDATE master.federal_person SET full_name = 'Updated Name' WHERE id = %s
        """,
            (person_id,),
        )
        conn.commit()

        # Verify audit log
        cursor.execute(
            """
            SELECT * FROM master.audit_log
            WHERE table_name = 'federal_person' AND record_id = 'TEST123' OR record_id = %s
            ORDER BY created_at DESC LIMIT 1
        """,
            (person_id,),
        )
        audit = cursor.fetchone()
        assert audit is not None
        assert audit["operation"] == "UPDATE"
        assert audit["old_value"] is not None
        assert audit["new_value"] == "Updated Name"

        # Test foreign key integrity
        cursor.execute(
            """
            INSERT INTO master.federal_member (person_id, chamber, state, party) VALUES (%s, 'senate', 'CA', 'D')
        """,
            (person_id,),
        )
        conn.commit()

        # Delete person - should cascade or block
        with pytest.raises(psycopg2.IntegrityError):
            cursor.execute(
                "DELETE FROM master.federal_person WHERE id = %s", (person_id,)
            )
            conn.commit()  # Should fail due to FK if no cascade

        # Reset for cleanup
        cursor.execute(
            "DELETE FROM master.federal_member WHERE person_id = %s", (person_id,)
        )
        cursor.execute("DELETE FROM master.federal_person WHERE id = %s", (person_id,))
        conn.commit()

    def test_ingestion_resume(self, test_db_conn, mock_api):
        """Test resume functionality after partial ingestion."""
        conn, cursor = test_db_conn
        ingestor = CongressMemberIngestor(db_config=settings.test_db_config)
        sample_records = [
            {"record_id": "RESUME1", "metadata": {}},
            {"record_id": "RESUME2", "metadata": {}},
            {"record_id": "RESUME3", "metadata": {}},
        ]
        ingestor.tracker.initialize_records(sample_records)

        # Process first two, fail third
        ingestor.process_record(sample_records[0])  # Success
        ingestor.process_record(sample_records[1])  # Success
        ingestor.process_record(sample_records[2])  # Fail (mock)

        # Verify status
        status1 = ingestor.tracker.get_record_status("RESUME1")
        assert status1["ingestion_status"] == "completed"
        status2 = ingestor.tracker.get_record_status("RESUME2")
        assert status2["ingestion_status"] == "completed"
        status3 = ingestor.tracker.get_record_status("RESUME3")
        assert status3["ingestion_status"] == "pending"  # Retry pending

        # Resume should only process RESUME3
        pending = ingestor.tracker.get_pending_records()
        assert len(pending) == 1
        assert pending[0]["record_id"] == "RESUME3"

    @pytest.mark.vector
    def test_vectorization_support(self, test_db_conn):
        """Test pgvector extension for future semantic search."""
        conn, cursor = test_db_conn
        # Add vector column to test
        cursor.execute(
            """
            ALTER TABLE master.federal_person ADD COLUMN IF NOT EXISTS embedding VECTOR(384)
        """
        )
        conn.commit()

        # Insert with sample vector
        cursor.execute(
            """
            INSERT INTO master.federal_person (bioguide_id, full_name, embedding)
            VALUES ('VEC1', 'Vector Test', '[0.1, 0.2, 0.3]'::vector)
        """
        )
        conn.commit()

        # Verify vector query (cosine similarity example)
        cursor.execute(
            """
            SELECT bioguide_id FROM master.federal_person
            ORDER BY embedding <=> '[0.1, 0.2, 0.3]'::vector LIMIT 1
        """
        )
        result = cursor.fetchone()
        assert result["bioguide_id"] == "VEC1"

        # Cleanup
        cursor.execute("DELETE FROM master.federal_person WHERE bioguide_id = 'VEC1'")
        conn.commit()


if __name__ == "__main__":
    pytest.main(["-v", __file__])
