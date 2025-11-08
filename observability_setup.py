#!/usr/bin/env python3
"""
OpenTelemetry Observability Setup for OpenLegislation

This module sets up comprehensive observability using OpenTelemetry,
integrating with the existing decorators and telemetry system.

Features:
- OpenTelemetry tracing and metrics
- Integration with existing decorators
- Jaeger/Grafana Tempo support
- Prometheus metrics export
- Custom spans for ingestion operations
- Performance monitoring and alerting

Author: OpenLegislation Team
Date: 2025-11-08
"""

import logging
import time
from typing import Dict, Any, Optional, Callable
from functools import wraps
import asyncio

# OpenTelemetry imports
try:
    from opentelemetry import trace, metrics
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor
    from opentelemetry.sdk.metrics import MeterProvider
    from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
    from opentelemetry.exporter.jaeger.thrift import JaegerExporter
    from opentelemetry.exporter.prometheus import PrometheusMetricReader
    from opentelemetry.instrumentation.requests import RequestsInstrumentor
    from opentelemetry.instrumentation.httpx import HTTPXInstrumentor
    from opentelemetry.trace import Status, StatusCode
    from opentelemetry.metrics import Counter, Histogram, UpDownCounter
    OPENTELEMETRY_AVAILABLE = True
except ImportError:
    OPENTELEMETRY_AVAILABLE = False
    logging.warning("OpenTelemetry not available. Install with: pip install opentelemetry-distro opentelemetry-instrumentation")

from database_connection import get_db_config
from decorators import performance_monitor, telemetry

logger = logging.getLogger(__name__)


class OpenTelemetryManager:
    """
    Manages OpenTelemetry setup and integration
    """

    def __init__(self):
        self.tracer = None
        self.meter = None
        self.initialized = False

        # Metrics
        self.request_counter = None
        self.request_duration = None
        self.active_requests = None
        self.error_counter = None
        self.ingestion_counter = None
        self.queue_size = None

    def initialize(self, service_name: str = "openlegislation", service_version: str = "1.0.0"):
        """Initialize OpenTelemetry"""
        if not OPENTELEMETRY_AVAILABLE:
            logger.warning("OpenTelemetry not available, skipping initialization")
            return

        try:
            # Set up tracing
            trace.set_tracer_provider(TracerProvider())
            tracer_provider = trace.get_tracer_provider()

            # Jaeger exporter for traces
            jaeger_exporter = JaegerExporter(
                agent_host_name="localhost",
                agent_port=6831,
            )
            span_processor = BatchSpanProcessor(jaeger_exporter)
            tracer_provider.add_span_processor(span_processor)

            # Prometheus exporter for metrics
            prometheus_reader = PrometheusMetricReader()
            metric_readers = [prometheus_reader]

            # Set up metrics
            metrics.set_meter_provider(MeterProvider(metric_readers=metric_readers))

            # Get tracer and meter
            self.tracer = trace.get_tracer(__name__)
            self.meter = metrics.get_meter(__name__)

            # Initialize metrics
            self._initialize_metrics()

            # Instrument HTTP libraries
            self._instrument_libraries()

            self.initialized = True
            logger.info("OpenTelemetry initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize OpenTelemetry: {e}")

    def _initialize_metrics(self):
        """Initialize custom metrics"""
        if not self.meter:
            return

        # Request metrics
        self.request_counter = self.meter.create_counter(
            name="http_requests_total",
            description="Total number of HTTP requests",
            unit="1"
        )

        self.request_duration = self.meter.create_histogram(
            name="http_request_duration_seconds",
            description="HTTP request duration in seconds",
            unit="s"
        )

        self.active_requests = self.meter.create_up_down_counter(
            name="http_requests_active",
            description="Number of active HTTP requests",
            unit="1"
        )

        # Error metrics
        self.error_counter = self.meter.create_counter(
            name="errors_total",
            description="Total number of errors",
            unit="1"
        )

        # Ingestion metrics
        self.ingestion_counter = self.meter.create_counter(
            name="ingestion_records_total",
            description="Total number of records ingested",
            unit="1"
        )

        # Queue metrics
        self.queue_size = self.meter.create_up_down_counter(
            name="queue_size",
            description="Current queue size",
            unit="1"
        )

    def _instrument_libraries(self):
        """Instrument HTTP libraries"""
        try:
            RequestsInstrumentor().instrument()
            HTTPXInstrumentor().instrument()
            logger.info("HTTP libraries instrumented")
        except Exception as e:
            logger.warning(f"Failed to instrument HTTP libraries: {e}")

    def create_span(self, name: str, attributes: Dict[str, Any] = None) -> Optional[Any]:
        """Create a new span"""
        if not self.tracer:
            return None

        span = self.tracer.start_as_span(name)
        if attributes:
            for key, value in attributes.items():
                span.set_attribute(key, value)
        return span

    def record_request(self, method: str, url: str, status_code: int, duration: float):
        """Record HTTP request metrics"""
        if not self.request_counter or not self.request_duration:
            return

        # Record counter
        self.request_counter.add(1, {
            "method": method,
            "status_code": str(status_code),
            "url": url
        })

        # Record duration
        self.request_duration.record(duration, {
            "method": method,
            "status_code": str(status_code)
        })

    def record_error(self, error_type: str, context: Dict[str, Any] = None):
        """Record error metrics"""
        if not self.error_counter:
            return

        attributes = {"error_type": error_type}
        if context:
            attributes.update(context)

        self.error_counter.add(1, attributes)

    def record_ingestion(self, record_type: str, count: int, source: str = "unknown"):
        """Record ingestion metrics"""
        if not self.ingestion_counter:
            return

        self.ingestion_counter.add(count, {
            "record_type": record_type,
            "source": source
        })

    def update_queue_size(self, size: int):
        """Update queue size metric"""
        if self.queue_size:
            self.queue_size.set(size)


# Global instance
_otel_manager = None


def get_otel_manager() -> OpenTelemetryManager:
    """Get global OpenTelemetry manager instance"""
    global _otel_manager
    if _otel_manager is None:
        _otel_manager = OpenTelemetryManager()
    return _otel_manager


def init_observability():
    """Initialize observability"""
    manager = get_otel_manager()
    manager.initialize()
    return manager


# Enhanced decorators with OpenTelemetry integration
def otel_traced(name: str = None, attributes: Dict[str, Any] = None):
    """Decorator to add OpenTelemetry tracing"""
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            manager = get_otel_manager()
            span_name = name or f"{func.__module__}.{func.__qualname__}"

            span = manager.create_span(span_name, attributes)
            if span:
                try:
                    result = func(*args, **kwargs)
                    span.set_status(Status(StatusCode.OK))
                    return result
                except Exception as e:
                    span.set_status(Status(StatusCode.ERROR, str(e)))
                    span.record_exception(e)
                    raise
                finally:
                    span.end()
            else:
                # Fallback if OpenTelemetry not available
                return func(*args, **kwargs)

        return wrapper
    return decorator


def otel_performance_monitor(func_name: str = None):
    """Enhanced performance monitor with OpenTelemetry"""
    def decorator(func: Callable):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            manager = get_otel_manager()
            start_time = time.time()

            span_name = func_name or f"{func.__module__}.{func.__qualname__}"
            span = manager.create_span(span_name, {"operation": "async_function"})

            try:
                result = await func(*args, **kwargs)

                duration = time.time() - start_time
                if span:
                    span.set_attribute("duration_seconds", duration)
                    span.set_status(Status(StatusCode.OK))

                # Log performance
                logger.info(f"Function {span_name} completed in {duration:.3f}s")

                return result

            except Exception as e:
                duration = time.time() - start_time
                if span:
                    span.set_attribute("duration_seconds", duration)
                    span.set_status(Status(StatusCode.ERROR, str(e)))
                    span.record_exception(e)

                logger.error(f"Function {span_name} failed after {duration:.3f}s: {e}")
                raise
            finally:
                if span:
                    span.end()

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            manager = get_otel_manager()
            start_time = time.time()

            span_name = func_name or f"{func.__module__}.{func.__qualname__}"
            span = manager.create_span(span_name, {"operation": "sync_function"})

            try:
                result = func(*args, **kwargs)

                duration = time.time() - start_time
                if span:
                    span.set_attribute("duration_seconds", duration)
                    span.set_status(Status(StatusCode.OK))

                # Log performance
                logger.info(f"Function {span_name} completed in {duration:.3f}s")

                return result

            except Exception as e:
                duration = time.time() - start_time
                if span:
                    span.set_attribute("duration_seconds", duration)
                    span.set_status(Status(StatusCode.ERROR, str(e)))
                    span.record_exception(e)

                logger.error(f"Function {span_name} failed after {duration:.3f}s: {e}")
                raise
            finally:
                if span:
                    span.end()

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator


def otel_ingestion_tracker(record_type: str, source: str = "unknown"):
    """Decorator to track ingestion operations"""
    def decorator(func: Callable):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            manager = get_otel_manager()

            span = manager.create_span(
                f"ingestion.{record_type}",
                {
                    "operation": "data_ingestion",
                    "record_type": record_type,
                    "source": source
                }
            )

            start_time = time.time()
            records_processed = 0

            try:
                result = await func(*args, **kwargs)

                # Try to extract record count from result
                if isinstance(result, dict) and 'records_processed' in result:
                    records_processed = result['records_processed']
                elif isinstance(result, int):
                    records_processed = result
                elif hasattr(result, '__len__'):
                    records_processed = len(result)

                duration = time.time() - start_time

                if span:
                    span.set_attribute("records_processed", records_processed)
                    span.set_attribute("duration_seconds", duration)
                    span.set_attribute("records_per_second", records_processed / duration if duration > 0 else 0)
                    span.set_status(Status(StatusCode.OK))

                # Record metrics
                manager.record_ingestion(record_type, records_processed, source)

                logger.info(f"Ingestion {record_type} from {source}: {records_processed} records in {duration:.3f}s")

                return result

            except Exception as e:
                duration = time.time() - start_time
                if span:
                    span.set_attribute("duration_seconds", duration)
                    span.set_status(Status(StatusCode.ERROR, str(e)))
                    span.record_exception(e)

                logger.error(f"Ingestion {record_type} failed after {duration:.3f}s: {e}")
                raise
            finally:
                if span:
                    span.end()

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            manager = get_otel_manager()

            span = manager.create_span(
                f"ingestion.{record_type}",
                {
                    "operation": "data_ingestion",
                    "record_type": record_type,
                    "source": source
                }
            )

            start_time = time.time()
            records_processed = 0

            try:
                result = func(*args, **kwargs)

                # Try to extract record count from result
                if isinstance(result, dict) and 'records_processed' in result:
                    records_processed = result['records_processed']
                elif isinstance(result, int):
                    records_processed = result
                elif hasattr(result, '__len__'):
                    records_processed = len(result)

                duration = time.time() - start_time

                if span:
                    span.set_attribute("records_processed", records_processed)
                    span.set_attribute("duration_seconds", duration)
                    span.set_attribute("records_per_second", records_processed / duration if duration > 0 else 0)
                    span.set_status(Status(StatusCode.OK))

                # Record metrics
                manager.record_ingestion(record_type, records_processed, source)

                logger.info(f"Ingestion {record_type} from {source}: {records_processed} records in {duration:.3f}s")

                return result

            except Exception as e:
                duration = time.time() - start_time
                if span:
                    span.set_attribute("duration_seconds", duration)
                    span.set_status(Status(StatusCode.ERROR, str(e)))
                    span.record_exception(e)

                logger.error(f"Ingestion {record_type} failed after {duration:.3f}s: {e}")
                raise
            finally:
                if span:
                    span.end()

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator


# Integration with existing decorators
def enhanced_performance_monitor(func_name: str = None):
    """Enhanced performance monitor combining existing decorators with OpenTelemetry"""
    def decorator(func: Callable):
        # Apply existing decorators
        func = performance_monitor(func_name)(func)
        func = telemetry()(func)

        # Apply OpenTelemetry decorator
        func = otel_performance_monitor(func_name)(func)

        return func
    return decorator


def enhanced_ingestion_tracker(record_type: str, source: str = "unknown"):
    """Enhanced ingestion tracker combining existing decorators with OpenTelemetry"""
    def decorator(func: Callable):
        # Apply existing decorators
        func = performance_monitor(f"ingestion_{record_type}")(func)
        func = telemetry()(func)

        # Apply OpenTelemetry decorator
        func = otel_ingestion_tracker(record_type, source)(func)

        return func
    return decorator


# Test and benchmarking integration
class ObservabilityTester:
    """Test observability setup and run benchmarks"""

    def __init__(self):
        self.manager = get_otel_manager()

    async def test_tracing(self):
        """Test tracing functionality"""
        logger.info("Testing OpenTelemetry tracing...")

        with self.manager.create_span("test_span", {"test": "tracing"}) as span:
            span.set_attribute("test_attribute", "test_value")
            await asyncio.sleep(0.1)  # Simulate work
            span.set_status(Status(StatusCode.OK))

        logger.info("Tracing test completed")

    async def test_metrics(self):
        """Test metrics functionality"""
        logger.info("Testing OpenTelemetry metrics...")

        # Record some test metrics
        self.manager.record_request("GET", "http://test.com", 200, 0.1)
        self.manager.record_error("test_error", {"component": "tester"})
        self.manager.record_ingestion("test_records", 100, "test_source")
        self.manager.update_queue_size(5)

        logger.info("Metrics test completed")

    async def run_ingestion_benchmark(self):
        """Run ingestion benchmarking with observability"""
        logger.info("Running ingestion benchmark with observability...")

        @otel_ingestion_tracker("benchmark_records", "test_benchmark")
        async def benchmark_ingestion():
            # Simulate ingestion work
            records = []
            for i in range(1000):
                records.append({"id": i, "data": f"test_data_{i}"})
                if i % 100 == 0:
                    await asyncio.sleep(0.01)  # Simulate processing time

            return {"records_processed": len(records), "data": records}

        result = await benchmark_ingestion()

        logger.info(f"Benchmark completed: {result['records_processed']} records processed")
        return result

    async def run_comprehensive_test(self):
        """Run comprehensive observability test"""
        logger.info("Running comprehensive observability test...")

        # Test tracing
        await self.test_tracing()

        # Test metrics
        await self.test_metrics()

        # Run benchmark
        benchmark_result = await self.run_ingestion_benchmark()

        # Test error handling
        try:
            raise ValueError("Test error for observability")
        except Exception as e:
            self.manager.record_error("test_exception", {"error_message": str(e)})

        logger.info("Comprehensive test completed")
        return {
            "tracing_tested": True,
            "metrics_tested": True,
            "benchmark_result": benchmark_result,
            "error_handling_tested": True
        }


async def main():
    """Main function for testing observability"""
    print("OpenLegislation Observability Setup")
    print("=" * 40)

    # Initialize observability
    manager = init_observability()

    if not manager.initialized:
        print("❌ OpenTelemetry not available")
        print("Install with: pip install opentelemetry-distro opentelemetry-instrumentation")
        return

    print("✅ OpenTelemetry initialized")

    # Run tests
    tester = ObservabilityTester()

    try:
        print("\n🧪 Running observability tests...")

        # Test tracing
        await tester.test_tracing()
        print("✅ Tracing test passed")

        # Test metrics
        await tester.test_metrics()
        print("✅ Metrics test passed")

        # Run benchmark
        benchmark_result = await tester.run_ingestion_benchmark()
        print(f"✅ Benchmark completed: {benchmark_result['records_processed']} records")

        # Comprehensive test
        test_results = await tester.run_comprehensive_test()
        print("✅ Comprehensive test completed")

        print("\n📊 Observability Status:")
        print(f"  Tracing: ✅ Active")
        print(f"  Metrics: ✅ Active")
        print(f"  Benchmark: ✅ {benchmark_result['records_processed']} records processed")
        print(f"  Error Handling: ✅ Tested")

        print("\n🔗 Access Points:")
        print("  Jaeger UI: http://localhost:16686")
        print("  Prometheus: http://localhost:9090")
        print("  Grafana: http://localhost:3000")

    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    asyncio.run(main())
