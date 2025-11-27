"""
Unit tests for mcp_servers.base module.

Tests cover:
- PaginationConfig behavior and advance logic
- MCPBulkIngestor pagination (offset and page modes)
- Rate limiting behavior
- The _pluck method for navigating nested JSON
- Error conditions (network failures, invalid JSON, missing keys)
- Fallback behavior for result keys
"""

import pytest
import time
from unittest.mock import Mock, patch, MagicMock
from requests.exceptions import HTTPError, ConnectionError, Timeout

from mcp_servers.base import PaginationConfig, EndpointConfig, MCPBulkIngestor


class TestPaginationConfig:
    """Tests for PaginationConfig dataclass."""

    def test_default_values(self):
        """Test default pagination config values."""
        config = PaginationConfig()
        assert config.kind == "offset"
        assert config.page_param == "offset"
        assert config.page_size_param == "limit"
        assert config.start == 0
        assert config.page_size == 100
        assert config.results_path == ("results",)
        assert config.total_path is None
        assert config.max_pages is None

    def test_advance_offset_mode(self):
        """Test advance method in offset mode."""
        config = PaginationConfig(kind="offset")
        # current=0, batch_count=100 -> next should be 100
        assert config.advance(0, 100) == 100
        # current=100, batch_count=50 -> next should be 150
        assert config.advance(100, 50) == 150
        # current=200, batch_count=0 -> next should be 200
        assert config.advance(200, 0) == 200

    def test_advance_page_mode(self):
        """Test advance method in page mode."""
        config = PaginationConfig(kind="page")
        # In page mode, always advances by 1 regardless of batch count
        assert config.advance(0, 100) == 1
        assert config.advance(1, 50) == 2
        assert config.advance(5, 0) == 6


class TestEndpointConfig:
    """Tests for EndpointConfig dataclass."""

    def test_default_values(self):
        """Test default endpoint config values."""
        pagination = PaginationConfig()
        config = EndpointConfig(name="test", path="/api/test", pagination=pagination)
        assert config.name == "test"
        assert config.path == "/api/test"
        assert config.description == ""
        assert config.extra_params == {}
        assert config.result_key_fallbacks == ("results", "data", "items")

    def test_custom_values(self):
        """Test custom endpoint config values."""
        pagination = PaginationConfig(kind="page", page_size=50)
        config = EndpointConfig(
            name="custom",
            path="/api/custom",
            pagination=pagination,
            description="Custom endpoint",
            extra_params={"filter": "active"},
            result_key_fallbacks=("records", "entries"),
        )
        assert config.name == "custom"
        assert config.description == "Custom endpoint"
        assert config.extra_params == {"filter": "active"}
        assert config.result_key_fallbacks == ("records", "entries")


class TestMCPBulkIngestorPluck:
    """Tests for MCPBulkIngestor._pluck static method."""

    def test_pluck_single_key(self):
        """Test pluck with single key path."""
        data = {"results": [1, 2, 3]}
        assert MCPBulkIngestor._pluck(data, ("results",)) == [1, 2, 3]

    def test_pluck_nested_path(self):
        """Test pluck with nested path."""
        data = {"response": {"data": {"items": ["a", "b", "c"]}}}
        assert MCPBulkIngestor._pluck(data, ("response", "data", "items")) == ["a", "b", "c"]

    def test_pluck_deep_nested(self):
        """Test pluck with deeply nested path."""
        data = {"a": {"b": {"c": {"d": {"e": "deep_value"}}}}}
        assert MCPBulkIngestor._pluck(data, ("a", "b", "c", "d", "e")) == "deep_value"

    def test_pluck_missing_key(self):
        """Test pluck returns None for missing key."""
        data = {"results": [1, 2, 3]}
        assert MCPBulkIngestor._pluck(data, ("missing",)) is None

    def test_pluck_missing_nested_key(self):
        """Test pluck returns None for missing nested key."""
        data = {"response": {"data": {}}}
        assert MCPBulkIngestor._pluck(data, ("response", "data", "items")) is None

    def test_pluck_non_dict_intermediate(self):
        """Test pluck returns None when encountering non-dict intermediate."""
        data = {"response": "not_a_dict"}
        assert MCPBulkIngestor._pluck(data, ("response", "data")) is None

    def test_pluck_empty_path(self):
        """Test pluck with empty path returns original data."""
        data = {"key": "value"}
        assert MCPBulkIngestor._pluck(data, ()) == {"key": "value"}

    def test_pluck_with_various_types(self):
        """Test pluck works with various value types."""
        data = {
            "int_val": 42,
            "str_val": "hello",
            "list_val": [1, 2, 3],
            "dict_val": {"nested": True},
            "none_val": None,
            "bool_val": False,
        }
        assert MCPBulkIngestor._pluck(data, ("int_val",)) == 42
        assert MCPBulkIngestor._pluck(data, ("str_val",)) == "hello"
        assert MCPBulkIngestor._pluck(data, ("list_val",)) == [1, 2, 3]
        assert MCPBulkIngestor._pluck(data, ("dict_val",)) == {"nested": True}
        assert MCPBulkIngestor._pluck(data, ("none_val",)) is None
        assert MCPBulkIngestor._pluck(data, ("bool_val",)) is False


class TestMCPBulkIngestorInit:
    """Tests for MCPBulkIngestor initialization."""

    def test_default_init(self):
        """Test default initialization."""
        ingestor = MCPBulkIngestor("https://api.example.com")
        assert ingestor.base_url == "https://api.example.com"
        assert ingestor.api_key is None
        assert ingestor.api_key_header == "X-Api-Key"
        assert ingestor.rate_limit_per_sec == 3.0
        assert ingestor._last_request_ts is None

    def test_trailing_slash_removed(self):
        """Test trailing slash is removed from base_url."""
        ingestor = MCPBulkIngestor("https://api.example.com/")
        assert ingestor.base_url == "https://api.example.com"

    def test_custom_api_key(self):
        """Test custom API key initialization."""
        ingestor = MCPBulkIngestor(
            "https://api.example.com",
            api_key="test_key",
            api_key_header="Authorization",
        )
        assert ingestor.api_key == "test_key"
        assert ingestor.api_key_header == "Authorization"

    def test_custom_rate_limit(self):
        """Test custom rate limit initialization."""
        ingestor = MCPBulkIngestor(
            "https://api.example.com",
            default_rate_limit_per_sec=10.0,
        )
        assert ingestor.rate_limit_per_sec == 10.0

    def test_custom_session(self):
        """Test custom session initialization."""
        mock_session = Mock()
        ingestor = MCPBulkIngestor(
            "https://api.example.com",
            session=mock_session,
        )
        assert ingestor.session is mock_session


class TestMCPBulkIngestorHeaders:
    """Tests for MCPBulkIngestor._headers method."""

    def test_headers_without_api_key(self):
        """Test headers without API key."""
        ingestor = MCPBulkIngestor("https://api.example.com")
        headers = ingestor._headers()
        assert headers == {"Accept": "application/json"}

    def test_headers_with_api_key(self):
        """Test headers with API key."""
        ingestor = MCPBulkIngestor(
            "https://api.example.com",
            api_key="test_key",
        )
        headers = ingestor._headers()
        assert headers == {"Accept": "application/json", "X-Api-Key": "test_key"}

    def test_headers_with_custom_api_key_header(self):
        """Test headers with custom API key header."""
        ingestor = MCPBulkIngestor(
            "https://api.example.com",
            api_key="Bearer token123",
            api_key_header="Authorization",
        )
        headers = ingestor._headers()
        assert headers == {
            "Accept": "application/json",
            "Authorization": "Bearer token123",
        }


class TestMCPBulkIngestorRateLimiting:
    """Tests for MCPBulkIngestor rate limiting."""

    def test_throttle_first_request_no_delay(self):
        """Test first request has no throttle delay."""
        ingestor = MCPBulkIngestor("https://api.example.com")
        start = time.time()
        ingestor._throttle()
        elapsed = time.time() - start
        # Should be nearly instant for first request
        assert elapsed < 0.01

    @patch("time.sleep")
    @patch("time.time")
    def test_throttle_applies_delay_when_needed(self, mock_time, mock_sleep):
        """Test throttle applies delay when requests are too fast."""
        ingestor = MCPBulkIngestor(
            "https://api.example.com",
            default_rate_limit_per_sec=2.0,  # 0.5 seconds between requests
        )
        # Simulate that last request was 0.2 seconds ago
        ingestor._last_request_ts = 100.0
        mock_time.return_value = 100.2  # 0.2 seconds elapsed

        ingestor._throttle()

        # min_interval is 0.5, elapsed is 0.2, so should sleep for 0.3
        mock_sleep.assert_called_once()
        sleep_arg = mock_sleep.call_args[0][0]
        assert abs(sleep_arg - 0.3) < 0.001

    @patch("time.sleep")
    @patch("time.time")
    def test_throttle_no_delay_when_sufficient_time_passed(self, mock_time, mock_sleep):
        """Test no delay when sufficient time has passed."""
        ingestor = MCPBulkIngestor(
            "https://api.example.com",
            default_rate_limit_per_sec=2.0,  # 0.5 seconds between requests
        )
        # Simulate that last request was 1 second ago (enough time)
        ingestor._last_request_ts = 100.0
        mock_time.return_value = 101.0  # 1 second elapsed

        ingestor._throttle()

        # Should not sleep because enough time has passed
        mock_sleep.assert_not_called()


class TestMCPBulkIngestorRequest:
    """Tests for MCPBulkIngestor.request method."""

    def test_request_success(self):
        """Test successful request."""
        mock_session = Mock()
        mock_response = Mock()
        mock_response.json.return_value = {"results": [1, 2, 3]}
        mock_session.get.return_value = mock_response

        ingestor = MCPBulkIngestor(
            "https://api.example.com",
            session=mock_session,
        )
        result = ingestor.request("/api/test", {"param": "value"})

        assert result == {"results": [1, 2, 3]}
        mock_session.get.assert_called_once_with(
            "https://api.example.com/api/test",
            headers={"Accept": "application/json"},
            params={"param": "value"},
            timeout=60,
        )
        mock_response.raise_for_status.assert_called_once()

    def test_request_with_api_key(self):
        """Test request includes API key."""
        mock_session = Mock()
        mock_response = Mock()
        mock_response.json.return_value = {}
        mock_session.get.return_value = mock_response

        ingestor = MCPBulkIngestor(
            "https://api.example.com",
            api_key="test_key",
            session=mock_session,
        )
        ingestor.request("/api/test", {})

        call_args = mock_session.get.call_args
        assert call_args[1]["headers"]["X-Api-Key"] == "test_key"

    def test_request_http_error(self):
        """Test request raises HTTPError on failure."""
        mock_session = Mock()
        mock_response = Mock()
        mock_response.raise_for_status.side_effect = HTTPError("404 Not Found")
        mock_session.get.return_value = mock_response

        ingestor = MCPBulkIngestor(
            "https://api.example.com",
            session=mock_session,
        )

        with pytest.raises(HTTPError):
            ingestor.request("/api/test", {})

    def test_request_connection_error(self):
        """Test request raises ConnectionError on network failure."""
        mock_session = Mock()
        mock_session.get.side_effect = ConnectionError("Connection refused")

        ingestor = MCPBulkIngestor(
            "https://api.example.com",
            session=mock_session,
        )

        with pytest.raises(ConnectionError):
            ingestor.request("/api/test", {})

    def test_request_timeout(self):
        """Test request raises Timeout on timeout."""
        mock_session = Mock()
        mock_session.get.side_effect = Timeout("Request timed out")

        ingestor = MCPBulkIngestor(
            "https://api.example.com",
            session=mock_session,
        )

        with pytest.raises(Timeout):
            ingestor.request("/api/test", {})

    def test_request_invalid_json(self):
        """Test request raises error on invalid JSON."""
        mock_session = Mock()
        mock_response = Mock()
        mock_response.json.side_effect = ValueError("Invalid JSON")
        mock_session.get.return_value = mock_response

        ingestor = MCPBulkIngestor(
            "https://api.example.com",
            session=mock_session,
        )

        with pytest.raises(ValueError):
            ingestor.request("/api/test", {})

    def test_request_updates_last_request_timestamp(self):
        """Test request updates last request timestamp."""
        mock_session = Mock()
        mock_response = Mock()
        mock_response.json.return_value = {}
        mock_session.get.return_value = mock_response

        ingestor = MCPBulkIngestor(
            "https://api.example.com",
            session=mock_session,
        )
        assert ingestor._last_request_ts is None

        ingestor.request("/api/test", {})

        assert ingestor._last_request_ts is not None


class TestMCPBulkIngestorFetchPaginated:
    """Tests for MCPBulkIngestor.fetch_paginated method."""

    def test_fetch_paginated_offset_mode(self):
        """Test offset-based pagination."""
        mock_session = Mock()
        
        # Simulate 2 pages of items, then empty page (which is also yielded before break)
        responses = [
            {"results": list(range(100))},  # First page - 100 items
            {"results": list(range(50))},   # Second page - 50 items  
            {"results": []},                 # Third page - empty (yielded before break)
        ]
        mock_response = Mock()
        mock_response.json.side_effect = responses
        mock_session.get.return_value = mock_response

        ingestor = MCPBulkIngestor(
            "https://api.example.com",
            session=mock_session,
        )

        pagination = PaginationConfig(kind="offset", page_size=100)
        endpoint = EndpointConfig(name="test", path="/api/test", pagination=pagination)

        pages = list(ingestor.fetch_paginated(endpoint))

        # All 3 pages are yielded (including empty page before break)
        assert len(pages) == 3
        assert pages[0]["offset"] == 0
        assert len(pages[0]["results"]) == 100
        assert pages[1]["offset"] == 100
        assert len(pages[1]["results"]) == 50
        assert pages[2]["offset"] == 150
        assert len(pages[2]["results"]) == 0

    def test_fetch_paginated_page_mode(self):
        """Test page-based pagination."""
        mock_session = Mock()
        
        responses = [
            {"data": [{"id": 1}, {"id": 2}]},  # Page 1
            {"data": [{"id": 3}]},              # Page 2
            {"data": []},                        # Page 3 (empty, yielded before break)
        ]
        mock_response = Mock()
        mock_response.json.side_effect = responses
        mock_session.get.return_value = mock_response

        ingestor = MCPBulkIngestor(
            "https://api.example.com",
            session=mock_session,
        )

        pagination = PaginationConfig(
            kind="page",
            page_param="page",
            start=1,
            results_path=("data",),
        )
        endpoint = EndpointConfig(name="test", path="/api/test", pagination=pagination)

        pages = list(ingestor.fetch_paginated(endpoint))

        # All 3 pages are yielded (including empty page before break)
        assert len(pages) == 3
        assert pages[0]["offset"] == 1  # Page 1
        assert pages[1]["offset"] == 2  # Page 2
        assert pages[2]["offset"] == 3  # Page 3 (empty)

    def test_fetch_paginated_with_max_pages(self):
        """Test max_pages limit."""
        mock_session = Mock()
        
        # Return 100 items for each request (would normally continue)
        mock_response = Mock()
        mock_response.json.return_value = {"results": list(range(100))}
        mock_session.get.return_value = mock_response

        ingestor = MCPBulkIngestor(
            "https://api.example.com",
            session=mock_session,
        )

        pagination = PaginationConfig(kind="offset", page_size=100)
        endpoint = EndpointConfig(name="test", path="/api/test", pagination=pagination)

        pages = list(ingestor.fetch_paginated(endpoint, max_pages=2))

        assert len(pages) == 2

    def test_fetch_paginated_with_total_path(self):
        """Test pagination stops when total is reached."""
        mock_session = Mock()
        
        responses = [
            {"results": list(range(100)), "meta": {"total": 150}},
            {"results": list(range(50)), "meta": {"total": 150}},
        ]
        mock_response = Mock()
        mock_response.json.side_effect = responses
        mock_session.get.return_value = mock_response

        ingestor = MCPBulkIngestor(
            "https://api.example.com",
            session=mock_session,
        )

        pagination = PaginationConfig(
            kind="offset",
            page_size=100,
            total_path=("meta", "total"),
        )
        endpoint = EndpointConfig(name="test", path="/api/test", pagination=pagination)

        pages = list(ingestor.fetch_paginated(endpoint))

        assert len(pages) == 2
        assert pages[0]["total"] == 150
        assert pages[1]["total"] == 150

    def test_fetch_paginated_fallback_keys(self):
        """Test fallback result keys when results_path not found."""
        mock_session = Mock()
        
        # Response without "results" key, but has "data"
        mock_response = Mock()
        mock_response.json.return_value = {"data": [{"id": 1}]}
        mock_session.get.return_value = mock_response

        ingestor = MCPBulkIngestor(
            "https://api.example.com",
            session=mock_session,
        )

        pagination = PaginationConfig(results_path=("nonexistent",))
        endpoint = EndpointConfig(
            name="test",
            path="/api/test",
            pagination=pagination,
            result_key_fallbacks=("results", "data", "items"),
        )

        pages = list(ingestor.fetch_paginated(endpoint, max_pages=1))

        assert len(pages) == 1
        assert pages[0]["results"] == [{"id": 1}]

    def test_fetch_paginated_fallback_to_items(self):
        """Test fallback to 'items' key."""
        mock_session = Mock()
        
        mock_response = Mock()
        mock_response.json.return_value = {"items": [{"id": 1}, {"id": 2}]}
        mock_session.get.return_value = mock_response

        ingestor = MCPBulkIngestor(
            "https://api.example.com",
            session=mock_session,
        )

        pagination = PaginationConfig(results_path=("nonexistent",))
        endpoint = EndpointConfig(
            name="test",
            path="/api/test",
            pagination=pagination,
            result_key_fallbacks=("results", "data", "items"),
        )

        pages = list(ingestor.fetch_paginated(endpoint, max_pages=1))

        assert pages[0]["results"] == [{"id": 1}, {"id": 2}]

    def test_fetch_paginated_empty_fallback(self):
        """Test that empty list is returned when no results found."""
        mock_session = Mock()
        
        mock_response = Mock()
        mock_response.json.return_value = {"unknown_key": [1, 2, 3]}
        mock_session.get.return_value = mock_response

        ingestor = MCPBulkIngestor(
            "https://api.example.com",
            session=mock_session,
        )

        pagination = PaginationConfig(results_path=("nonexistent",))
        endpoint = EndpointConfig(
            name="test",
            path="/api/test",
            pagination=pagination,
            result_key_fallbacks=("results", "data"),
        )

        pages = list(ingestor.fetch_paginated(endpoint))

        # Should get one page with empty results, which stops pagination
        assert len(pages) == 1
        assert pages[0]["results"] == []

    def test_fetch_paginated_with_extra_params(self):
        """Test extra parameters are passed correctly."""
        mock_session = Mock()
        
        mock_response = Mock()
        mock_response.json.return_value = {"results": []}
        mock_session.get.return_value = mock_response

        ingestor = MCPBulkIngestor(
            "https://api.example.com",
            session=mock_session,
        )

        pagination = PaginationConfig(page_size=50)
        endpoint = EndpointConfig(
            name="test",
            path="/api/test",
            pagination=pagination,
            extra_params={"filter": "active"},
        )

        list(ingestor.fetch_paginated(endpoint, extra_params={"sort": "date"}))

        call_args = mock_session.get.call_args
        params = call_args[1]["params"]
        assert params["filter"] == "active"
        assert params["sort"] == "date"
        assert params["offset"] == 0
        assert params["limit"] == 50

    def test_fetch_paginated_custom_start_and_page_size(self):
        """Test custom start offset and page size."""
        mock_session = Mock()
        
        mock_response = Mock()
        mock_response.json.return_value = {"results": []}
        mock_session.get.return_value = mock_response

        ingestor = MCPBulkIngestor(
            "https://api.example.com",
            session=mock_session,
        )

        pagination = PaginationConfig()
        endpoint = EndpointConfig(name="test", path="/api/test", pagination=pagination)

        list(ingestor.fetch_paginated(endpoint, start=50, page_size=25))

        call_args = mock_session.get.call_args
        params = call_args[1]["params"]
        assert params["offset"] == 50
        assert params["limit"] == 25


class TestMCPBulkIngestorIngestEndpoints:
    """Tests for MCPBulkIngestor.ingest_endpoints method."""

    def test_ingest_multiple_endpoints(self):
        """Test ingesting multiple endpoints."""
        mock_session = Mock()
        
        # First endpoint returns 2 pages
        # Second endpoint returns 1 page
        responses = [
            {"results": list(range(10))},  # endpoint1 page1
            {"results": []},               # endpoint1 done
            {"results": list(range(5))},   # endpoint2 page1
            {"results": []},               # endpoint2 done
        ]
        mock_response = Mock()
        mock_response.json.side_effect = responses
        mock_session.get.return_value = mock_response

        ingestor = MCPBulkIngestor(
            "https://api.example.com",
            session=mock_session,
        )

        pagination = PaginationConfig()
        endpoints = [
            EndpointConfig(name="endpoint1", path="/api/endpoint1", pagination=pagination),
            EndpointConfig(name="endpoint2", path="/api/endpoint2", pagination=pagination),
        ]

        counts = ingestor.ingest_endpoints(endpoints)

        assert counts == {"endpoint1": 10, "endpoint2": 5}

    def test_ingest_endpoints_with_overrides(self):
        """Test ingesting endpoints with start offsets and page size overrides."""
        mock_session = Mock()
        
        mock_response = Mock()
        mock_response.json.return_value = {"results": []}
        mock_session.get.return_value = mock_response

        ingestor = MCPBulkIngestor(
            "https://api.example.com",
            session=mock_session,
        )

        pagination = PaginationConfig()
        endpoints = [
            EndpointConfig(name="test", path="/api/test", pagination=pagination),
        ]

        ingestor.ingest_endpoints(
            endpoints,
            start_offsets={"test": 100},
            page_size_overrides={"test": 25},
        )

        call_args = mock_session.get.call_args
        params = call_args[1]["params"]
        assert params["offset"] == 100
        assert params["limit"] == 25

    def test_ingest_endpoints_with_max_pages(self):
        """Test max_pages is respected during ingestion."""
        mock_session = Mock()
        
        mock_response = Mock()
        mock_response.json.return_value = {"results": list(range(100))}
        mock_session.get.return_value = mock_response

        ingestor = MCPBulkIngestor(
            "https://api.example.com",
            session=mock_session,
        )

        pagination = PaginationConfig(page_size=100)
        endpoints = [
            EndpointConfig(name="test", path="/api/test", pagination=pagination),
        ]

        counts = ingestor.ingest_endpoints(endpoints, max_pages=3)

        # Should have fetched 3 pages of 100 items each
        assert counts == {"test": 300}

    def test_ingest_endpoints_handles_non_list_results(self):
        """Test handling of non-list results."""
        mock_session = Mock()
        
        responses = [
            {"results": {"key": "value"}},  # Not a list
            {"results": []},
        ]
        mock_response = Mock()
        mock_response.json.side_effect = responses
        mock_session.get.return_value = mock_response

        ingestor = MCPBulkIngestor(
            "https://api.example.com",
            session=mock_session,
        )

        pagination = PaginationConfig()
        endpoints = [
            EndpointConfig(name="test", path="/api/test", pagination=pagination),
        ]

        counts = ingestor.ingest_endpoints(endpoints)

        # Non-list results should count as 0
        assert counts == {"test": 0}


class TestMCPBulkIngestorEdgeCases:
    """Tests for edge cases and error handling."""

    def test_empty_endpoint_list(self):
        """Test ingesting with empty endpoint list."""
        ingestor = MCPBulkIngestor("https://api.example.com")
        counts = ingestor.ingest_endpoints([])
        assert counts == {}

    def test_payload_is_list_not_dict(self):
        """Test handling when API returns a list directly."""
        mock_session = Mock()
        
        responses = [
            [{"id": 1}, {"id": 2}],  # List, not dict - 2 items
            [],                       # Empty list - yielded before break
        ]
        mock_response = Mock()
        mock_response.json.side_effect = responses
        mock_session.get.return_value = mock_response

        ingestor = MCPBulkIngestor(
            "https://api.example.com",
            session=mock_session,
        )

        pagination = PaginationConfig(results_path=("nonexistent",))
        endpoint = EndpointConfig(name="test", path="/api/test", pagination=pagination)

        pages = list(ingestor.fetch_paginated(endpoint))

        # Both pages are yielded (including empty page before break)
        assert len(pages) == 2
        assert pages[0]["results"] == [{"id": 1}, {"id": 2}]
        assert pages[1]["results"] == []

    def test_results_path_with_none_value(self):
        """Test handling when results_path leads to None."""
        mock_session = Mock()
        
        mock_response = Mock()
        mock_response.json.return_value = {"results": None}
        mock_session.get.return_value = mock_response

        ingestor = MCPBulkIngestor(
            "https://api.example.com",
            session=mock_session,
        )

        pagination = PaginationConfig(results_path=("results",))
        endpoint = EndpointConfig(name="test", path="/api/test", pagination=pagination)

        pages = list(ingestor.fetch_paginated(endpoint))

        # None results should be converted to empty list
        assert len(pages) == 1
        assert pages[0]["results"] == []

    def test_total_path_non_integer(self):
        """Test handling when total_path yields non-integer value."""
        mock_session = Mock()
        
        mock_response = Mock()
        mock_response.json.return_value = {
            "results": [1],
            "meta": {"total": "not_an_int"},
        }
        mock_session.get.return_value = mock_response

        ingestor = MCPBulkIngestor(
            "https://api.example.com",
            session=mock_session,
        )

        pagination = PaginationConfig(
            total_path=("meta", "total"),
        )
        endpoint = EndpointConfig(name="test", path="/api/test", pagination=pagination)

        pages = list(ingestor.fetch_paginated(endpoint, max_pages=1))

        # Total should remain None if not an integer
        assert pages[0]["total"] is None


class TestModuleExports:
    """Test module exports."""

    def test_all_exports(self):
        """Test __all__ exports correct symbols."""
        from mcp_servers import base
        assert "PaginationConfig" in base.__all__
        assert "EndpointConfig" in base.__all__
        assert "MCPBulkIngestor" in base.__all__
        assert len(base.__all__) == 3
