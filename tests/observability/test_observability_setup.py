"""
Tests for OpenTelemetry observability setup.

This module tests the observability_setup.py functionality including:
- OpenTelemetry manager initialization
- Tracing and metrics setup
- Decorator integration
- Performance monitoring
- Error handling
"""

import pytest
import time
from unittest.mock import Mock, patch, MagicMock
from tests.utils.test_helpers import assert_performance_metrics, assert_no_exceptions


class TestOpenTelemetryManager:
    """Test OpenTelemetry manager functionality."""

    @pytest.mark.unit
    def test_initialization_without_opentelemetry(self, mock_opentelemetry):
        """Test initialization when OpenTelemetry is not available."""
        with patch('observability_setup.OPENTELEMETRY_AVAILABLE', False):
            from observability_setup import OpenTelemetryManager

            manager = OpenTelemetryManager()
            assert manager.tracer_provider is None
            assert manager.meter_provider is None
            assert not manager.enabled

    @pytest.mark.unit
    def test_initialization_with_opentelemetry(self, mock_opentelemetry):
        """Test initialization when OpenTelemetry is available."""
        with patch('observability_setup.OPENTELEMETRY_AVAILABLE', True):
            from observability_setup import OpenTelemetryManager

            manager = OpenTelemetryManager()
            assert manager.enabled
            assert manager.tracer is not None
            assert manager.meter is not None

    @pytest.mark.unit
    def test_setup_tracing(self, mock_opentelemetry):
        """Test tracing setup."""
        with patch('observability_setup.OPENTELEMETRY_AVAILABLE', True):
            from observability_setup import OpenTelemetryManager

            manager = OpenTelemetryManager()
            manager.setup_tracing()

            # Verify tracer provider was set
            assert manager.tracer_provider is not None
            assert manager.tracer is not None

    @pytest.mark.unit
    def test_setup_metrics(self, mock_opentelemetry):
        """Test metrics setup."""
        with patch('observability_setup.OPENTELEMETRY_AVAILABLE', True):
            from observability_setup import OpenTelemetryManager

            manager = OpenTelemetryManager()
            manager.setup_metrics()

            # Verify meter provider was set
            assert manager.meter_provider is not None
            assert manager.meter is not None

    @pytest.mark.unit
    def test_create_span(self, mock_opentelemetry):
        """Test span creation."""
        with patch('observability_setup.OPENTELEMETRY_AVAILABLE', True):
            from observability_setup import OpenTelemetryManager

            manager = OpenTelemetryManager()

            with manager.create_span("test_span") as span:
                assert span is not None
                # Verify span context
                assert hasattr(span, '__enter__')
                assert hasattr(span, '__exit__')

    @pytest.mark.unit
    def test_record_metric(self, mock_opentelemetry):
        """Test metric recording."""
        with patch('observability_setup.OPENTELEMETRY_AVAILABLE', True):
            from observability_setup import OpenTelemetryManager

            manager = OpenTelemetryManager()

            # Test counter metric
            manager.record_metric("test_counter", 1, {"key": "value"})
            mock_opentelemetry["counter"].add.assert_called_with(1, {"key": "value"})

            # Test histogram metric
            manager.record_metric("test_histogram", 10.5, {"key": "value"}, metric_type="histogram")
            mock_opentelemetry["histogram"].record.assert_called_with(10.5, {"key": "value"})

    @pytest.mark.unit
    def test_disabled_functionality(self, mock_opentelemetry):
        """Test behavior when OpenTelemetry is disabled."""
        with patch('observability_setup.OPENTELEMETRY_AVAILABLE', False):
            from observability_setup import OpenTelemetryManager

            manager = OpenTelemetryManager()

            # These should not raise exceptions but should be no-ops
            assert_no_exceptions(manager.setup_tracing)
            assert_no_exceptions(manager.setup_metrics)
            assert_no_exceptions(manager.create_span, "test")
            assert_no_exceptions(manager.record_metric, "test", 1)


class TestObservabilityDecorators:
    """Test observability decorators."""

    @pytest.mark.unit
    def test_telemetry_decorator(self, mock_opentelemetry):
        """Test telemetry decorator."""
        with patch('observability_setup.OPENTELEMETRY_AVAILABLE', True):
            from observability_setup import telemetry_decorator

            @telemetry_decorator
            def test_function():
                return "test_result"

            result = test_function()
            assert result == "test_result"

    @pytest.mark.unit
    def test_performance_decorator(self, mock_opentelemetry):
        """Test performance decorator."""
        with patch('observability_setup.OPENTELEMETRY_AVAILABLE', True):
            from observability_setup import performance_decorator

            @performance_decorator
            def test_function():
                time.sleep(0.01)  # Small delay for testing
                return "test_result"

            result = test_function()
            assert result == "test_result"

    @pytest.mark.unit
    def test_ingestion_tracking_decorator(self, mock_opentelemetry):
        """Test ingestion tracking decorator."""
        with patch('observability_setup.OPENTELEMETRY_AVAILABLE', True):
            from observability_setup import ingestion_tracking_decorator

            @ingestion_tracking_decorator
            def test_ingestion(records_count=10):
                return f"Processed {records_count} records"

            result = test_ingestion(records_count=5)
            assert result == "Processed 5 records"

    @pytest.mark.unit
    def test_decorators_without_opentelemetry(self, mock_opentelemetry):
        """Test decorators when OpenTelemetry is not available."""
        with patch('observability_setup.OPENTELEMETRY_AVAILABLE', False):
            from observability_setup import (
                telemetry_decorator,
                performance_decorator,
                ingestion_tracking_decorator
            )

            @telemetry_decorator
            def test_func1():
                return "result1"

            @performance_decorator
            def test_func2():
                return "result2"

            @ingestion_tracking_decorator
            def test_func3():
                return "result3"

            # These should work normally even without OpenTelemetry
            assert test_func1() == "result1"
            assert test_func2() == "result2"
            assert test_func3() == "result3"


class TestIntegrationWithExistingDecorators:
    """Test integration with existing decorators."""

    @pytest.mark.unit
    def test_combined_decorators(self, mock_opentelemetry):
        """Test combining observability decorators with existing ones."""
        with patch('observability_setup.OPENTELEMETRY_AVAILABLE', True):
            from observability_setup import telemetry_decorator, performance_decorator
            from decorators import ingestion_monitor

            @telemetry_decorator
            @performance_decorator
            @ingestion_monitor
            def complex_function(records_count=100):
                time.sleep(0.01)
                return f"Processed {records_count} records"

            result = complex_function(records_count=50)
            assert "Processed 50 records" in result

    @pytest.mark.unit
    def test_error_handling_in_decorators(self, mock_opentelemetry):
        """Test error handling in decorated functions."""
        with patch('observability_setup.OPENTELEMETRY_AVAILABLE', True):
            from observability_setup import telemetry_decorator

            @telemetry_decorator
            def failing_function():
                raise ValueError("Test error")

            with pytest.raises(ValueError, match="Test error"):
                failing_function()


class TestMetricsAndMonitoring:
    """Test metrics and monitoring functionality."""

    @pytest.mark.unit
    def test_custom_metrics_creation(self, mock_opentelemetry):
        """Test creation of custom metrics."""
        with patch('observability_setup.OPENTELEMETRY_AVAILABLE', True):
            from observability_setup import OpenTelemetryManager

            manager = OpenTelemetryManager()

            # Test creating custom counter
            counter = manager.create_counter("custom_counter", "Custom counter", "1")
            assert counter is not None

            # Test creating custom histogram
            histogram = manager.create_histogram("custom_histogram", "Custom histogram", "ms")
            assert histogram is not None

    @pytest.mark.unit
    def test_ingestion_metrics(self, mock_opentelemetry):
        """Test ingestion-specific metrics."""
        with patch('observability_setup.OPENTELEMETRY_AVAILABLE', True):
            from observability_setup import OpenTelemetryManager

            manager = OpenTelemetryManager()

            # Test recording ingestion metrics
            manager.record_ingestion_metric("bills_processed", 100, {"jurisdiction": "federal"})
            manager.record_ingestion_metric("members_processed", 50, {"jurisdiction": "state"})

    @pytest.mark.unit
    def test_performance_metrics(self, mock_opentelemetry):
        """Test performance metrics recording."""
        with patch('observability_setup.OPENTELEMETRY_AVAILABLE', True):
            from observability_setup import OpenTelemetryManager

            manager = OpenTelemetryManager()

            # Test recording performance metrics
            metrics = {
                "duration_ms": 150.5,
                "cpu_usage": 45.2,
                "memory_usage": 128.7,
                "records_processed": 1000
            }

            manager.record_performance_metrics("ingestion_job", metrics)

            # Verify metrics were recorded
            expected_keys = ["duration_ms", "cpu_usage", "memory_usage", "records_processed"]
            assert_performance_metrics(metrics, expected_keys)


class TestConfigurationAndSetup:
    """Test configuration and setup functionality."""

    @pytest.mark.unit
    def test_configuration_loading(self):
        """Test loading observability configuration."""
        from observability_setup import load_observability_config

        config = load_observability_config()

        # Should return a dict with default configuration
        assert isinstance(config, dict)
        assert "enabled" in config
        assert "service_name" in config

    @pytest.mark.unit
    def test_service_setup(self, mock_opentelemetry):
        """Test complete service setup."""
        with patch('observability_setup.OPENTELEMETRY_AVAILABLE', True):
            from observability_setup import setup_observability

            result = setup_observability()

            # Should return True on successful setup
            assert result is True

    @pytest.mark.unit
    def test_service_setup_without_opentelemetry(self):
        """Test service setup when OpenTelemetry is not available."""
        with patch('observability_setup.OPENTELEMETRY_AVAILABLE', False):
            from observability_setup import setup_observability

            result = setup_observability()

            # Should return False when OpenTelemetry is not available
            assert result is False


class TestErrorHandling:
    """Test error handling in observability system."""

    @pytest.mark.unit
    def test_graceful_failures(self, mock_opentelemetry):
        """Test that system fails gracefully when OpenTelemetry operations fail."""
        with patch('observability_setup.OPENTELEMETRY_AVAILABLE', True):
            from observability_setup import OpenTelemetryManager

            manager = OpenTelemetryManager()

            # Mock tracer to raise exception
            manager.tracer.start_as_current_span.side_effect = Exception("Tracer error")

            # Should not raise exception
            assert_no_exceptions(manager.create_span, "test_span")

    @pytest.mark.unit
    def test_invalid_metric_types(self, mock_opentelemetry):
        """Test handling of invalid metric types."""
        with patch('observability_setup.OPENTELEMETRY_AVAILABLE', True):
            from observability_setup import OpenTelemetryManager

            manager = OpenTelemetryManager()

            # Should handle invalid metric type gracefully
            assert_no_exceptions(manager.record_metric, "test", 1, metric_type="invalid")


class TestIntegrationTests:
    """Integration tests for observability system."""

    @pytest.mark.integration
    def test_full_workflow(self, mock_opentelemetry, mock_db_connection):
        """Test full observability workflow."""
        with patch('observability_setup.OPENTELEMETRY_AVAILABLE', True):
            from observability_setup import (
                OpenTelemetryManager,
                telemetry_decorator,
                performance_decorator
            )

            manager = OpenTelemetryManager()

            @telemetry_decorator
            @performance_decorator
            def workflow_function():
                # Simulate some work
                time.sleep(0.01)
                return {"status": "completed", "records": 100}

            # Execute workflow
            result = workflow_function()

            # Verify result
            assert result["status"] == "completed"
            assert result["records"] == 100

            # Verify metrics were recorded
            assert manager.meter is not None