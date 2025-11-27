"""
Unit tests for MCP bulk ingestion base module.

These tests verify pagination, throttling, error handling, and header injection
prevention without making live API calls, as recommended in SRS line 14.
"""

import json
import time
import pytest
from unittest.mock import Mock, patch, MagicMock


class TestPaginationConfig:
    """Test PaginationConfig class."""

    def test_default_values(self):
        """Test that PaginationConfig has sensible defaults."""
        from mcp_servers.base import PaginationConfig

        config = PaginationConfig()
        assert config.kind == "offset"
        assert config.page_param == "offset"
        assert config.page_size_param == "limit"
        assert config.start == 0
        assert config.page_size == 100
        assert config.results_path == ("results",)
        assert config.total_path is None
        assert config.max_pages is None

    def test_advance_offset_pagination(self):
        """Test advance method for offset-based pagination."""
        from mcp_servers.base import PaginationConfig

        config = PaginationConfig(kind="offset")
        # With offset pagination, advance adds batch_count to current
        assert config.advance(0, 100) == 100
        assert config.advance(100, 50) == 150
        assert config.advance(200, 0) == 200

    def test_advance_page_pagination(self):
        """Test advance method for page-based pagination."""
        from mcp_servers.base import PaginationConfig

        config = PaginationConfig(kind="page")
        # With page pagination, advance increments by 1
        assert config.advance(0, 100) == 1
        assert config.advance(1, 50) == 2
        assert config.advance(5, 0) == 6


class TestEndpointConfig:
    """Test EndpointConfig class."""

    def test_default_values(self):
        """Test EndpointConfig defaults."""
        from mcp_servers.base import EndpointConfig, PaginationConfig

        config = EndpointConfig(
            name="test",
            path="/api/test",
            pagination=PaginationConfig(),
        )
        assert config.name == "test"
        assert config.path == "/api/test"
        assert config.description == ""
        assert config.extra_params == {}
        assert config.result_key_fallbacks == ("results", "data", "items")

    def test_custom_values(self):
        """Test EndpointConfig with custom values."""
        from mcp_servers.base import EndpointConfig, PaginationConfig

        pagination = PaginationConfig(kind="page", page_param="page")
        config = EndpointConfig(
            name="bills",
            path="/api/bills",
            pagination=pagination,
            description="Bill endpoint",
            extra_params={"format": "json"},
            result_key_fallbacks=("bills", "records"),
        )
        assert config.name == "bills"
        assert config.description == "Bill endpoint"
        assert config.extra_params == {"format": "json"}
        assert config.result_key_fallbacks == ("bills", "records")


class TestMCPBulkIngestorInit:
    """Test MCPBulkIngestor initialization."""

    def test_default_init(self):
        """Test default initialization."""
        from mcp_servers.base import MCPBulkIngestor

        ingestor = MCPBulkIngestor(base_url="https://api.example.com")
        assert ingestor.base_url == "https://api.example.com"
        assert ingestor.api_key is None
        assert ingestor.api_key_header == "X-Api-Key"
        assert ingestor.rate_limit_per_sec == 3.0
        assert ingestor._last_request_ts is None

    def test_trailing_slash_removed(self):
        """Test that trailing slashes are stripped from base_url."""
        from mcp_servers.base import MCPBulkIngestor

        ingestor = MCPBulkIngestor(base_url="https://api.example.com/")
        assert ingestor.base_url == "https://api.example.com"

    def test_custom_session(self):
        """Test custom session injection."""
        from mcp_servers.base import MCPBulkIngestor

        mock_session = Mock()
        ingestor = MCPBulkIngestor(
            base_url="https://api.example.com",
            session=mock_session,
        )
        assert ingestor.session is mock_session


class TestMCPBulkIngestorHeaders:
    """Test header generation and injection prevention."""

    def test_headers_without_api_key(self):
        """Test headers without API key."""
        from mcp_servers.base import MCPBulkIngestor

        ingestor = MCPBulkIngestor(base_url="https://api.example.com")
        headers = ingestor._headers()
        assert headers == {"Accept": "application/json"}

    def test_headers_with_api_key(self):
        """Test headers with valid API key."""
        from mcp_servers.base import MCPBulkIngestor

        ingestor = MCPBulkIngestor(
            base_url="https://api.example.com",
            api_key="test-api-key-123",
        )
        headers = ingestor._headers()
        assert headers["Accept"] == "application/json"
        assert headers["X-Api-Key"] == "test-api-key-123"

    def test_headers_with_custom_header_name(self):
        """Test headers with custom API key header name."""
        from mcp_servers.base import MCPBulkIngestor

        ingestor = MCPBulkIngestor(
            base_url="https://api.example.com",
            api_key="test-key",
            api_key_header="Authorization",
        )
        headers = ingestor._headers()
        assert headers["Authorization"] == "test-key"

    def test_header_injection_newline_rejected(self):
        """Test that newline characters in API key are rejected."""
        from mcp_servers.base import MCPBulkIngestor

        ingestor = MCPBulkIngestor(
            base_url="https://api.example.com",
            api_key="valid-key\nX-Injected: malicious",
        )
        with pytest.raises(ValueError, match="invalid characters"):
            ingestor._headers()

    def test_header_injection_carriage_return_rejected(self):
        """Test that carriage return characters in API key are rejected."""
        from mcp_servers.base import MCPBulkIngestor

        ingestor = MCPBulkIngestor(
            base_url="https://api.example.com",
            api_key="valid-key\rX-Injected: malicious",
        )
        with pytest.raises(ValueError, match="invalid characters"):
            ingestor._headers()

    def test_empty_api_key_rejected(self):
        """Test that empty API keys are rejected."""
        from mcp_servers.base import MCPBulkIngestor

        ingestor = MCPBulkIngestor(
            base_url="https://api.example.com",
            api_key="   ",  # Whitespace only
        )
        with pytest.raises(ValueError, match="empty or whitespace"):
            ingestor._headers()

    def test_whitespace_stripped_from_api_key(self):
        """Test that leading/trailing whitespace is stripped from API key."""
        from mcp_servers.base import MCPBulkIngestor

        ingestor = MCPBulkIngestor(
            base_url="https://api.example.com",
            api_key="  valid-key  ",
        )
        headers = ingestor._headers()
        assert headers["X-Api-Key"] == "valid-key"


class TestMCPBulkIngestorThrottling:
    """Test rate limiting/throttling behavior."""

    def test_no_throttle_on_first_request(self):
        """Test that first request has no throttle delay."""
        from mcp_servers.base import MCPBulkIngestor

        ingestor = MCPBulkIngestor(
            base_url="https://api.example.com",
            default_rate_limit_per_sec=10.0,
        )
        start = time.time()
        ingestor._throttle()
        elapsed = time.time() - start
        # First request should not sleep
        assert elapsed < 0.05

    @patch("time.sleep")
    def test_throttle_sleeps_when_too_fast(self, mock_sleep):
        """Test that throttle sleeps when requests are too fast."""
        from mcp_servers.base import MCPBulkIngestor

        ingestor = MCPBulkIngestor(
            base_url="https://api.example.com",
            default_rate_limit_per_sec=10.0,  # min interval = 0.1s
        )
        # Simulate a recent request
        ingestor._last_request_ts = time.time()

        ingestor._throttle()

        # Should have called sleep
        mock_sleep.assert_called_once()
        sleep_time = mock_sleep.call_args[0][0]
        # Sleep time should be close to min_interval (0.1s)
        assert 0.05 < sleep_time <= 0.1

    @patch("time.sleep")
    def test_no_throttle_when_enough_time_elapsed(self, mock_sleep):
        """Test no throttle when enough time has passed."""
        from mcp_servers.base import MCPBulkIngestor

        ingestor = MCPBulkIngestor(
            base_url="https://api.example.com",
            default_rate_limit_per_sec=10.0,  # min interval = 0.1s
        )
        # Simulate request from 1 second ago
        ingestor._last_request_ts = time.time() - 1.0

        ingestor._throttle()

        # Should not have called sleep
        mock_sleep.assert_not_called()


class TestMCPBulkIngestorRequest:
    """Test the request method."""

    def test_request_success(self):
        """Test successful request."""
        from mcp_servers.base import MCPBulkIngestor

        mock_session = Mock()
        mock_response = Mock()
        mock_response.json.return_value = {"results": [1, 2, 3]}
        mock_response.raise_for_status = Mock()
        mock_session.get.return_value = mock_response

        ingestor = MCPBulkIngestor(
            base_url="https://api.example.com",
            api_key="test-key",
            session=mock_session,
        )

        result = ingestor.request("/test", {"param": "value"})

        assert result == {"results": [1, 2, 3]}
        mock_session.get.assert_called_once_with(
            "https://api.example.com/test",
            headers={"Accept": "application/json", "X-Api-Key": "test-key"},
            params={"param": "value"},
            timeout=60,
        )
        mock_response.raise_for_status.assert_called_once()

    def test_request_updates_last_timestamp(self):
        """Test that request updates _last_request_ts."""
        from mcp_servers.base import MCPBulkIngestor

        mock_session = Mock()
        mock_response = Mock()
        mock_response.json.return_value = {}
        mock_response.raise_for_status = Mock()
        mock_session.get.return_value = mock_response

        ingestor = MCPBulkIngestor(
            base_url="https://api.example.com",
            session=mock_session,
        )
        assert ingestor._last_request_ts is None

        ingestor.request("/test", {})

        assert ingestor._last_request_ts is not None
        assert time.time() - ingestor._last_request_ts < 1.0

    def test_request_http_error(self):
        """Test request raises on HTTP error."""
        import requests
        from mcp_servers.base import MCPBulkIngestor

        mock_session = Mock()
        mock_response = Mock()
        mock_response.raise_for_status.side_effect = requests.HTTPError("404 Not Found")
        mock_session.get.return_value = mock_response

        ingestor = MCPBulkIngestor(
            base_url="https://api.example.com",
            session=mock_session,
        )

        with pytest.raises(requests.HTTPError):
            ingestor.request("/nonexistent", {})


class TestMCPBulkIngestorPluck:
    """Test the _pluck static method for extracting nested data."""

    def test_pluck_single_level(self):
        """Test plucking single level key."""
        from mcp_servers.base import MCPBulkIngestor

        data = {"results": [1, 2, 3]}
        result = MCPBulkIngestor._pluck(data, ("results",))
        assert result == [1, 2, 3]

    def test_pluck_nested(self):
        """Test plucking nested keys."""
        from mcp_servers.base import MCPBulkIngestor

        data = {"response": {"data": {"items": [1, 2, 3]}}}
        result = MCPBulkIngestor._pluck(data, ("response", "data", "items"))
        assert result == [1, 2, 3]

    def test_pluck_missing_key(self):
        """Test plucking with missing key returns None."""
        from mcp_servers.base import MCPBulkIngestor

        data = {"other": "value"}
        result = MCPBulkIngestor._pluck(data, ("results",))
        assert result is None

    def test_pluck_non_dict_intermediate(self):
        """Test plucking when intermediate value is not a dict."""
        from mcp_servers.base import MCPBulkIngestor

        data = {"results": "not a dict"}
        result = MCPBulkIngestor._pluck(data, ("results", "nested"))
        assert result is None

    def test_pluck_empty_path(self):
        """Test plucking with empty path returns the data itself."""
        from mcp_servers.base import MCPBulkIngestor

        data = {"results": [1, 2, 3]}
        result = MCPBulkIngestor._pluck(data, ())
        assert result == data


class TestMCPBulkIngestorFetchPaginated:
    """Test the fetch_paginated method."""

    def test_fetch_single_page(self):
        """Test fetching a single page of results."""
        from mcp_servers.base import MCPBulkIngestor, PaginationConfig, EndpointConfig

        mock_session = Mock()
        mock_response = Mock()
        mock_response.json.return_value = {"results": [{"id": 1}, {"id": 2}]}
        mock_response.raise_for_status = Mock()
        mock_session.get.return_value = mock_response

        ingestor = MCPBulkIngestor(
            base_url="https://api.example.com",
            session=mock_session,
        )

        endpoint = EndpointConfig(
            name="test",
            path="/api/items",
            pagination=PaginationConfig(max_pages=1),
        )

        pages = list(ingestor.fetch_paginated(endpoint))

        assert len(pages) == 1
        assert pages[0]["endpoint"] == "test"
        assert pages[0]["results"] == [{"id": 1}, {"id": 2}]
        assert pages[0]["offset"] == 0

    def test_fetch_multiple_pages(self):
        """Test pagination across multiple pages."""
        from mcp_servers.base import MCPBulkIngestor, PaginationConfig, EndpointConfig

        mock_session = Mock()

        # First page has results, second page is empty
        responses = [
            Mock(json=Mock(return_value={"results": [{"id": 1}, {"id": 2}]})),
            Mock(json=Mock(return_value={"results": []})),
        ]
        for r in responses:
            r.raise_for_status = Mock()
        mock_session.get.side_effect = responses

        ingestor = MCPBulkIngestor(
            base_url="https://api.example.com",
            session=mock_session,
        )

        endpoint = EndpointConfig(
            name="test",
            path="/api/items",
            pagination=PaginationConfig(),
        )

        pages = list(ingestor.fetch_paginated(endpoint))

        assert len(pages) == 2
        assert pages[0]["results"] == [{"id": 1}, {"id": 2}]
        assert pages[1]["results"] == []

    def test_fetch_respects_max_pages(self):
        """Test that max_pages limit is respected."""
        from mcp_servers.base import MCPBulkIngestor, PaginationConfig, EndpointConfig

        mock_session = Mock()

        # Return results on every page
        mock_response = Mock()
        mock_response.json.return_value = {"results": [{"id": 1}]}
        mock_response.raise_for_status = Mock()
        mock_session.get.return_value = mock_response

        ingestor = MCPBulkIngestor(
            base_url="https://api.example.com",
            session=mock_session,
        )

        endpoint = EndpointConfig(
            name="test",
            path="/api/items",
            pagination=PaginationConfig(max_pages=3),
        )

        pages = list(ingestor.fetch_paginated(endpoint))

        assert len(pages) == 3
        assert mock_session.get.call_count == 3

    def test_fetch_respects_total_records(self):
        """Test that pagination stops when total is reached."""
        from mcp_servers.base import MCPBulkIngestor, PaginationConfig, EndpointConfig

        mock_session = Mock()

        # First page returns total, second page would exceed
        responses = [
            Mock(json=Mock(return_value={
                "results": [{"id": 1}, {"id": 2}],
                "total": 2,
            })),
        ]
        responses[0].raise_for_status = Mock()
        mock_session.get.side_effect = responses

        ingestor = MCPBulkIngestor(
            base_url="https://api.example.com",
            session=mock_session,
        )

        endpoint = EndpointConfig(
            name="test",
            path="/api/items",
            pagination=PaginationConfig(
                total_path=("total",),
                page_size=10,
            ),
        )

        pages = list(ingestor.fetch_paginated(endpoint))

        # Should stop after first page since offset + batch_count >= total
        assert len(pages) == 1

    def test_fetch_with_fallback_keys(self):
        """Test fallback result keys when primary path is missing."""
        from mcp_servers.base import MCPBulkIngestor, PaginationConfig, EndpointConfig

        mock_session = Mock()
        mock_response = Mock()
        mock_response.json.return_value = {"data": [{"id": 1}]}
        mock_response.raise_for_status = Mock()
        mock_session.get.return_value = mock_response

        ingestor = MCPBulkIngestor(
            base_url="https://api.example.com",
            session=mock_session,
        )

        endpoint = EndpointConfig(
            name="test",
            path="/api/items",
            pagination=PaginationConfig(
                results_path=("nonexistent",),
                max_pages=1,
            ),
        )

        pages = list(ingestor.fetch_paginated(endpoint))

        # Should fall back to "data" key
        assert pages[0]["results"] == [{"id": 1}]

    def test_fetch_with_extra_params(self):
        """Test extra parameters are included in requests."""
        from mcp_servers.base import MCPBulkIngestor, PaginationConfig, EndpointConfig

        mock_session = Mock()
        mock_response = Mock()
        mock_response.json.return_value = {"results": []}
        mock_response.raise_for_status = Mock()
        mock_session.get.return_value = mock_response

        ingestor = MCPBulkIngestor(
            base_url="https://api.example.com",
            session=mock_session,
        )

        endpoint = EndpointConfig(
            name="test",
            path="/api/items",
            pagination=PaginationConfig(max_pages=1),
            extra_params={"format": "json", "api_version": "2"},
        )

        list(ingestor.fetch_paginated(endpoint, extra_params={"filter": "active"}))

        call_args = mock_session.get.call_args
        params = call_args.kwargs["params"]
        assert params["format"] == "json"
        assert params["api_version"] == "2"
        assert params["filter"] == "active"

    def test_fetch_page_based_pagination(self):
        """Test page-based pagination (incrementing page numbers)."""
        from mcp_servers.base import MCPBulkIngestor, PaginationConfig, EndpointConfig

        mock_session = Mock()

        responses = [
            Mock(json=Mock(return_value={"results": [{"id": 1}]})),
            Mock(json=Mock(return_value={"results": [{"id": 2}]})),
            Mock(json=Mock(return_value={"results": []})),
        ]
        for r in responses:
            r.raise_for_status = Mock()
        mock_session.get.side_effect = responses

        ingestor = MCPBulkIngestor(
            base_url="https://api.example.com",
            session=mock_session,
        )

        endpoint = EndpointConfig(
            name="test",
            path="/api/items",
            pagination=PaginationConfig(kind="page", page_param="page", start=1),
        )

        pages = list(ingestor.fetch_paginated(endpoint))

        # Verify that 3 pages were fetched
        assert len(pages) == 3
        # Verify offsets (which track the page numbers) in the returned pages
        assert pages[0]["offset"] == 1
        assert pages[1]["offset"] == 2
        assert pages[2]["offset"] == 3


class TestMCPBulkIngestorIngestEndpoints:
    """Test the ingest_endpoints method."""

    def test_ingest_single_endpoint(self):
        """Test ingesting a single endpoint."""
        from mcp_servers.base import MCPBulkIngestor, PaginationConfig, EndpointConfig

        mock_session = Mock()
        responses = [
            Mock(json=Mock(return_value={"results": [{"id": 1}, {"id": 2}]})),
            Mock(json=Mock(return_value={"results": []})),
        ]
        for r in responses:
            r.raise_for_status = Mock()
        mock_session.get.side_effect = responses

        ingestor = MCPBulkIngestor(
            base_url="https://api.example.com",
            session=mock_session,
        )

        endpoint = EndpointConfig(
            name="items",
            path="/api/items",
            pagination=PaginationConfig(),
        )

        counts = ingestor.ingest_endpoints([endpoint])

        assert counts == {"items": 2}

    def test_ingest_multiple_endpoints(self):
        """Test ingesting multiple endpoints."""
        from mcp_servers.base import MCPBulkIngestor, PaginationConfig, EndpointConfig

        mock_session = Mock()
        responses = [
            # First endpoint
            Mock(json=Mock(return_value={"results": [{"id": 1}]})),
            Mock(json=Mock(return_value={"results": []})),
            # Second endpoint
            Mock(json=Mock(return_value={"results": [{"id": 1}, {"id": 2}, {"id": 3}]})),
            Mock(json=Mock(return_value={"results": []})),
        ]
        for r in responses:
            r.raise_for_status = Mock()
        mock_session.get.side_effect = responses

        ingestor = MCPBulkIngestor(
            base_url="https://api.example.com",
            session=mock_session,
        )

        endpoints = [
            EndpointConfig(
                name="items",
                path="/api/items",
                pagination=PaginationConfig(),
            ),
            EndpointConfig(
                name="users",
                path="/api/users",
                pagination=PaginationConfig(),
            ),
        ]

        counts = ingestor.ingest_endpoints(endpoints)

        assert counts == {"items": 1, "users": 3}

    def test_ingest_with_start_offset(self):
        """Test ingestion with custom start offsets."""
        from mcp_servers.base import MCPBulkIngestor, PaginationConfig, EndpointConfig

        mock_session = Mock()
        mock_response = Mock()
        mock_response.json.return_value = {"results": [{"id": 1}]}
        mock_response.raise_for_status = Mock()
        mock_session.get.return_value = mock_response

        ingestor = MCPBulkIngestor(
            base_url="https://api.example.com",
            session=mock_session,
        )

        endpoint = EndpointConfig(
            name="items",
            path="/api/items",
            pagination=PaginationConfig(max_pages=1),
        )

        ingestor.ingest_endpoints(
            [endpoint],
            start_offsets={"items": 100},
        )

        call_args = mock_session.get.call_args
        params = call_args.kwargs["params"]
        assert params["offset"] == 100

    def test_ingest_with_page_size_override(self):
        """Test ingestion with custom page sizes."""
        from mcp_servers.base import MCPBulkIngestor, PaginationConfig, EndpointConfig

        mock_session = Mock()
        mock_response = Mock()
        mock_response.json.return_value = {"results": [{"id": 1}]}
        mock_response.raise_for_status = Mock()
        mock_session.get.return_value = mock_response

        ingestor = MCPBulkIngestor(
            base_url="https://api.example.com",
            session=mock_session,
        )

        endpoint = EndpointConfig(
            name="items",
            path="/api/items",
            pagination=PaginationConfig(page_size=100, max_pages=1),
        )

        ingestor.ingest_endpoints(
            [endpoint],
            page_size_overrides={"items": 50},
        )

        call_args = mock_session.get.call_args
        params = call_args.kwargs["params"]
        assert params["limit"] == 50


class TestMCPBulkIngestorErrorHandling:
    """Test error handling scenarios."""

    def test_handles_non_list_results(self):
        """Test handling when results is not a list."""
        from mcp_servers.base import MCPBulkIngestor, PaginationConfig, EndpointConfig

        mock_session = Mock()
        mock_response = Mock()
        mock_response.json.return_value = {"results": {"key": "value"}}  # Dict, not list
        mock_response.raise_for_status = Mock()
        mock_session.get.return_value = mock_response

        ingestor = MCPBulkIngestor(
            base_url="https://api.example.com",
            session=mock_session,
        )

        endpoint = EndpointConfig(
            name="test",
            path="/api/items",
            pagination=PaginationConfig(max_pages=1),
        )

        pages = list(ingestor.fetch_paginated(endpoint))

        # Should return the non-list results but count as 0 for pagination
        assert pages[0]["results"] == {"key": "value"}

    def test_handles_missing_results_key(self):
        """Test handling when results key is completely missing."""
        from mcp_servers.base import MCPBulkIngestor, PaginationConfig, EndpointConfig

        mock_session = Mock()
        mock_response = Mock()
        mock_response.json.return_value = {"status": "ok"}  # No results key
        mock_response.raise_for_status = Mock()
        mock_session.get.return_value = mock_response

        ingestor = MCPBulkIngestor(
            base_url="https://api.example.com",
            session=mock_session,
        )

        endpoint = EndpointConfig(
            name="test",
            path="/api/items",
            pagination=PaginationConfig(
                results_path=("results",),
                max_pages=1,
            ),
            result_key_fallbacks=(),  # No fallbacks
        )

        pages = list(ingestor.fetch_paginated(endpoint))

        # Should return empty list
        assert pages[0]["results"] == []

    def test_handles_json_decode_error(self):
        """Test handling of JSON decode errors."""
        from mcp_servers.base import MCPBulkIngestor, PaginationConfig, EndpointConfig

        mock_session = Mock()
        mock_response = Mock()
        mock_response.json.side_effect = json.JSONDecodeError("Invalid", "", 0)
        mock_response.raise_for_status = Mock()
        mock_session.get.return_value = mock_response

        ingestor = MCPBulkIngestor(
            base_url="https://api.example.com",
            session=mock_session,
        )

        endpoint = EndpointConfig(
            name="test",
            path="/api/items",
            pagination=PaginationConfig(max_pages=1),
        )

        with pytest.raises(json.JSONDecodeError):
            list(ingestor.fetch_paginated(endpoint))

    def test_handles_connection_error(self):
        """Test handling of connection errors."""
        import requests
        from mcp_servers.base import MCPBulkIngestor, PaginationConfig, EndpointConfig

        mock_session = Mock()
        mock_session.get.side_effect = requests.ConnectionError("Connection refused")

        ingestor = MCPBulkIngestor(
            base_url="https://api.example.com",
            session=mock_session,
        )

        endpoint = EndpointConfig(
            name="test",
            path="/api/items",
            pagination=PaginationConfig(max_pages=1),
        )

        with pytest.raises(requests.ConnectionError):
            list(ingestor.fetch_paginated(endpoint))

    def test_handles_timeout_error(self):
        """Test handling of timeout errors."""
        import requests
        from mcp_servers.base import MCPBulkIngestor, PaginationConfig, EndpointConfig

        mock_session = Mock()
        mock_session.get.side_effect = requests.Timeout("Request timed out")

        ingestor = MCPBulkIngestor(
            base_url="https://api.example.com",
            session=mock_session,
        )

        endpoint = EndpointConfig(
            name="test",
            path="/api/items",
            pagination=PaginationConfig(max_pages=1),
        )

        with pytest.raises(requests.Timeout):
            list(ingestor.fetch_paginated(endpoint))
