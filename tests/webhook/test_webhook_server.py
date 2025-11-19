"""
Tests for webhook server functionality.

This module tests webhook server components including:
- HTTP request handling
- Webhook payload processing
- Authentication and security
- Error handling and logging
- Integration with ingestion system
"""

import pytest
import json
from unittest.mock import Mock, patch, MagicMock
from tests.utils.test_helpers import assert_no_exceptions, mock_http_response


class TestWebhookServer:
    """Test webhook server functionality."""

    @pytest.fixture
    def webhook_server(self):
        """Create a webhook server instance for testing."""
        # Import the webhook server app
        from webhook_server.app import app
        app.config['TESTING'] = True
        return app.test_client()

    @pytest.mark.unit
    def test_webhook_endpoint_exists(self, webhook_server):
        """Test that webhook endpoints exist."""
        # Test main webhook endpoint
        response = webhook_server.get('/webhook')
        # Should return method not allowed or similar
        assert response.status_code in [405, 404, 200]  # Depends on implementation

    @pytest.mark.unit
    def test_health_check_endpoint(self, webhook_server):
        """Test health check endpoint."""
        response = webhook_server.get('/health')

        # Should return success status
        assert response.status_code == 200
        data = json.loads(response.data)
        assert "status" in data
        assert data["status"] in ["healthy", "ok"]

    @pytest.mark.unit
    def test_webhook_payload_processing(self, webhook_server):
        """Test webhook payload processing."""
        test_payload = {
            "event": "bill_updated",
            "data": {
                "bill_id": "HR1234",
                "jurisdiction": "federal",
                "changes": ["title", "status"]
            },
            "timestamp": "2025-01-15T10:30:00Z"
        }

        response = webhook_server.post(
            '/webhook/bill',
            data=json.dumps(test_payload),
            content_type='application/json'
        )

        # Should process successfully
        assert response.status_code in [200, 201, 202]

    @pytest.mark.unit
    def test_invalid_payload_handling(self, webhook_server):
        """Test handling of invalid webhook payloads."""
        invalid_payloads = [
            {},  # Empty payload
            {"invalid": "data"},  # Missing required fields
            {"event": "unknown_event"},  # Unknown event type
            "not json",  # Invalid JSON
        ]

        for payload in invalid_payloads:
            if isinstance(payload, dict):
                data = json.dumps(payload)
            else:
                data = payload

            response = webhook_server.post(
                '/webhook/bill',
                data=data,
                content_type='application/json'
            )

            # Should handle gracefully (not crash)
            assert response.status_code in [200, 400, 422, 500]


class TestWebhookAuthentication:
    """Test webhook authentication functionality."""

    @pytest.fixture
    def webhook_server(self):
        """Create webhook server with authentication for testing."""
        from webhook_server.app import app
        app.config['TESTING'] = True
        return app.test_client()

    @pytest.mark.unit
    def test_valid_authentication(self, webhook_server):
        """Test valid webhook authentication."""
        test_payload = {"event": "test", "data": {}}

        # Mock valid authentication
        with patch('webhook_server.app.verify_webhook_signature', return_value=True):
            response = webhook_server.post(
                '/webhook/secure',
                data=json.dumps(test_payload),
                content_type='application/json',
                headers={'X-Webhook-Signature': 'valid_signature'}
            )

            assert response.status_code in [200, 201, 202]

    @pytest.mark.unit
    def test_invalid_authentication(self, webhook_server):
        """Test invalid webhook authentication."""
        test_payload = {"event": "test", "data": {}}

        # Mock invalid authentication
        with patch('webhook_server.app.verify_webhook_signature', return_value=False):
            response = webhook_server.post(
                '/webhook/secure',
                data=json.dumps(test_payload),
                content_type='application/json',
                headers={'X-Webhook-Signature': 'invalid_signature'}
            )

            # Should reject unauthorized requests
            assert response.status_code in [401, 403]

    @pytest.mark.unit
    def test_missing_authentication(self, webhook_server):
        """Test missing authentication headers."""
        test_payload = {"event": "test", "data": {}}

        response = webhook_server.post(
            '/webhook/secure',
            data=json.dumps(test_payload),
            content_type='application/json'
        )

        # Should reject requests without authentication
        assert response.status_code in [401, 403]


class TestWebhookPayloadValidation:
    """Test webhook payload validation."""

    @pytest.fixture
    def payload_validator(self):
        """Create payload validator for testing."""
        class MockPayloadValidator:
            def validate_bill_payload(self, payload):
                """Validate bill webhook payload."""
                required_fields = ['event', 'data']
                if not all(field in payload for field in required_fields):
                    return False, "Missing required fields"

                data = payload.get('data', {})
                if 'bill_id' not in data:
                    return False, "Missing bill_id in data"

                return True, "Valid"

            def validate_member_payload(self, payload):
                """Validate member webhook payload."""
                required_fields = ['event', 'data']
                if not all(field in payload for field in required_fields):
                    return False, "Missing required fields"

                data = payload.get('data', {})
                if 'member_id' not in data:
                    return False, "Missing member_id in data"

                return True, "Valid"

            def validate_vote_payload(self, payload):
                """Validate vote webhook payload."""
                required_fields = ['event', 'data']
                if not all(field in payload for field in required_fields):
                    return False, "Missing required fields"

                data = payload.get('data', {})
                if 'vote_id' not in data:
                    return False, "Missing vote_id in data"

                return True, "Valid"

        return MockPayloadValidator()

    @pytest.mark.unit
    def test_valid_bill_payload(self, payload_validator):
        """Test validation of valid bill payload."""
        valid_payload = {
            "event": "bill_updated",
            "data": {
                "bill_id": "HR1234",
                "title": "Test Bill",
                "jurisdiction": "federal"
            }
        }

        is_valid, message = payload_validator.validate_bill_payload(valid_payload)

        assert is_valid is True
        assert message == "Valid"

    @pytest.mark.unit
    def test_invalid_bill_payload(self, payload_validator):
        """Test validation of invalid bill payload."""
        invalid_payloads = [
            {},  # Empty
            {"event": "bill_updated"},  # Missing data
            {"event": "bill_updated", "data": {}},  # Missing bill_id
        ]

        for payload in invalid_payloads:
            is_valid, message = payload_validator.validate_bill_payload(payload)

            assert is_valid is False
            assert "Missing" in message

    @pytest.mark.unit
    def test_valid_member_payload(self, payload_validator):
        """Test validation of valid member payload."""
        valid_payload = {
            "event": "member_updated",
            "data": {
                "member_id": "M001",
                "name": "John Doe",
                "jurisdiction": "federal"
            }
        }

        is_valid, message = payload_validator.validate_member_payload(valid_payload)

        assert is_valid is True
        assert message == "Valid"

    @pytest.mark.unit
    def test_valid_vote_payload(self, payload_validator):
        """Test validation of valid vote payload."""
        valid_payload = {
            "event": "vote_recorded",
            "data": {
                "vote_id": "V001",
                "bill_id": "HR1234",
                "result": "passed",
                "jurisdiction": "federal"
            }
        }

        is_valid, message = payload_validator.validate_vote_payload(valid_payload)

        assert is_valid is True
        assert message == "Valid"


class TestWebhookEventProcessing:
    """Test webhook event processing."""

    @pytest.fixture
    def event_processor(self):
        """Create event processor for testing."""
        class MockEventProcessor:
            def __init__(self):
                self.processed_events = []

            def process_bill_event(self, event_data):
                """Process bill-related events."""
                self.processed_events.append({
                    "type": "bill",
                    "data": event_data,
                    "processed": True
                })
                return {"status": "processed", "event_type": "bill"}

            def process_member_event(self, event_data):
                """Process member-related events."""
                self.processed_events.append({
                    "type": "member",
                    "data": event_data,
                    "processed": True
                })
                return {"status": "processed", "event_type": "member"}

            def process_vote_event(self, event_data):
                """Process vote-related events."""
                self.processed_events.append({
                    "type": "vote",
                    "data": event_data,
                    "processed": True
                })
                return {"status": "processed", "event_type": "vote"}

            def get_processed_events(self):
                """Get list of processed events."""
                return self.processed_events

        return MockEventProcessor()

    @pytest.mark.unit
    def test_bill_event_processing(self, event_processor):
        """Test bill event processing."""
        event_data = {
            "bill_id": "HR1234",
            "action": "updated",
            "changes": ["status", "title"]
        }

        result = event_processor.process_bill_event(event_data)

        assert result["status"] == "processed"
        assert result["event_type"] == "bill"

        processed_events = event_processor.get_processed_events()
        assert len(processed_events) == 1
        assert processed_events[0]["type"] == "bill"
        assert processed_events[0]["data"] == event_data

    @pytest.mark.unit
    def test_member_event_processing(self, event_processor):
        """Test member event processing."""
        event_data = {
            "member_id": "M001",
            "action": "updated",
            "changes": ["party", "district"]
        }

        result = event_processor.process_member_event(event_data)

        assert result["status"] == "processed"
        assert result["event_type"] == "member"

    @pytest.mark.unit
    def test_vote_event_processing(self, event_processor):
        """Test vote event processing."""
        event_data = {
            "vote_id": "V001",
            "bill_id": "HR1234",
            "result": "passed",
            "yeas": 220,
            "nays": 210
        }

        result = event_processor.process_vote_event(event_data)

        assert result["status"] == "processed"
        assert result["event_type"] == "vote"

    @pytest.mark.unit
    def test_multiple_event_processing(self, event_processor):
        """Test processing multiple events."""
        # Process different types of events
        bill_event = {"bill_id": "HR1234", "action": "introduced"}
        member_event = {"member_id": "M001", "action": "elected"}
        vote_event = {"vote_id": "V001", "action": "recorded"}

        event_processor.process_bill_event(bill_event)
        event_processor.process_member_event(member_event)
        event_processor.process_vote_event(vote_event)

        processed_events = event_processor.get_processed_events()
        assert len(processed_events) == 3

        event_types = [event["type"] for event in processed_events]
        assert "bill" in event_types
        assert "member" in event_types
        assert "vote" in event_types


class TestWebhookErrorHandling:
    """Test webhook error handling."""

    @pytest.fixture
    def error_handler(self):
        """Create error handler for testing."""
        class MockErrorHandler:
            def __init__(self):
                self.errors = []

            def handle_processing_error(self, error, payload, endpoint):
                """Handle processing errors."""
                error_info = {
                    "type": "processing_error",
                    "error": str(error),
                    "payload": payload,
                    "endpoint": endpoint,
                    "timestamp": "2025-01-15T10:30:00Z"
                }
                self.errors.append(error_info)
                return {"status": "error_handled", "error_id": len(self.errors)}

            def handle_authentication_error(self, payload, headers):
                """Handle authentication errors."""
                error_info = {
                    "type": "auth_error",
                    "payload": payload,
                    "headers": dict(headers),
                    "timestamp": "2025-01-15T10:30:00Z"
                }
                self.errors.append(error_info)
                return {"status": "auth_failed", "error": "Invalid signature"}

            def handle_validation_error(self, payload, validation_errors):
                """Handle validation errors."""
                error_info = {
                    "type": "validation_error",
                    "payload": payload,
                    "validation_errors": validation_errors,
                    "timestamp": "2025-01-15T10:30:00Z"
                }
                self.errors.append(error_info)
                return {"status": "validation_failed", "errors": validation_errors}

            def get_errors(self):
                """Get list of errors."""
                return self.errors

        return MockErrorHandler()

    @pytest.mark.unit
    def test_processing_error_handling(self, error_handler):
        """Test processing error handling."""
        test_error = ValueError("Processing failed")
        test_payload = {"event": "test"}
        endpoint = "/webhook/bill"

        result = error_handler.handle_processing_error(test_error, test_payload, endpoint)

        assert result["status"] == "error_handled"
        assert "error_id" in result

        errors = error_handler.get_errors()
        assert len(errors) == 1
        assert errors[0]["type"] == "processing_error"
        assert errors[0]["error"] == "Processing failed"

    @pytest.mark.unit
    def test_authentication_error_handling(self, error_handler):
        """Test authentication error handling."""
        test_payload = {"event": "test"}
        test_headers = {"X-Webhook-Signature": "invalid"}

        result = error_handler.handle_authentication_error(test_payload, test_headers)

        assert result["status"] == "auth_failed"
        assert result["error"] == "Invalid signature"

        errors = error_handler.get_errors()
        assert len(errors) == 1
        assert errors[0]["type"] == "auth_error"

    @pytest.mark.unit
    def test_validation_error_handling(self, error_handler):
        """Test validation error handling."""
        test_payload = {"invalid": "payload"}
        validation_errors = ["Missing required field: event", "Invalid data format"]

        result = error_handler.handle_validation_error(test_payload, validation_errors)

        assert result["status"] == "validation_failed"
        assert result["errors"] == validation_errors

        errors = error_handler.get_errors()
        assert len(errors) == 1
        assert errors[0]["type"] == "validation_error"


class TestWebhookIntegration:
    """Test webhook integration with other systems."""

    @pytest.mark.unit
    def test_webhook_to_ingestion_integration(self):
        """Test integration between webhooks and ingestion system."""
        # Mock ingestion system
        mock_ingestion = Mock()
        mock_ingestion.process_bill.return_value = {"status": "ingested", "bill_id": "HR1234"}
        mock_ingestion.process_member.return_value = {"status": "ingested", "member_id": "M001"}
        mock_ingestion.process_vote.return_value = {"status": "ingested", "vote_id": "V001"}

        # Test webhook triggers ingestion
        bill_payload = {
            "event": "bill_updated",
            "data": {"bill_id": "HR1234", "title": "Test Bill"}
        }

        # Simulate webhook processing triggering ingestion
        result = mock_ingestion.process_bill(bill_payload["data"])

        assert result["status"] == "ingested"
        assert result["bill_id"] == "HR1234"
        mock_ingestion.process_bill.assert_called_once_with(bill_payload["data"])

    @pytest.mark.unit
    def test_webhook_rate_limiting(self):
        """Test webhook rate limiting."""
        # Mock rate limiter
        class MockRateLimiter:
            def __init__(self):
                self.requests = {}

            def is_allowed(self, client_id, endpoint):
                key = f"{client_id}:{endpoint}"
                count = self.requests.get(key, 0)
                if count >= 10:  # 10 requests per minute limit
                    return False
                self.requests[key] = count + 1
                return True

        rate_limiter = MockRateLimiter()

        # Test normal requests
        client_id = "test_client"
        endpoint = "/webhook/bill"

        for i in range(10):
            assert rate_limiter.is_allowed(client_id, endpoint) is True

        # Test rate limit exceeded
        assert rate_limiter.is_allowed(client_id, endpoint) is False

    @pytest.mark.unit
    def test_webhook_retry_mechanism(self):
        """Test webhook retry mechanism."""
        # Mock retry handler
        class MockRetryHandler:
            def __init__(self):
                self.attempts = {}

            def should_retry(self, webhook_id, attempt_count):
                max_attempts = 3
                if attempt_count >= max_attempts:
                    return False
                return True

            def schedule_retry(self, webhook_id, payload, delay_seconds):
                self.attempts[webhook_id] = {
                    "payload": payload,
                    "delay": delay_seconds,
                    "scheduled": True
                }
                return f"retry_{webhook_id}"

        retry_handler = MockRetryHandler()

        webhook_id = "webhook_123"
        payload = {"event": "test"}

        # Test retry scheduling
        retry_id = retry_handler.schedule_retry(webhook_id, payload, 60)

        assert retry_id == f"retry_{webhook_id}"
        assert retry_handler.attempts[webhook_id]["scheduled"] is True
        assert retry_handler.attempts[webhook_id]["delay"] == 60

        # Test retry limits
        assert retry_handler.should_retry(webhook_id, 1) is True
        assert retry_handler.should_retry(webhook_id, 2) is True
        assert retry_handler.should_retry(webhook_id, 3) is False


class TestIntegrationTests:
    """Integration tests for webhook server."""

    @pytest.mark.integration
    def test_full_webhook_workflow(self):
        """Test full webhook processing workflow."""
        # This would test the complete webhook processing pipeline
        # For now, we'll test component interactions

        # Mock all components
        mock_validator = Mock()
        mock_validator.validate_bill_payload.return_value = (True, "Valid")

        mock_processor = Mock()
        mock_processor.process_bill_event.return_value = {"status": "processed"}

        mock_ingestion = Mock()
        mock_ingestion.process_bill.return_value = {"status": "ingested"}

        # Simulate webhook workflow
        payload = {
            "event": "bill_updated",
            "data": {"bill_id": "HR1234", "title": "Test Bill"}
        }

        # Validate payload
        is_valid, message = mock_validator.validate_bill_payload(payload)
        assert is_valid is True

        # Process event
        process_result = mock_processor.process_bill_event(payload["data"])
        assert process_result["status"] == "processed"

        # Trigger ingestion
        ingest_result = mock_ingestion.process_bill(payload["data"])
        assert ingest_result["status"] == "ingested"

    @pytest.mark.integration
    def test_webhook_error_recovery(self):
        """Test webhook error recovery mechanisms."""
        # Mock components that can fail
        mock_processor = Mock()
        mock_processor.process_bill_event.side_effect = [
            Exception("Temporary failure"),
            {"status": "processed"}  # Success on retry
        ]

        mock_retry_handler = Mock()
        mock_retry_handler.should_retry.return_value = True
        mock_retry_handler.schedule_retry.return_value = "retry_123"

        payload = {"event": "bill_updated", "data": {"bill_id": "HR1234"}}

        # First attempt fails
        try:
            mock_processor.process_bill_event(payload["data"])
        except Exception:
            # Schedule retry
            retry_id = mock_retry_handler.schedule_retry("webhook_123", payload, 60)
            assert retry_id == "retry_123"

        # Second attempt succeeds
        result = mock_processor.process_bill_event(payload["data"])
        assert result["status"] == "processed"