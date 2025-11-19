"""
Performance Monitoring, Feature Flags, and Telemetry Decorators for OpenLegislation

This module provides decorators to track feature flags, telemetry, and measure the speed
and efficiency of function execution, especially for ingestion functions.
"""

import functools
import time
import logging
import json
from typing import Dict, Any, Optional, Callable
from datetime import datetime
import threading
from contextlib import contextmanager

# Global telemetry storage
_telemetry_data = {}
_telemetry_lock = threading.Lock()

# Feature flags storage
_feature_flags = {}
_feature_flags_lock = threading.Lock()

# Performance metrics storage
_performance_metrics = {}
_performance_metrics_lock = threading.Lock()

logger = logging.getLogger(__name__)


class TelemetryCollector:
    """Collects and manages telemetry data"""

    @staticmethod
    def record_event(event_type: str, data: Dict[str, Any], source: str = "unknown"):
        """Record a telemetry event"""
        with _telemetry_lock:
            if source not in _telemetry_data:
                _telemetry_data[source] = []

            event = {
                "timestamp": datetime.utcnow().isoformat(),
                "event_type": event_type,
                "data": data,
                "source": source
            }

            _telemetry_data[source].append(event)

            # Keep only last 1000 events per source
            if len(_telemetry_data[source]) > 1000:
                _telemetry_data[source] = _telemetry_data[source][-1000:]

    @staticmethod
    def get_telemetry(source: str = None) -> Dict[str, Any]:
        """Get telemetry data"""
        with _telemetry_lock:
            if source:
                return {source: _telemetry_data.get(source, [])}
            return _telemetry_data.copy()

    @staticmethod
    def clear_telemetry(source: str = None):
        """Clear telemetry data"""
        with _telemetry_lock:
            if source:
                _telemetry_data.pop(source, None)
            else:
                _telemetry_data.clear()


class FeatureFlagManager:
    """Manages feature flags"""

    @staticmethod
    def set_flag(flag_name: str, enabled: bool, metadata: Dict[str, Any] = None):
        """Set a feature flag"""
        with _feature_flags_lock:
            _feature_flags[flag_name] = {
                "enabled": enabled,
                "metadata": metadata or {},
                "updated_at": datetime.utcnow().isoformat()
            }

    @staticmethod
    def get_flag(flag_name: str) -> bool:
        """Get a feature flag value"""
        with _feature_flags_lock:
            flag_data = _feature_flags.get(flag_name, {})
            return flag_data.get("enabled", False)

    @staticmethod
    def is_enabled(flag_name: str) -> bool:
        """Check if a feature flag is enabled"""
        return FeatureFlagManager.get_flag(flag_name)

    @staticmethod
    def get_all_flags() -> Dict[str, Any]:
        """Get all feature flags"""
        with _feature_flags_lock:
            return _feature_flags.copy()


class PerformanceMonitor:
    """Monitors function performance"""

    @staticmethod
    def record_metric(function_name: str, execution_time: float, success: bool,
                     metadata: Dict[str, Any] = None):
        """Record a performance metric"""
        with _performance_metrics_lock:
            if function_name not in _performance_metrics:
                _performance_metrics[function_name] = []

            metric = {
                "timestamp": datetime.utcnow().isoformat(),
                "execution_time": execution_time,
                "success": success,
                "metadata": metadata or {}
            }

            _performance_metrics[function_name].append(metric)

            # Keep only last 500 metrics per function
            if len(_performance_metrics[function_name]) > 500:
                _performance_metrics[function_name] = _performance_metrics[function_name][-500:]

    @staticmethod
    def get_metrics(function_name: str = None) -> Dict[str, Any]:
        """Get performance metrics"""
        with _performance_metrics_lock:
            if function_name:
                return {function_name: _performance_metrics.get(function_name, [])}
            return _performance_metrics.copy()

    @staticmethod
    def get_stats(function_name: str) -> Dict[str, Any]:
        """Get performance statistics for a function"""
        with _performance_metrics_lock:
            metrics = _performance_metrics.get(function_name, [])
            if not metrics:
                return {}

            execution_times = [m["execution_time"] for m in metrics]
            success_count = sum(1 for m in metrics if m["success"])

            return {
                "call_count": len(metrics),
                "success_count": success_count,
                "failure_count": len(metrics) - success_count,
                "success_rate": success_count / len(metrics) if metrics else 0,
                "avg_execution_time": sum(execution_times) / len(execution_times),
                "min_execution_time": min(execution_times),
                "max_execution_time": max(execution_times),
                "total_execution_time": sum(execution_times)
            }


def feature_flag(flag_name: str, default_enabled: bool = False):
    """
    Decorator to check if a feature flag is enabled before executing a function

    Args:
        flag_name: Name of the feature flag
        default_enabled: Default value if flag doesn't exist
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            enabled = FeatureFlagManager.get_flag(flag_name)
            if not enabled and not default_enabled:
                TelemetryCollector.record_event(
                    "feature_flag_disabled",
                    {"flag_name": flag_name, "function": func.__name__},
                    source="feature_flags"
                )
                logger.info(f"Feature flag '{flag_name}' disabled, skipping {func.__name__}")
                return None

            TelemetryCollector.record_event(
                "feature_flag_enabled",
                {"flag_name": flag_name, "function": func.__name__},
                source="feature_flags"
            )

            return func(*args, **kwargs)
        return wrapper
    return decorator


def telemetry(event_type: str = None, include_args: bool = False, include_result: bool = False):
    """
    Decorator to record telemetry for function calls

    Args:
        event_type: Type of telemetry event (defaults to function name)
        include_args: Whether to include function arguments in telemetry
        include_result: Whether to include function result in telemetry
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            event_name = event_type or f"call_{func.__name__}"

            # Record function call start
            call_data = {
                "function": func.__name__,
                "start_time": datetime.utcnow().isoformat()
            }

            if include_args:
                # Sanitize args for telemetry (avoid sensitive data)
                call_data["args_count"] = len(args)
                call_data["kwargs_keys"] = list(kwargs.keys())

            TelemetryCollector.record_event(
                f"{event_name}_start",
                call_data,
                source="function_calls"
            )

            try:
                result = func(*args, **kwargs)
                execution_time = time.time() - start_time

                # Record successful completion
                completion_data = {
                    "function": func.__name__,
                    "execution_time": execution_time,
                    "success": True
                }

                if include_result and result is not None:
                    # Sanitize result for telemetry
                    if isinstance(result, (int, float, str, bool)):
                        completion_data["result_type"] = type(result).__name__
                    else:
                        completion_data["result_type"] = type(result).__name__
                        completion_data["has_result"] = True

                TelemetryCollector.record_event(
                    f"{event_name}_complete",
                    completion_data,
                    source="function_calls"
                )

                return result

            except Exception as e:
                execution_time = time.time() - start_time

                # Record error
                error_data = {
                    "function": func.__name__,
                    "execution_time": execution_time,
                    "success": False,
                    "error_type": type(e).__name__,
                    "error_message": str(e)
                }

                TelemetryCollector.record_event(
                    f"{event_name}_error",
                    error_data,
                    source="function_calls"
                )

                raise

        return wrapper
    return decorator


def performance_monitor(track_memory: bool = False, track_cpu: bool = False):
    """
    Decorator to monitor function performance

    Args:
        track_memory: Whether to track memory usage
        track_cpu: Whether to track CPU usage
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()

            # Track additional metrics if requested
            memory_start = None
            cpu_start = None

            if track_memory:
                try:
                    import psutil
                    process = psutil.Process()
                    memory_start = process.memory_info().rss
                except ImportError:
                    logger.warning("psutil not available for memory tracking")

            if track_cpu:
                try:
                    import psutil
                    process = psutil.Process()
                    cpu_start = process.cpu_times().user
                except ImportError:
                    logger.warning("psutil not available for CPU tracking")

            metadata = {
                "args_count": len(args),
                "kwargs_count": len(kwargs)
            }

            try:
                result = func(*args, **kwargs)
                execution_time = time.time() - start_time

                # Add performance metrics
                if memory_start is not None:
                    try:
                        memory_end = process.memory_info().rss
                        metadata["memory_delta"] = memory_end - memory_start
                        metadata["memory_end"] = memory_end
                    except:
                        pass

                if cpu_start is not None:
                    try:
                        cpu_end = process.cpu_times().user
                        metadata["cpu_delta"] = cpu_end - cpu_start
                        metadata["cpu_end"] = cpu_end
                    except:
                        pass

                PerformanceMonitor.record_metric(
                    func.__name__,
                    execution_time,
                    True,
                    metadata
                )

                return result

            except Exception as e:
                execution_time = time.time() - start_time

                PerformanceMonitor.record_metric(
                    func.__name__,
                    execution_time,
                    False,
                    {"error": str(e), **metadata}
                )

                raise

        return wrapper
    return decorator


def ingestion_performance(track_records: bool = True, track_api_calls: bool = False):
    """
    Specialized decorator for ingestion functions

    Args:
        track_records: Whether to track number of records processed
        track_api_calls: Whether to track API calls made
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        @performance_monitor(track_memory=True)
        @telemetry(event_type="ingestion_operation", include_args=True)
        def wrapper(*args, **kwargs):
            # Pre-execution setup
            ingestion_metadata = {
                "ingestion_type": func.__name__,
                "start_time": datetime.utcnow().isoformat()
            }

            # Try to extract useful metadata from args
            if args and hasattr(args[0], '__class__'):
                ingestion_metadata["class_name"] = args[0].__class__.__name__

            # Track API calls if requested
            api_call_count = 0
            if track_api_calls:
                original_requests_get = None
                try:
                    import requests
                    original_requests_get = requests.get

                    def tracked_get(*req_args, **req_kwargs):
                        nonlocal api_call_count
                        api_call_count += 1
                        return original_requests_get(*req_args, **req_kwargs)

                    requests.get = tracked_get
                except ImportError:
                    pass

            try:
                result = func(*args, **kwargs)

                # Post-execution analysis
                ingestion_metadata.update({
                    "end_time": datetime.utcnow().isoformat(),
                    "success": True
                })

                if track_api_calls:
                    ingestion_metadata["api_calls"] = api_call_count

                # Try to extract record counts from result or args
                if track_records:
                    record_count = 0
                    if hasattr(result, '__len__'):
                        record_count = len(result)
                    elif isinstance(result, dict) and 'count' in result:
                        record_count = result['count']
                    elif hasattr(args[0], 'tracker') and hasattr(args[0].tracker, 'get_ingestion_stats'):
                        stats = args[0].tracker.get_ingestion_stats()
                        record_count = stats.get('total_processed', 0)

                    ingestion_metadata["records_processed"] = record_count

                # Record successful ingestion
                TelemetryCollector.record_event(
                    "ingestion_complete",
                    ingestion_metadata,
                    source="ingestion_operations"
                )

                return result

            except Exception as e:
                ingestion_metadata.update({
                    "end_time": datetime.utcnow().isoformat(),
                    "success": False,
                    "error": str(e)
                })

                TelemetryCollector.record_event(
                    "ingestion_failed",
                    ingestion_metadata,
                    source="ingestion_operations"
                )

                raise

            finally:
                # Restore original requests.get if it was patched
                if track_api_calls and original_requests_get:
                    try:
                        requests.get = original_requests_get
                    except:
                        pass

        return wrapper
    return decorator


@contextmanager
def telemetry_context(operation_name: str, **context_data):
    """Context manager for telemetry tracking"""
    start_time = time.time()

    TelemetryCollector.record_event(
        f"{operation_name}_start",
        {"context": context_data},
        source="contexts"
    )

    try:
        yield
        execution_time = time.time() - start_time

        TelemetryCollector.record_event(
            f"{operation_name}_complete",
            {
                "execution_time": execution_time,
                "context": context_data,
                "success": True
            },
            source="contexts"
        )

    except Exception as e:
        execution_time = time.time() - start_time

        TelemetryCollector.record_event(
            f"{operation_name}_error",
            {
                "execution_time": execution_time,
                "context": context_data,
                "success": False,
                "error": str(e)
            },
            source="contexts"
        )

        raise


def export_telemetry_to_file(filename: str = "telemetry_export.json"):
    """Export all telemetry data to a JSON file"""
    data = {
        "telemetry": TelemetryCollector.get_telemetry(),
        "feature_flags": FeatureFlagManager.get_all_flags(),
        "performance_metrics": PerformanceMonitor.get_metrics(),
        "exported_at": datetime.utcnow().isoformat()
    }

    with open(filename, 'w') as f:
        json.dump(data, f, indent=2, default=str)

    logger.info(f"Telemetry data exported to {filename}")


def get_performance_report(function_name: str = None) -> str:
    """Generate a performance report"""
    if function_name:
        stats = PerformanceMonitor.get_stats(function_name)
        if not stats:
            return f"No performance data available for {function_name}"

        return f"""
Performance Report for {function_name}:
- Total calls: {stats['call_count']}
- Success rate: {stats['success_rate']:.2%}
- Average execution time: {stats['avg_execution_time']:.4f}s
- Min execution time: {stats['min_execution_time']:.4f}s
- Max execution time: {stats['max_execution_time']:.4f}s
- Total execution time: {stats['total_execution_time']:.4f}s
"""
    else:
        all_metrics = PerformanceMonitor.get_metrics()
        report_lines = ["Performance Report for all functions:"]

        for func_name, metrics in all_metrics.items():
            if metrics:
                stats = PerformanceMonitor.get_stats(func_name)
                report_lines.append(f"- {func_name}: {stats['call_count']} calls, {stats['success_rate']:.1%} success, {stats['avg_execution_time']:.4f}s avg")

        return "\n".join(report_lines)


# Convenience functions for common use cases
def enable_feature_flag(flag_name: str, metadata: Dict[str, Any] = None):
    """Enable a feature flag"""
    FeatureFlagManager.set_flag(flag_name, True, metadata)

def disable_feature_flag(flag_name: str):
    """Disable a feature flag"""
    FeatureFlagManager.set_flag(flag_name, False)

def is_feature_enabled(flag_name: str) -> bool:
    """Check if a feature is enabled"""
    return FeatureFlagManager.is_enabled(flag_name)
