"""
Pytest configuration and shared fixtures for OpenLegislation tests.

This module provides common test fixtures, utilities, and configuration
for all test modules in the OpenLegislation project.
"""

import asyncio
import os
import pytest
import tempfile
import shutil
from typing import Dict, Any, Generator
from unittest.mock import Mock, MagicMock, patch
try:  # pragma: no cover - optional dependency for tests
    import psycopg2
except ImportError:  # pragma: no cover
    psycopg2 = MagicMock()

try:  # pragma: no cover
    import asyncpg
except ImportError:  # pragma: no cover
    asyncpg = MagicMock()


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def temp_dir():
    """Create a temporary directory for tests."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)


@pytest.fixture(scope="session")
def mock_db_config():
    """Mock database configuration for testing."""
    return {
        'host': 'localhost',
        'port': 5432,
        'user': 'test_user',
        'password': 'test_password',
        'database': 'test_db'
    }


@pytest.fixture(scope="function")
def mock_db_connection(mock_db_config):
    """Mock database connection."""
    with patch('psycopg2.connect') as mock_connect:
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_conn.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_conn
        yield mock_conn


@pytest.fixture(scope="function")
def mock_async_db_connection():
    """Mock async database connection."""
    mock_conn = Mock()
    mock_conn.execute = Mock(return_value=asyncio.Future())
    mock_conn.execute.return_value.set_result(None)
    mock_conn.fetch = Mock(return_value=asyncio.Future())
    mock_conn.fetch.return_value.set_result([])
    mock_conn.fetchrow = Mock(return_value=asyncio.Future())
    mock_conn.fetchrow.return_value.set_result(None)
    yield mock_conn


@pytest.fixture(scope="function")
def mock_crewai_agent():
    """Mock CrewAI agent for testing."""
    agent = Mock()
    agent.name = "TestAgent"
    agent.role = "Test Role"
    agent.goal = "Test Goal"
    agent.backstory = "Test Backstory"
    agent.execute = Mock(return_value="Test response")
    yield agent


@pytest.fixture(scope="function")
def mock_crawl4ai():
    """Mock crawl4ai for web crawling tests."""
    with patch('crawl4ai.AsyncWebCrawler') as mock_crawler:
        mock_instance = Mock()
        mock_instance.arun = Mock(return_value=asyncio.Future())
        mock_instance.arun.return_value.set_result({
            'content': '<html><body>Test content</body></html>',
            'links': ['http://example.com/page1', 'http://example.com/page2'],
            'metadata': {'title': 'Test Page', 'description': 'Test description'}
        })
        mock_crawler.return_value.__aenter__ = Mock(return_value=mock_instance)
        mock_crawler.return_value.__aexit__ = Mock(return_value=None)
        yield mock_crawler


@pytest.fixture(scope="function")
def sample_legislative_data():
    """Sample legislative data for testing."""
    return {
        'bill_id': 'HR1234',
        'title': 'Test Bill Title',
        'summary': 'This is a test bill summary',
        'status': 'introduced',
        'introduced_date': '2025-01-01',
        'sponsor': 'Test Sponsor',
        'jurisdiction': 'federal',
        'content': 'Full bill text content here...'
    }


@pytest.fixture(scope="function")
def sample_member_data():
    """Sample member data for testing."""
    return {
        'member_id': 'M001',
        'name': 'John Doe',
        'party': 'Democrat',
        'state': 'NY',
        'district': '1',
        'chamber': 'house',
        'jurisdiction': 'federal'
    }


@pytest.fixture(scope="function")
def sample_vote_data():
    """Sample vote data for testing."""
    return {
        'vote_id': 'V001',
        'bill_id': 'HR1234',
        'chamber': 'house',
        'date': '2025-01-15',
        'result': 'passed',
        'yeas': 220,
        'nays': 210,
        'jurisdiction': 'federal'
    }


@pytest.fixture(autouse=True)
def mock_env_vars():
    """Mock environment variables for consistent testing."""
    env_vars = {
        'DB_HOST': 'localhost',
        'DB_PORT': '5432',
        'DB_USER': 'test_user',
        'DB_PASS': 'test_password',
        'DB_NAME': 'test_db',
        'OPENAI_API_KEY': 'test_key',
        'CRAWL4AI_API_KEY': 'test_crawl_key'
    }

    with patch.dict(os.environ, env_vars):
        yield


@pytest.fixture(scope="function")
def mock_opentelemetry():
    """Mock OpenTelemetry components for testing."""
    with patch('opentelemetry.trace.get_tracer') as mock_get_tracer, \
         patch('opentelemetry.metrics.get_meter') as mock_get_meter:

        mock_tracer = Mock()
        mock_span = Mock()
        mock_tracer.start_as_current_span.return_value.__enter__ = Mock(return_value=mock_span)
        mock_tracer.start_as_current_span.return_value.__exit__ = Mock(return_value=None)
        mock_get_tracer.return_value = mock_tracer

        mock_meter = Mock()
        mock_counter = Mock()
        mock_histogram = Mock()
        mock_updown_counter = Mock()
        mock_meter.create_counter.return_value = mock_counter
        mock_meter.create_histogram.return_value = mock_histogram
        mock_meter.create_up_down_counter.return_value = mock_updown_counter
        mock_get_meter.return_value = mock_meter

        yield {
            'tracer': mock_tracer,
            'meter': mock_meter,
            'span': mock_span,
            'counter': mock_counter,
            'histogram': mock_histogram,
            'updown_counter': mock_updown_counter
        }


@pytest.fixture(scope="function")
def mock_requests():
    """Mock HTTP requests for testing."""
    with patch('requests.get') as mock_get, \
         patch('requests.post') as mock_post, \
         patch('httpx.AsyncClient') as mock_client:

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'status': 'success'}
        mock_response.text = 'Success response'
        mock_get.return_value = mock_response
        mock_post.return_value = mock_response

        mock_async_response = Mock()
        mock_async_response.status_code = 200
        mock_async_response.json = Mock(return_value=asyncio.Future())
        mock_async_response.json.return_value.set_result({'status': 'success'})

        mock_client_instance = Mock()
        mock_client_instance.get = Mock(return_value=asyncio.Future())
        mock_client_instance.get.return_value.set_result(mock_async_response)
        mock_client_instance.post = Mock(return_value=asyncio.Future())
        mock_client_instance.post.return_value.set_result(mock_async_response)
        mock_client.return_value.__aenter__ = Mock(return_value=mock_client_instance)
        mock_client.return_value.__aexit__ = Mock(return_value=None)

        yield {
            'get': mock_get,
            'post': mock_post,
            'async_client': mock_client_instance
        }


# Test utilities
def assert_dict_contains(actual: Dict[str, Any], expected: Dict[str, Any]):
    """Assert that actual dict contains all expected key-value pairs."""
    for key, value in expected.items():
        assert key in actual, f"Key '{key}' not found in actual dict"
        assert actual[key] == value, f"Value for key '{key}' mismatch: expected {value}, got {actual[key]}"


def assert_list_contains(actual: list, expected: list):
    """Assert that actual list contains all expected items."""
    for item in expected:
        assert item in actual, f"Item '{item}' not found in actual list"


async def async_test_wrapper(coro):
    """Wrapper for running async tests."""
    return await coro


# Database test utilities
def create_test_database_schema(cursor):
    """Create test database schema."""
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS test_bills (
            id SERIAL PRIMARY KEY,
            bill_id VARCHAR(50) UNIQUE,
            title TEXT,
            status VARCHAR(50),
            jurisdiction VARCHAR(50),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS test_members (
            id SERIAL PRIMARY KEY,
            member_id VARCHAR(50) UNIQUE,
            name VARCHAR(255),
            party VARCHAR(50),
            state VARCHAR(10),
            jurisdiction VARCHAR(50),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS test_votes (
            id SERIAL PRIMARY KEY,
            vote_id VARCHAR(50) UNIQUE,
            bill_id VARCHAR(50),
            result VARCHAR(50),
            jurisdiction VARCHAR(50),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)


def cleanup_test_database(cursor):
    """Clean up test database."""
    cursor.execute("""
        DROP TABLE IF EXISTS test_votes;
        DROP TABLE IF EXISTS test_members;
        DROP TABLE IF EXISTS test_bills;
    """)