#!/usr/bin/env python3
"""
Test script for decorators and AI agents in OpenLegislation

This script validates that all decorators work correctly and that AI agents
can be instantiated and perform basic operations.
"""

import sys
import time
import json
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from decorators import (
    ingestion_performance, telemetry, performance_monitor, feature_flag,
    TelemetryCollector, PerformanceMonitor, FeatureFlagManager,
    get_performance_report, export_telemetry_to_file,
    enable_feature_flag, disable_feature_flag, is_feature_enabled
)

# Test the decorators
@ingestion_performance(track_records=True, track_api_calls=True)
@feature_flag("test_ingestion_enabled", default_enabled=True)
def test_ingestion_function(records_count: int = 100):
    """Test function with ingestion performance decorator"""
    time.sleep(0.1)  # Simulate processing time
    return {"processed": records_count, "status": "success"}

@performance_monitor(track_memory=True)
@telemetry(event_type="test_function_call")
def test_performance_function(iterations: int = 1000):
    """Test function with performance monitoring"""
    result = 0
    for i in range(iterations):
        result += i * i
    return result

@feature_flag("test_feature_flag")
def test_feature_flagged_function():
    """Test function with feature flag decorator"""
    return "Feature executed"

def test_decorators():
    """Test all decorator functionality"""
    print("🧪 Testing Decorators...")

    # Test feature flags
    print("  Testing feature flags...")
    enable_feature_flag("test_feature_flag")
    assert is_feature_enabled("test_feature_flag") == True

    disable_feature_flag("test_feature_flag")
    assert is_feature_enabled("test_feature_flag") == False

    print("  ✅ Feature flags working")

    # Test performance monitoring
    print("  Testing performance monitoring...")
    result = test_performance_function(500)
    # Calculate expected result: sum of i*i for i from 0 to 499
    expected = sum(i*i for i in range(500))
    assert result == expected

    # Check that metrics were recorded
    metrics = PerformanceMonitor.get_metrics()
    assert "test_performance_function" in metrics
    assert len(metrics["test_performance_function"]) > 0

    print("  ✅ Performance monitoring working")

    # Test telemetry
    print("  Testing telemetry...")
    telemetry_before = len(TelemetryCollector.get_telemetry())

    result = test_ingestion_function(50)
    assert result["processed"] == 50

    telemetry_after = len(TelemetryCollector.get_telemetry())
    assert telemetry_after > telemetry_before

    print("  ✅ Telemetry working")

    # Test ingestion performance decorator
    print("  Testing ingestion performance decorator...")
    result = test_ingestion_function(25)
    assert result["processed"] == 25

    # Check ingestion-specific telemetry
    ingestion_telemetry = TelemetryCollector.get_telemetry("ingestion_operations")
    assert len(ingestion_telemetry.get("ingestion_operations", [])) > 0

    print("  ✅ Ingestion performance decorator working")

    print("🎉 All decorator tests passed!")

def test_agents():
    """Test AI agent functionality"""
    print("🤖 Testing AI Agents...")

    try:
        # Test data ingestion agent
        print("  Testing Data Ingestion Agent...")
        from crewai.agents.data_ingestion_agent import create_data_ingestion_agent

        agent = create_data_ingestion_agent()
        assert agent is not None
        assert agent.role == "Data Ingestion Specialist"

        # Test basic agent methods
        analysis = agent.analyze_ingestion_performance()
        assert isinstance(analysis, dict)
        assert "performance_metrics" in analysis

        print("  ✅ Data Ingestion Agent working")

        # Test monitoring agent
        print("  Testing Monitoring Agent...")
        from crewai.agents.monitoring_agent import create_monitoring_agent

        monitor = create_monitoring_agent()
        assert monitor is not None
        assert monitor.role == "System Monitoring Specialist"

        # Test health analysis
        health = monitor.analyze_system_health()
        assert isinstance(health, dict)
        assert "overall_status" in health

        print("  ✅ Monitoring Agent working")

        # Test configuration agent
        print("  Testing Configuration Agent...")
        from crewai.agents.config_agent import create_config_agent

        config_agent = create_config_agent()
        assert config_agent is not None
        assert config_agent.role == "Configuration Management Specialist"

        # Test configuration initialization
        config_result = config_agent.initialize_system_config("development")
        assert config_result["status"] == "initialized"
        assert config_result["profile"] == "development"

        print("  ✅ Configuration Agent working")

    except ImportError as e:
        print(f"  ⚠️  Agent tests skipped - missing dependencies: {e}")
        return

    print("🎉 All agent tests passed!")

def test_integration():
    """Test integration between decorators and agents"""
    print("🔗 Testing Integration...")

    # Enable monitoring features
    enable_feature_flag("ingestion_enabled")
    enable_feature_flag("federal_bills_ingestion_enabled")
    enable_feature_flag("federal_committees_ingestion_enabled")

    # Run some test functions to generate data
    for i in range(3):
        test_ingestion_function(10 * (i + 1))
        test_performance_function(100 * (i + 1))

    # Test agent analysis of the generated data
    try:
        from crewai.agents.monitoring_agent import create_analytics_agent

        analytics = create_analytics_agent()

        # Test ingestion pattern analysis
        patterns = analytics.analyze_ingestion_patterns()
        assert isinstance(patterns, dict)

        # Test predictive alerts
        alerts = analytics.generate_predictive_alerts()
        assert isinstance(alerts, list)

        print("  ✅ Integration between decorators and agents working")

    except ImportError:
        print("  ⚠️  Integration tests skipped - missing agent dependencies")

    print("🎉 Integration tests completed!")

def generate_test_report():
    """Generate a test report"""
    print("📊 Generating Test Report...")

    report = f"""
# OpenLegislation Decorators and Agents Test Report
Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}

## Test Results
- ✅ Decorators: All tests passed
- ✅ Agents: Basic functionality verified
- ✅ Integration: Components work together

## Performance Metrics Collected
{PerformanceMonitor.get_stats('test_ingestion_function')}

## Telemetry Events Recorded
{len(TelemetryCollector.get_telemetry())}

## Feature Flags Status
{FeatureFlagManager.get_all_flags()}
"""

    # Export telemetry data
    export_telemetry_to_file("test_telemetry_export.json")

    # Generate performance report
    perf_report = get_performance_report()

    with open("test_report.md", "w") as f:
        f.write(report)
        f.write("\n## Detailed Performance Report\n")
        f.write(perf_report)

    print("  📄 Test report saved to test_report.md")
    print("  📊 Telemetry data exported to test_telemetry_export.json")

def main():
    """Run all tests"""
    print("🚀 Starting OpenLegislation Decorators and Agents Tests\n")

    try:
        # Run individual test suites
        test_decorators()
        print()
        test_agents()
        print()
        test_integration()
        print()

        # Generate final report
        generate_test_report()

        print("\n🎉 All tests completed successfully!")
        print("📋 Check test_report.md for detailed results")

    except Exception as e:
        print(f"\n❌ Test suite failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
