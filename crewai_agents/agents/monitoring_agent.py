"""
Monitoring and Analytics Agent for OpenLegislation

AI agent specialized in system monitoring, performance analytics, and alerting
for data ingestion and processing pipelines.
"""

from crewai import Agent, Task, Crew
from typing import Dict, List, Any, Optional
import json
import time
from datetime import datetime, timedelta
from pathlib import Path
import threading

# Add project paths
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))  # Project root

from decorators import (
    telemetry, performance_monitor, feature_flag,
    TelemetryCollector, PerformanceMonitor, FeatureFlagManager,
    get_performance_report, export_telemetry_to_file
)


class MonitoringAgent(Agent):
    """AI Agent specialized in system monitoring and analytics"""

    def __init__(self, **kwargs):
        super().__init__(
            role="System Monitoring Specialist",
            goal="Monitor system performance, analyze metrics, and provide insights for optimization of data ingestion processes",
            backstory="""You are an expert system monitor with deep knowledge of performance metrics, telemetry analysis,
            and system optimization. You excel at identifying bottlenecks, predicting issues, and recommending
            improvements for data processing pipelines.""",
            verbose=True,
            allow_delegation=False,
            **kwargs
        )

        # Initialize monitoring state
        self.monitoring_active = False
        self.alerts = []
        self.baseline_metrics = {}
        self.monitoring_thread = None

    @telemetry(event_type="monitoring_system_start")
    def start_monitoring(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Start comprehensive system monitoring"""
        if self.monitoring_active:
            return {"status": "already_running", "message": "Monitoring is already active"}

        self.monitoring_active = True

        # Configure monitoring parameters
        monitoring_config = {
            "check_interval": config.get("check_interval", 60),  # seconds
            "alert_thresholds": {
                "cpu_usage": config.get("cpu_threshold", 80),
                "memory_usage": config.get("memory_threshold", 85),
                "error_rate": config.get("error_threshold", 0.05),
                "response_time": config.get("response_time_threshold", 30)
            },
            "enabled_checks": config.get("enabled_checks", [
                "performance_metrics", "system_resources", "error_rates", "telemetry_analysis"
            ])
        }

        # Start monitoring thread
        self.monitoring_thread = threading.Thread(target=self._monitoring_loop, args=(monitoring_config,))
        self.monitoring_thread.daemon = True
        self.monitoring_thread.start()

        return {
            "status": "started",
            "config": monitoring_config,
            "message": f"Monitoring started with {len(monitoring_config['enabled_checks'])} checks"
        }

    def stop_monitoring(self) -> Dict[str, Any]:
        """Stop system monitoring"""
        self.monitoring_active = False
        if self.monitoring_thread:
            self.monitoring_thread.join(timeout=5)

        return {"status": "stopped", "message": "Monitoring stopped"}

    def _monitoring_loop(self, config: Dict[str, Any]):
        """Main monitoring loop"""
        while self.monitoring_active:
            try:
                # Perform monitoring checks
                if "performance_metrics" in config["enabled_checks"]:
                    self._check_performance_metrics(config["alert_thresholds"])

                if "system_resources" in config["enabled_checks"]:
                    self._check_system_resources(config["alert_thresholds"])

                if "error_rates" in config["enabled_checks"]:
                    self._check_error_rates(config["alert_thresholds"])

                if "telemetry_analysis" in config["enabled_checks"]:
                    self._analyze_telemetry_patterns()

                # Sleep for check interval
                time.sleep(config["check_interval"])

            except Exception as e:
                TelemetryCollector.record_event(
                    "monitoring_error",
                    {"error": str(e), "component": "monitoring_loop"},
                    source="system_monitoring"
                )

    def _check_performance_metrics(self, thresholds: Dict[str, Any]):
        """Check performance metrics against thresholds"""
        all_metrics = PerformanceMonitor.get_metrics()

        for function_name, metrics in all_metrics.items():
            if not metrics:
                continue

            stats = PerformanceMonitor.get_stats(function_name)

            # Check execution time
            if stats["avg_execution_time"] > thresholds["response_time"]:
                self._create_alert({
                    "type": "performance",
                    "severity": "warning",
                    "function": function_name,
                    "message": f"Slow execution: {stats['avg_execution_time']:.2f}s average",
                    "current_value": stats["avg_execution_time"],
                    "threshold": thresholds["response_time"]
                })

            # Check success rate
            if stats["success_rate"] < (1 - thresholds["error_rate"]):
                self._create_alert({
                    "type": "reliability",
                    "severity": "error",
                    "function": function_name,
                    "message": f"Low success rate: {stats['success_rate']:.1%}",
                    "current_value": stats["success_rate"],
                    "threshold": 1 - thresholds["error_rate"]
                })

    def _check_system_resources(self, thresholds: Dict[str, Any]):
        """Check system resource usage"""
        try:
            import psutil
            process = psutil.Process()

            # CPU usage
            cpu_percent = process.cpu_percent(interval=1)
            if cpu_percent > thresholds["cpu_usage"]:
                self._create_alert({
                    "type": "system_resource",
                    "severity": "warning",
                    "resource": "cpu",
                    "message": f"High CPU usage: {cpu_percent:.1f}%",
                    "current_value": cpu_percent,
                    "threshold": thresholds["cpu_usage"]
                })

            # Memory usage
            memory_percent = process.memory_percent()
            if memory_percent > thresholds["memory_usage"]:
                self._create_alert({
                    "type": "system_resource",
                    "severity": "warning",
                    "resource": "memory",
                    "message": f"High memory usage: {memory_percent:.1f}%",
                    "current_value": memory_percent,
                    "threshold": thresholds["memory_usage"]
                })

        except ImportError:
            # psutil not available
            pass

    def _check_error_rates(self, thresholds: Dict[str, Any]):
        """Check error rates across the system"""
        telemetry_data = TelemetryCollector.get_telemetry()

        for source, events in telemetry_data.items():
            if not events:
                continue

            # Count errors in recent events (last hour)
            recent_events = [e for e in events if self._is_recent_event(e, hours=1)]
            error_events = [e for e in recent_events if e["event_type"].endswith("_error")]

            if recent_events:
                error_rate = len(error_events) / len(recent_events)
                if error_rate > thresholds["error_rate"]:
                    self._create_alert({
                        "type": "error_rate",
                        "severity": "error",
                        "source": source,
                        "message": f"High error rate: {error_rate:.1%} in last hour",
                        "current_value": error_rate,
                        "threshold": thresholds["error_rate"]
                    })

    def _analyze_telemetry_patterns(self):
        """Analyze telemetry patterns for anomalies"""
        telemetry_data = TelemetryCollector.get_telemetry()

        for source, events in telemetry_data.items():
            if len(events) < 10:  # Need minimum data for analysis
                continue

            # Analyze event frequency patterns
            recent_events = [e for e in events if self._is_recent_event(e, hours=1)]
            older_events = [e for e in events if not self._is_recent_event(e, hours=1) and self._is_recent_event(e, hours=2)]

            if older_events:
                recent_rate = len(recent_events) / 60  # events per minute
                older_rate = len(older_events) / 60

                # Check for significant changes in event rates
                rate_change = abs(recent_rate - older_rate) / max(older_rate, 0.1)
                if rate_change > 2.0:  # 200% change
                    direction = "increase" if recent_rate > older_rate else "decrease"
                    self._create_alert({
                        "type": "telemetry_anomaly",
                        "severity": "info",
                        "source": source,
                        "message": f"Unusual event rate {direction}: {rate_change:.1f}x change",
                        "current_rate": recent_rate,
                        "baseline_rate": older_rate
                    })

    def _is_recent_event(self, event: Dict[str, Any], hours: int = 1) -> bool:
        """Check if an event is within the specified recent time window"""
        try:
            event_time = datetime.fromisoformat(event["timestamp"])
            return datetime.utcnow() - event_time < timedelta(hours=hours)
        except:
            return False

    def _create_alert(self, alert_data: Dict[str, Any]):
        """Create and store an alert"""
        alert = {
            "id": f"alert_{int(time.time())}_{len(self.alerts)}",
            "timestamp": datetime.utcnow().isoformat(),
            **alert_data
        }

        self.alerts.append(alert)

        # Keep only recent alerts (last 1000)
        if len(self.alerts) > 1000:
            self.alerts = self.alerts[-1000:]

        # Record alert in telemetry
        TelemetryCollector.record_event(
            "alert_created",
            alert,
            source="system_monitoring"
        )

    @performance_monitor(track_memory=True)
    @telemetry(event_type="monitoring_analysis")
    def analyze_system_health(self) -> Dict[str, Any]:
        """Analyze overall system health"""
        health_analysis = {
            "timestamp": datetime.utcnow().isoformat(),
            "overall_status": "unknown",
            "components": {},
            "recommendations": []
        }

        # Analyze performance metrics
        performance_health = self._analyze_performance_health()
        health_analysis["components"]["performance"] = performance_health

        # Analyze system resources
        resource_health = self._analyze_resource_health()
        health_analysis["components"]["resources"] = resource_health

        # Analyze error patterns
        error_health = self._analyze_error_health()
        health_analysis["components"]["errors"] = error_health

        # Determine overall status
        component_statuses = [comp["status"] for comp in health_analysis["components"].values()]
        if "critical" in component_statuses:
            health_analysis["overall_status"] = "critical"
        elif "warning" in component_statuses:
            health_analysis["overall_status"] = "warning"
        elif all(status == "healthy" for status in component_statuses):
            health_analysis["overall_status"] = "healthy"
        else:
            health_analysis["overall_status"] = "degraded"

        # Generate recommendations
        health_analysis["recommendations"] = self._generate_health_recommendations(health_analysis)

        return health_analysis

    def _analyze_performance_health(self) -> Dict[str, Any]:
        """Analyze performance health"""
        all_metrics = PerformanceMonitor.get_metrics()
        total_functions = len(all_metrics)
        healthy_functions = 0
        issues = []

        for func_name, metrics in all_metrics.items():
            if not metrics:
                continue

            stats = PerformanceMonitor.get_stats(func_name)

            # Check for performance issues
            if stats["success_rate"] < 0.95:
                issues.append(f"{func_name}: low success rate ({stats['success_rate']:.1%})")
            elif stats["avg_execution_time"] > 10.0:
                issues.append(f"{func_name}: slow execution ({stats['avg_execution_time']:.2f}s avg)")
            else:
                healthy_functions += 1

        status = "healthy" if not issues else "warning" if len(issues) < total_functions * 0.3 else "critical"

        return {
            "status": status,
            "total_functions": total_functions,
            "healthy_functions": healthy_functions,
            "issues": issues
        }

    def _analyze_resource_health(self) -> Dict[str, Any]:
        """Analyze system resource health"""
        try:
            import psutil
            process = psutil.Process()

            cpu_usage = process.cpu_percent()
            memory_usage = process.memory_percent()

            issues = []
            if cpu_usage > 80:
                issues.append(f"High CPU usage: {cpu_usage:.1f}%")
            if memory_usage > 85:
                issues.append(f"High memory usage: {memory_usage:.1f}%")

            status = "healthy" if not issues else "warning" if len(issues) == 1 else "critical"

            return {
                "status": status,
                "cpu_usage": cpu_usage,
                "memory_usage": memory_usage,
                "issues": issues
            }

        except ImportError:
            return {
                "status": "unknown",
                "message": "psutil not available for resource monitoring"
            }

    def _analyze_error_health(self) -> Dict[str, Any]:
        """Analyze error patterns"""
        telemetry_data = TelemetryCollector.get_telemetry()
        total_events = 0
        error_events = 0

        for source, events in telemetry_data.items():
            total_events += len(events)
            error_events += len([e for e in events if e["event_type"].endswith("_error")])

        error_rate = error_events / total_events if total_events > 0 else 0

        if error_rate > 0.1:
            status = "critical"
        elif error_rate > 0.05:
            status = "warning"
        else:
            status = "healthy"

        return {
            "status": status,
            "total_events": total_events,
            "error_events": error_events,
            "error_rate": error_rate
        }

    def _generate_health_recommendations(self, health_analysis: Dict[str, Any]) -> List[str]:
        """Generate health recommendations based on analysis"""
        recommendations = []

        for component_name, component_data in health_analysis["components"].items():
            if component_data["status"] == "critical":
                if component_name == "performance":
                    recommendations.append("Critical: Optimize slow-performing functions and improve error handling")
                elif component_name == "resources":
                    recommendations.append("Critical: Reduce system resource usage or scale infrastructure")
                elif component_name == "errors":
                    recommendations.append("Critical: Investigate and fix high error rates immediately")

            elif component_data["status"] == "warning":
                if component_name == "performance":
                    recommendations.append("Warning: Monitor and optimize functions with performance issues")
                elif component_name == "resources":
                    recommendations.append("Warning: Monitor system resource usage trends")
                elif component_name == "errors":
                    recommendations.append("Warning: Investigate sources of elevated error rates")

        if not recommendations:
            recommendations.append("System health is good - continue monitoring")

        return recommendations

    def get_active_alerts(self, severity: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get active alerts, optionally filtered by severity"""
        alerts = self.alerts

        if severity:
            alerts = [a for a in alerts if a.get("severity") == severity]

        # Return most recent alerts first
        return sorted(alerts, key=lambda x: x["timestamp"], reverse=True)

    def generate_monitoring_report(self) -> str:
        """Generate comprehensive monitoring report"""
        health_analysis = self.analyze_system_health()
        active_alerts = self.get_active_alerts()
        performance_report = get_performance_report()

        report = f"""
# System Monitoring Report
Generated: {datetime.utcnow().isoformat()}

## Overall System Health: {health_analysis['overall_status'].upper()}

## Component Status
"""

        for component_name, component_data in health_analysis["components"].items():
            report += f"### {component_name.title()}: {component_data['status'].upper()}\n"
            if "issues" in component_data and component_data["issues"]:
                report += f"Issues: {', '.join(component_data['issues'])}\n\n"

        report += f"""
## Active Alerts ({len(active_alerts)})
"""
        for alert in active_alerts[:10]:  # Show last 10 alerts
            report += f"- **{alert['severity'].upper()}** [{alert['type']}]: {alert['message']}\n"

        report += f"""
## Performance Summary
{performance_report}

## Recommendations
{chr(10).join(f"- {rec}" for rec in health_analysis['recommendations'])}
"""

        return report

    def export_monitoring_data(self, filename: str = "monitoring_export.json"):
        """Export all monitoring data"""
        export_data = {
            "exported_at": datetime.utcnow().isoformat(),
            "system_health": self.analyze_system_health(),
            "active_alerts": self.get_active_alerts(),
            "performance_metrics": PerformanceMonitor.get_metrics(),
            "telemetry_data": TelemetryCollector.get_telemetry(),
            "feature_flags": FeatureFlagManager.get_all_flags()
        }

        with open(filename, 'w') as f:
            json.dump(export_data, f, indent=2, default=str)

        return f"Monitoring data exported to {filename}"


class AnalyticsAgent(MonitoringAgent):
    """Specialized agent for advanced analytics and predictive monitoring"""

    def __init__(self, **kwargs):
        super().__init__(
            role="Data Analytics Specialist",
            goal="Analyze system data patterns, predict issues, and provide advanced insights for system optimization",
            backstory="""You are a data analytics expert specializing in system performance analysis, predictive modeling,
            and advanced monitoring techniques. You identify trends, predict potential issues, and provide
            data-driven recommendations for system improvement.""",
            **kwargs
        )

    @performance_monitor(track_memory=True)
    @telemetry(event_type="analytics_prediction")
    def predict_performance_trends(self, hours_ahead: int = 24) -> Dict[str, Any]:
        """Predict future performance trends based on historical data"""
        predictions = {
            "prediction_window": f"{hours_ahead} hours",
            "predictions": [],
            "confidence_levels": [],
            "recommendations": []
        }

        # Analyze historical performance data
        all_metrics = PerformanceMonitor.get_metrics()

        for function_name, metrics in all_metrics.items():
            if len(metrics) < 5:  # Need minimum data points
                continue

            # Simple trend analysis (could be enhanced with ML models)
            recent_metrics = sorted(metrics, key=lambda x: x["timestamp"], reverse=True)[:10]
            execution_times = [m["execution_time"] for m in recent_metrics]

            # Calculate trend
            if len(execution_times) >= 2:
                trend = (execution_times[0] - execution_times[-1]) / len(execution_times)
                trend_direction = "improving" if trend < 0 else "degrading"

                # Predict future performance
                predicted_time = execution_times[0] + (trend * (hours_ahead / 24))

                predictions["predictions"].append({
                    "function": function_name,
                    "current_avg_time": sum(execution_times) / len(execution_times),
                    "predicted_avg_time": max(0, predicted_time),  # Don't predict negative times
                    "trend": trend_direction,
                    "trend_magnitude": abs(trend)
                })

                # Determine confidence based on data consistency
                time_variance = sum((t - sum(execution_times)/len(execution_times))**2 for t in execution_times) / len(execution_times)
                confidence = max(0.1, min(1.0, 1.0 - (time_variance / 100)))  # Simple confidence calculation
                predictions["confidence_levels"].append({
                    "function": function_name,
                    "confidence": confidence,
                    "data_points": len(execution_times)
                })

        # Generate recommendations based on predictions
        for pred in predictions["predictions"]:
            if pred["trend"] == "degrading" and pred["predicted_avg_time"] > 30:
                predictions["recommendations"].append(
                    f"Optimize {pred['function']} - predicted execution time: {pred['predicted_avg_time']:.2f}s"
                )

        return predictions

    def analyze_ingestion_patterns(self) -> Dict[str, Any]:
        """Analyze data ingestion patterns and efficiency"""
        telemetry_data = TelemetryCollector.get_telemetry("ingestion_operations")

        if not telemetry_data or "ingestion_operations" not in telemetry_data:
            return {"error": "No ingestion telemetry data available"}

        events = telemetry_data["ingestion_operations"]

        # Analyze ingestion patterns
        analysis = {
            "total_ingestion_events": len(events),
            "time_period": "all_time",
            "patterns": {},
            "efficiency_metrics": {},
            "bottlenecks": []
        }

        # Group events by ingestion type
        ingestion_types = {}
        for event in events:
            ing_type = event["data"].get("ingestion_type", "unknown")
            if ing_type not in ingestion_types:
                ingestion_types[ing_type] = []
            ingestion_types[ing_type].append(event)

        # Analyze each ingestion type
        for ing_type, type_events in ingestion_types.items():
            successful_events = [e for e in type_events if e["data"].get("success", False)]
            failed_events = [e for e in type_events if not e["data"].get("success", True)]

            analysis["patterns"][ing_type] = {
                "total_runs": len(type_events),
                "successful_runs": len(successful_events),
                "failed_runs": len(failed_events),
                "success_rate": len(successful_events) / len(type_events) if type_events else 0,
                "avg_records_processed": sum(e["data"].get("records_processed", 0) for e in successful_events) / len(successful_events) if successful_events else 0
            }

            # Identify potential bottlenecks
            if analysis["patterns"][ing_type]["success_rate"] < 0.9:
                analysis["bottlenecks"].append({
                    "type": ing_type,
                    "issue": "low_success_rate",
                    "severity": "high",
                    "details": f"Success rate: {analysis['patterns'][ing_type]['success_rate']:.1%}"
                })

        return analysis

    def generate_predictive_alerts(self) -> List[Dict[str, Any]]:
        """Generate alerts based on predictive analysis"""
        alerts = []

        # Get performance predictions
        predictions = self.predict_performance_trends(hours_ahead=6)  # 6 hour prediction

        for pred in predictions["predictions"]:
            if pred["predicted_avg_time"] > 60:  # Will exceed 1 minute
                alerts.append({
                    "type": "predictive_performance",
                    "severity": "warning",
                    "function": pred["function"],
                    "message": f"Predicted slow performance in 6 hours: {pred['predicted_avg_time']:.1f}s",
                    "predicted_value": pred["predicted_avg_time"],
                    "recommendation": "Consider scaling or optimization before predicted degradation"
                })

        # Analyze recent error trends
        telemetry_data = TelemetryCollector.get_telemetry()
        recent_errors = []

        for source, events in telemetry_data.items():
            recent_error_events = [
                e for e in events
                if e["event_type"].endswith("_error") and self._is_recent_event(e, hours=2)
            ]
            recent_errors.extend(recent_error_events)

        if len(recent_errors) > 5:  # High error rate in last 2 hours
            alerts.append({
                "type": "predictive_error_trend",
                "severity": "error",
                "message": f"Elevated error rate detected: {len(recent_errors)} errors in last 2 hours",
                "error_count": len(recent_errors),
                "recommendation": "Investigate error sources and implement fixes"
            })

        return alerts


# Convenience functions
def create_monitoring_agent(model_name: str = "gpt-4") -> MonitoringAgent:
    """Create a monitoring agent"""
    return MonitoringAgent(llm=model_name)

def create_analytics_agent(model_name: str = "gpt-4") -> AnalyticsAgent:
    """Create an analytics agent"""
    return AnalyticsAgent(llm=model_name)
