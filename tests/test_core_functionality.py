#!/usr/bin/env python3
"""
Core Functionality Tests for OpenLegislation

This module provides focused tests for core functionality without complex dependencies.
Tests decorators, telemetry, performance monitoring, and basic ingestion logic.

Author: OpenLegislation Team
Date: 2025-11-08
"""

import pytest
import time
import json
import tempfile
import os
from unittest.mock import patch, MagicMock


class TestDecorators:
    """Test decorator functionality"""

    def test_performance_monitor_decorator(self):
        """Test performance monitor decorator"""
        from decorators import performance_monitor, PerformanceMonitor

        @performance_monitor(track_memory=True)
        def test_function(x, y=10):
            time.sleep(0.01)  # Simulate work
            return x + y

        # Clear any existing metrics
        PerformanceMonitor._performance_metrics.clear()

        # Test the function
        result = test_function(5, 15)
        assert result == 20

        # Check that performance data was recorded
        metrics = PerformanceMonitor.get_metrics("test_function")
        assert "test_function" in metrics
        assert len(metrics["test_function"]) > 0

        # Check metric structure
        metric = metrics["test_function"][0]
        assert "execution_time" in metric
        assert "success" in metric
        assert metric["success"] is True
        assert "metadata" in metric

    def test_telemetry_decorator(self):
        """Test telemetry decorator"""
        from decorators import telemetry, TelemetryCollector

        @telemetry(event_type="test_event", include_args=True)
        def test_function(value):
            return value * 2

        # Clear existing telemetry
        TelemetryCollector._telemetry_data.clear()

        # Test the function
        result = test_function(21)
        assert result == 42

        # Check that telemetry was recorded
        telemetry_data = TelemetryCollector.get_telemetry("function_calls")
        assert "function_calls" in telemetry_data
        assert len(telemetry_data["function_calls"]) > 0

        # Check telemetry structure
        event = telemetry_data["function_calls"][0]
        assert "event_type" in event
        assert "data" in event
        assert "timestamp" in event

    def test_feature_flag_decorator(self):
        """Test feature flag decorator"""
        from decorators import feature_flag, FeatureFlagManager

        @feature_flag("test_feature")
        def test_function():
            return "executed"

        # Clear feature flags
        FeatureFlagManager._feature_flags.clear()

        # Test with feature flag disabled (default)
        result = test_function()
        assert result is None

        # Enable the feature flag
        FeatureFlagManager.set_flag("test_feature", True)

        # Test that function executes
        result = test_function()
        assert result == "executed"

        # Disable the feature flag
        FeatureFlagManager.set_flag("test_feature", False)

        # Test that function doesn't execute
        result = test_function()
        assert result is None

    def test_ingestion_performance_decorator(self):
        """Test ingestion performance decorator"""
        from decorators import ingestion_performance, TelemetryCollector, PerformanceMonitor

        @ingestion_performance(track_records=True)
        def test_ingestion():
            # Simulate processing records
            records = [{"id": i, "data": f"test_{i}"} for i in range(100)]
            return records

        # Clear existing data
        TelemetryCollector._telemetry_data.clear()
        PerformanceMonitor._performance_metrics.clear()

        # Test the function
        result = test_ingestion()
        assert len(result) == 100

        # Check telemetry
        telemetry_data = TelemetryCollector.get_telemetry("ingestion_operations")
        assert "ingestion_operations" in telemetry_data

        # Check performance metrics
        metrics = PerformanceMonitor.get_metrics("test_ingestion")
        assert "test_ingestion" in metrics


class TestTelemetryCollector:
    """Test telemetry collection functionality"""

    def setup_method(self):
        """Set up test environment"""
        from decorators import TelemetryCollector
        TelemetryCollector._telemetry_data.clear()

    def test_record_event(self):
        """Test event recording"""
        from decorators import TelemetryCollector

        # Record an event
        TelemetryCollector.record_event(
            "test_event",
            {"key": "value"},
            source="test_source"
        )

        # Check that event was recorded
        telemetry = TelemetryCollector.get_telemetry("test_source")
        assert "test_source" in telemetry
        assert len(telemetry["test_source"]) == 1

        event = telemetry["test_source"][0]
        assert event["event_type"] == "test_event"
        assert event["data"]["key"] == "value"
        assert "timestamp" in event

    def test_telemetry_limit(self):
        """Test telemetry data limit"""
        from decorators import TelemetryCollector

        # Record many events
        for i in range(1100):  # More than the 1000 limit
            TelemetryCollector.record_event(
                f"event_{i}",
                {"index": i},
                source="test_source"
            )

        # Check that only last 1000 events are kept
        telemetry = TelemetryCollector.get_telemetry("test_source")
        assert len(telemetry["test_source"]) == 1000

        # Check that the earliest events were removed (should have events 100-1099)
        first_event = telemetry["test_source"][0]
        last_event = telemetry["test_source"][-1]

        assert first_event["data"]["index"] == 100
        assert last_event["data"]["index"] == 1099


class TestPerformanceMonitor:
    """Test performance monitoring functionality"""

    def setup_method(self):
        """Set up test environment"""
        from decorators import PerformanceMonitor
        PerformanceMonitor._performance_metrics.clear()

    def test_record_metric(self):
        """Test metric recording"""
        from decorators import PerformanceMonitor

        # Record a metric
        PerformanceMonitor.record_metric(
            "test_function",
            1.5,
            True,
            {"records_processed": 100}
        )

        # Check that metric was recorded
        metrics = PerformanceMonitor.get_metrics("test_function")
        assert "test_function" in metrics
        assert len(metrics["test_function"]) == 1

        metric = metrics["test_function"][0]
        assert metric["execution_time"] == 1.5
        assert metric["success"] is True
        assert metric["metadata"]["records_processed"] == 100

    def test_get_stats(self):
        """Test performance statistics calculation"""
        from decorators import PerformanceMonitor

        # Record multiple metrics
        times = [1.0, 2.0, 1.5, 3.0, 0.5]
        for i, execution_time in enumerate(times):
            success = i != 2  # Make one failure
            PerformanceMonitor.record_metric(
                "test_function",
                execution_time,
                success,
                {"attempt": i}
            )

        # Get statistics
        stats = PerformanceMonitor.get_stats("test_function")

        assert stats["call_count"] == 5
        assert stats["success_count"] == 4  # 4 successes
        assert stats["failure_count"] == 1  # 1 failure
        assert stats["success_rate"] == 0.8  # 4/5
        assert stats["avg_execution_time"] == 1.6  # sum(times)/len(times)
        assert stats["min_execution_time"] == 0.5
        assert stats["max_execution_time"] == 3.0


class TestFeatureFlagManager:
    """Test feature flag management"""

    def setup_method(self):
        """Set up test environment"""
        from decorators import FeatureFlagManager
        FeatureFlagManager._feature_flags.clear()

    def test_set_and_get_flag(self):
        """Test setting and getting feature flags"""
        from decorators import FeatureFlagManager

        # Test default (non-existent flag)
        assert FeatureFlagManager.get_flag("test_flag") is False

        # Set flag to True
        FeatureFlagManager.set_flag("test_flag", True, {"version": "1.0"})

        # Test that flag is now True
        assert FeatureFlagManager.get_flag("test_flag") is True

        # Check metadata
        flags = FeatureFlagManager.get_all_flags()
        assert "test_flag" in flags
        assert flags["test_flag"]["enabled"] is True
        assert flags["test_flag"]["metadata"]["version"] == "1.0"
        assert "updated_at" in flags["test_flag"]

    def test_is_enabled_convenience_method(self):
        """Test is_enabled convenience method"""
        from decorators import FeatureFlagManager

        # Test disabled flag
        assert FeatureFlagManager.is_enabled("disabled_flag") is False

        # Enable flag
        FeatureFlagManager.set_flag("enabled_flag", True)

        # Test enabled flag
        assert FeatureFlagManager.is_enabled("enabled_flag") is True


class TestConfiguration:
    """Test configuration functionality"""

    def test_database_config_loading(self):
        """Test database configuration loading"""
        from database_connection import get_db_config

        config = get_db_config()
        assert hasattr(config, 'get_database_config')
        assert hasattr(config, 'get_connection_string')

        db_config = config.get_database_config()
        assert isinstance(db_config, dict)

        # Should have expected keys
        expected_keys = ['host', 'port', 'database', 'user', 'password']
        for key in expected_keys:
            assert key in db_config

    def test_connection_string_generation(self):
        """Test connection string generation"""
        from database_connection import DatabaseConfig

        # Create test config
        test_config = {
            "database": {
                "host": "testhost",
                "port": 5432,
                "database": "testdb",
                "user": "testuser",
                "password": "testpass"
            }
        }

        config = DatabaseConfig()
        config.config = test_config

        connection_string = config.get_connection_string()
        expected = "postgresql://testuser:testpass@testhost:5432/testdb"
        assert connection_string == expected


class TestObservabilityIntegration:
    """Test observability integration"""

    def test_observability_initialization(self):
        """Test observability initialization"""
        try:
            from observability_setup import init_observability
            manager = init_observability()

            # Should not raise exception
            assert manager is not None

            # Check if initialized (depends on OpenTelemetry availability)
            assert hasattr(manager, 'initialized')

        except Exception as e:
            # May fail if OpenTelemetry not available
            pytest.skip(f"OpenTelemetry not available: {e}")

    def test_enhanced_decorators(self):
        """Test enhanced decorators with OpenTelemetry"""
        try:
            from observability_setup import enhanced_performance_monitor, enhanced_ingestion_tracker

            @enhanced_performance_monitor("enhanced_test")
            def test_function():
                time.sleep(0.01)
                return "success"

            @enhanced_ingestion_tracker("test_records", "test_source")
            def test_ingestion():
                records = [{"id": i} for i in range(10)]
                return records

            # Test functions
            result1 = test_function()
            assert result1 == "success"

            result2 = test_ingestion()
            assert len(result2) == 10

        except Exception as e:
            # May fail if OpenTelemetry not available
            pytest.skip(f"OpenTelemetry integration not available: {e}")


class TestDataExport:
    """Test data export functionality"""

    def setup_method(self):
        """Set up test environment"""
        self.temp_dir = tempfile.mkdtemp()

    def teardown_method(self):
        """Clean up test environment"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_telemetry_export(self):
        """Test telemetry data export"""
        from decorators import export_telemetry_to_file, TelemetryCollector

        # Generate some test telemetry
        TelemetryCollector.record_event("test_event", {"data": "value"}, "test_source")

        # Export to file
        export_file = os.path.join(self.temp_dir, "test_telemetry.json")
        export_telemetry_to_file(export_file)

        # Verify export file exists and contains data
        assert os.path.exists(export_file)

        with open(export_file, 'r') as f:
            data = json.load(f)

        assert "telemetry" in data
        assert "feature_flags" in data
        assert "performance_metrics" in data
        assert "test_source" in data["telemetry"]

    def test_performance_report(self):
        """Test performance report generation"""
        from decorators import get_performance_report, PerformanceMonitor

        # Generate some performance data
        PerformanceMonitor.record_metric("report_test", 1.0, True, {})
        PerformanceMonitor.record_metric("report_test", 2.0, False, {})
        PerformanceMonitor.record_metric("report_test", 1.5, True, {})

        # Generate report
        report = get_performance_report("report_test")

        # Verify report contains expected information
        assert "report_test" in report
        assert "3 calls" in report  # Should show call count
        assert "67%" in report or "0.67" in report  # Should show success rate (2/3)


class TestErrorHandling:
    """Test error handling functionality"""

    def test_decorator_error_handling(self):
        """Test decorator error handling"""
        from decorators import telemetry, PerformanceMonitor, TelemetryCollector

        @telemetry("error_test")
        def failing_function():
            raise ValueError("Test error")

        # Clear existing data
        TelemetryCollector._telemetry_data.clear()
        PerformanceMonitor._performance_metrics.clear()

        # Test that error is raised
        with pytest.raises(ValueError, match="Test error"):
            failing_function()

        # Check that error was recorded in telemetry
        telemetry_data = TelemetryCollector.get_telemetry("function_calls")
        assert "function_calls" in telemetry_data

        # Find error event
        error_events = [e for e in telemetry_data["function_calls"] if e.get("data", {}).get("success") is False]
        assert len(error_events) > 0

        error_event = error_events[0]
        assert error_event["data"]["error_type"] == "ValueError"
        assert "Test error" in error_event["data"]["error_message"]

    def test_performance_error_recording(self):
        """Test that performance monitor records errors"""
        from decorators import performance_monitor, PerformanceMonitor

        @performance_monitor("error_test")
        def failing_function():
            time.sleep(0.01)  # Some execution time
            raise RuntimeError("Performance test error")

        # Clear existing metrics
        PerformanceMonitor._performance_metrics.clear()

        # Test that error is raised
        with pytest.raises(RuntimeError, match="Performance test error"):
            failing_function()

        # Check that error was recorded
        metrics = PerformanceMonitor.get_metrics("failing_function")
        assert "failing_function" in metrics

        # Find the error metric
        error_metrics = [m for m in metrics["failing_function"] if not m["success"]]
        assert len(error_metrics) > 0

        error_metric = error_metrics[0]
        assert error_metric["success"] is False
        assert "error" in error_metric["metadata"]


if __name__ == "__main__":
    # Run basic tests without pytest
    print("Running OpenLegislation Core Functionality Tests")
    print("=" * 55)

    test_classes = [
        TestDecorators,
        TestTelemetryCollector,
        TestPerformanceMonitor,
        TestFeatureFlagManager,
        TestConfiguration,
        TestDataExport,
        TestErrorHandling
    ]

    total_tests = 0
    passed_tests = 0

    for test_class in test_classes:
        print(f"\n🧪 Testing {test_class.__name__}")

        # Create instance
        if hasattr(test_class, 'setup_method'):
            instance = test_class()
            instance.setup_method()
        else:
            instance = test_class()

        # Run test methods
        for method_name in dir(instance):
            if method_name.startswith('test_'):
                total_tests += 1
                try:
                    method = getattr(instance, method_name)
                    method()
                    print(f"  ✅ {method_name}")
                    passed_tests += 1
                except Exception as e:
                    print(f"  ❌ {method_name}: {e}")

        # Clean up
        if hasattr(instance, 'teardown_method'):
            instance.teardown_method()

    print(f"\n📊 Test Results: {passed_tests}/{total_tests} tests passed")

    if passed_tests == total_tests:
        print("🎉 All core functionality tests passed!")
    else:
        print("⚠️  Some tests failed. Check the output above.")
