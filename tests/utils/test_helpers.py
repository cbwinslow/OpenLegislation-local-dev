"""
Test utilities and helper functions for OpenLegislation tests.

This module provides common utilities, assertions, and helper functions
used across different test modules.
"""

import json
import os
import pytest
import tempfile
from typing import Dict, Any, List, Optional
from pathlib import Path


def load_test_data(filename: str) -> Dict[str, Any]:
    """Load test data from JSON file."""
    test_data_dir = Path(__file__).parent / "fixtures"
    test_data_dir.mkdir(exist_ok=True)

    file_path = test_data_dir / filename
    if file_path.exists():
        with open(file_path, 'r') as f:
            return json.load(f)
    return {}


def save_test_data(filename: str, data: Dict[str, Any]):
    """Save test data to JSON file."""
    test_data_dir = Path(__file__).parent / "fixtures"
    test_data_dir.mkdir(exist_ok=True)

    file_path = test_data_dir / filename
    with open(file_path, 'w') as f:
        json.dump(data, f, indent=2)


def create_temp_file(content: str = "", suffix: str = ".txt") -> str:
    """Create a temporary file with given content."""
    import tempfile
    fd, path = tempfile.mkstemp(suffix=suffix)
    try:
        with os.fdopen(fd, 'w') as f:
            f.write(content)
        return path
    except:
        os.close(fd)
        raise


def assert_nested_dict_contains(actual: Dict[str, Any], expected: Dict[str, Any], path: str = ""):
    """Assert that nested dict contains expected structure."""
    for key, value in expected.items():
        current_path = f"{path}.{key}" if path else key

        assert key in actual, f"Key '{current_path}' not found"

        if isinstance(value, dict):
            assert isinstance(actual[key], dict), f"Value at '{current_path}' should be dict"
            assert_nested_dict_contains(actual[key], value, current_path)
        elif isinstance(value, list):
            assert isinstance(actual[key], list), f"Value at '{current_path}' should be list"
            # For lists, just check types match if they contain dicts
            if value and isinstance(value[0], dict):
                for i, item in enumerate(actual[key]):
                    if isinstance(item, dict):
                        assert_nested_dict_contains(item, value[0], f"{current_path}[{i}]")
        else:
            assert actual[key] == value, f"Value mismatch at '{current_path}': expected {value}, got {actual[key]}"


def assert_performance_metrics(metrics: Dict[str, Any], expected_keys: List[str]):
    """Assert that performance metrics contain expected keys."""
    for key in expected_keys:
        assert key in metrics, f"Performance metric '{key}' not found"
        assert isinstance(metrics[key], (int, float)), f"Performance metric '{key}' should be numeric"


def assert_database_record(record: Dict[str, Any], expected_fields: Dict[str, Any]):
    """Assert that database record contains expected fields."""
    for field, expected_value in expected_fields.items():
        assert field in record, f"Field '{field}' not found in record"
        if expected_value is not None:
            assert record[field] == expected_value, f"Field '{field}' mismatch: expected {expected_value}, got {record[field]}"


def assert_api_response(response: Dict[str, Any], expected_status: str = "success"):
    """Assert that API response has expected structure."""
    assert "status" in response, "Response missing 'status' field"
    assert response["status"] == expected_status, f"Expected status '{expected_status}', got '{response['status']}'"


def assert_legislative_data_integrity(data: Dict[str, Any]):
    """Assert that legislative data has required integrity constraints."""
    required_fields = ["jurisdiction"]

    for field in required_fields:
        assert field in data, f"Required field '{field}' missing from legislative data"
        assert data[field], f"Required field '{field}' cannot be empty"

    # Check for valid jurisdictions
    valid_jurisdictions = ["federal", "state", "local", "ny_state", "ca_state"]
    if "jurisdiction" in data:
        assert data["jurisdiction"] in valid_jurisdictions, f"Invalid jurisdiction: {data['jurisdiction']}"


def assert_member_data_integrity(data: Dict[str, Any]):
    """Assert that member data has required integrity constraints."""
    required_fields = ["member_id", "name", "jurisdiction"]

    for field in required_fields:
        assert field in data, f"Required field '{field}' missing from member data"
        assert data[field], f"Required field '{field}' cannot be empty"


def assert_vote_data_integrity(data: Dict[str, Any]):
    """Assert that vote data has required integrity constraints."""
    required_fields = ["vote_id", "jurisdiction", "result"]

    for field in required_fields:
        assert field in data, f"Required field '{field}' missing from vote data"
        assert data[field], f"Required field '{field}' cannot be empty"

    # Check for valid results
    valid_results = ["passed", "failed", "tie", "absent"]
    if "result" in data:
        assert data["result"] in valid_results, f"Invalid vote result: {data['result']}"


def generate_mock_bill_data(count: int = 1) -> List[Dict[str, Any]]:
    """Generate mock bill data for testing."""
    bills = []
    for i in range(count):
        bill = {
            "bill_id": f"HR{i+1000}",
            "title": f"Test Bill {i+1}",
            "summary": f"This is a summary for test bill {i+1}",
            "status": "introduced",
            "introduced_date": f"2025-01-{str(i+1).zfill(2)}",
            "sponsor": f"Test Sponsor {i+1}",
            "jurisdiction": "federal",
            "content": f"Full text content for bill {i+1}"
        }
        bills.append(bill)
    return bills if count > 1 else bills[0]


def generate_mock_member_data(count: int = 1) -> List[Dict[str, Any]]:
    """Generate mock member data for testing."""
    members = []
    states = ["NY", "CA", "TX", "FL", "IL"]
    parties = ["Democrat", "Republican", "Independent"]

    for i in range(count):
        member = {
            "member_id": f"M{i+100}",
            "name": f"Test Member {i+1}",
            "party": parties[i % len(parties)],
            "state": states[i % len(states)],
            "district": str((i % 50) + 1),
            "chamber": "house" if i % 2 == 0 else "senate",
            "jurisdiction": "federal"
        }
        members.append(member)
    return members if count > 1 else members[0]


def generate_mock_vote_data(count: int = 1) -> List[Dict[str, Any]]:
    """Generate mock vote data for testing."""
    votes = []
    results = ["passed", "failed", "tie"]

    for i in range(count):
        vote = {
            "vote_id": f"V{i+1000}",
            "bill_id": f"HR{i+1000}",
            "chamber": "house" if i % 2 == 0 else "senate",
            "date": f"2025-01-{str((i % 28) + 1).zfill(2)}",
            "result": results[i % len(results)],
            "yeas": 200 + (i % 50),
            "nays": 180 + (i % 40),
            "jurisdiction": "federal"
        }
        votes.append(vote)
    return votes if count > 1 else votes[0]


def mock_http_response(status_code: int = 200, json_data: Optional[Dict] = None, text: str = ""):
    """Create a mock HTTP response."""
    response = type('MockResponse', (), {})()
    response.status_code = status_code
    response.json = lambda: json_data or {}
    response.text = text or json.dumps(json_data or {})
    return response


def assert_no_exceptions(func, *args, **kwargs):
    """Assert that function executes without raising exceptions."""
    try:
        result = func(*args, **kwargs)
        return result
    except Exception as e:
        pytest.fail(f"Function {func.__name__} raised unexpected exception: {e}")


async def assert_async_no_exceptions(coro):
    """Assert that async coroutine executes without raising exceptions."""
    try:
        result = await coro
        return result
    except Exception as e:
        pytest.fail(f"Coroutine raised unexpected exception: {e}")


def assert_file_exists(file_path: str):
    """Assert that file exists."""
    assert os.path.exists(file_path), f"File does not exist: {file_path}"


def assert_file_contains(file_path: str, content: str):
    """Assert that file contains specific content."""
    assert_file_exists(file_path)
    with open(file_path, 'r') as f:
        file_content = f.read()
    assert content in file_content, f"Content '{content}' not found in file {file_path}"


def cleanup_temp_files(*file_paths: str):
    """Clean up temporary files."""
    for path in file_paths:
        try:
            if os.path.exists(path):
                os.remove(path)
        except OSError:
            pass  # Ignore cleanup errors


def create_test_database_schema() -> str:
    """Create a test database schema SQL for testing."""
    return """
    -- Test database schema for OpenLegislation
    CREATE TABLE IF NOT EXISTS test_bills (
        bill_id VARCHAR(50) PRIMARY KEY,
        title TEXT NOT NULL,
        summary TEXT,
        status VARCHAR(50) NOT NULL,
        introduced_date DATE,
        sponsor VARCHAR(255),
        jurisdiction VARCHAR(50) NOT NULL,
        content TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS test_members (
        member_id VARCHAR(50) PRIMARY KEY,
        name VARCHAR(255) NOT NULL,
        party VARCHAR(50),
        state VARCHAR(10),
        district VARCHAR(10),
        chamber VARCHAR(20),
        jurisdiction VARCHAR(50) NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS test_votes (
        vote_id VARCHAR(50) PRIMARY KEY,
        bill_id VARCHAR(50) REFERENCES test_bills(bill_id),
        chamber VARCHAR(20),
        date DATE,
        result VARCHAR(20),
        yeas INTEGER,
        nays INTEGER,
        jurisdiction VARCHAR(50) NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    CREATE INDEX IF NOT EXISTS idx_test_bills_jurisdiction ON test_bills(jurisdiction);
    CREATE INDEX IF NOT EXISTS idx_test_members_jurisdiction ON test_members(jurisdiction);
    CREATE INDEX IF NOT EXISTS idx_test_votes_jurisdiction ON test_votes(jurisdiction);
    """


def cleanup_test_database(connection):
    """Clean up test database tables."""
    try:
        with connection.cursor() as cursor:
            cursor.execute("DROP TABLE IF EXISTS test_votes CASCADE")
            cursor.execute("DROP TABLE IF EXISTS test_members CASCADE")
            cursor.execute("DROP TABLE IF EXISTS test_bills CASCADE")
        connection.commit()
    except Exception:
        # Ignore cleanup errors in tests
        pass