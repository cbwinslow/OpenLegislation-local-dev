"""
Data Ingestion Agent for OpenLegislation

Specialized AI agent for managing and optimizing data ingestion processes.
Handles federal data ingestion, performance monitoring, and error recovery.
"""

from crewai import Agent, Task, Crew
from typing import Dict, List, Any, Optional
import json
import os
from datetime import datetime
from pathlib import Path

# Add project paths
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))  # Project root
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "tools"))  # Tools directory

from decorators import (
    ingestion_performance, telemetry, performance_monitor,
    feature_flag, TelemetryCollector, PerformanceMonitor,
    get_performance_report, export_telemetry_to_file
)


class DataIngestionAgent(Agent):
    """AI Agent specialized in data ingestion management and optimization"""

    def __init__(self, **kwargs):
        super().__init__(
            role="Data Ingestion Specialist",
            goal="Manage and optimize data ingestion processes for legislative data, ensuring high performance, reliability, and monitoring",
            backstory="""You are an expert data ingestion engineer with deep knowledge of legislative data systems,
            API integrations, and performance optimization. You excel at managing complex data pipelines,
            troubleshooting ingestion issues, and implementing monitoring solutions.""",
            verbose=True,
            allow_delegation=True,
            **kwargs
        )

    @ingestion_performance(track_records=True, track_api_calls=True)
    @telemetry(event_type="agent_ingestion_analysis")
    def analyze_ingestion_performance(self, ingestion_type: str = "all") -> Dict[str, Any]:
        """Analyze performance of ingestion processes"""
        try:
            # Get performance metrics
            if ingestion_type == "all":
                metrics = PerformanceMonitor.get_metrics()
            else:
                metrics = PerformanceMonitor.get_metrics(ingestion_type)

            # Get telemetry data
            telemetry_data = TelemetryCollector.get_telemetry("ingestion_operations")

            # Generate analysis
            analysis = {
                "timestamp": datetime.utcnow().isoformat(),
                "ingestion_type": ingestion_type,
                "performance_metrics": metrics,
                "telemetry_events": len(telemetry_data.get(ingestion_type, [])),
                "recommendations": []
            }

            # Analyze performance and generate recommendations
            for func_name, func_metrics in metrics.items():
                if func_metrics:
                    stats = PerformanceMonitor.get_stats(func_name)

                    # Performance recommendations
                    if stats["success_rate"] < 0.95:
                        analysis["recommendations"].append({
                            "type": "reliability",
                            "function": func_name,
                            "issue": f"Low success rate: {stats['success_rate']:.1%}",
                            "recommendation": "Implement retry logic and error handling improvements"
                        })

                    if stats["avg_execution_time"] > 10.0:  # More than 10 seconds
                        analysis["recommendations"].append({
                            "type": "performance",
                            "function": func_name,
                            "issue": f"Slow execution: {stats['avg_execution_time']:.2f}s average",
                            "recommendation": "Consider batching, parallelization, or optimization"
                        })

            return analysis

        except Exception as e:
            return {
                "error": f"Analysis failed: {str(e)}",
                "timestamp": datetime.utcnow().isoformat()
            }

    @performance_monitor(track_memory=True)
    @telemetry(event_type="agent_ingestion_optimization")
    def optimize_ingestion_process(self, process_config: Dict[str, Any]) -> Dict[str, Any]:
        """Optimize ingestion process configuration"""
        optimization_suggestions = []

        # Analyze batch size
        current_batch_size = process_config.get("batch_size", 100)
        if current_batch_size < 50:
            optimization_suggestions.append({
                "category": "batching",
                "current": current_batch_size,
                "recommended": 250,
                "reason": "Small batch sizes increase API calls and reduce efficiency"
            })

        # Analyze rate limiting
        rate_limit = process_config.get("rate_limit_delay", 0)
        if rate_limit == 0:
            optimization_suggestions.append({
                "category": "rate_limiting",
                "current": "No delay",
                "recommended": 0.5,
                "reason": "Rate limiting prevents API throttling and improves reliability"
            })

        # Analyze retry configuration
        max_retries = process_config.get("max_retries", 3)
        if max_retries < 3:
            optimization_suggestions.append({
                "category": "reliability",
                "current": max_retries,
                "recommended": 5,
                "reason": "Higher retry counts improve success rates for transient failures"
            })

        return {
            "original_config": process_config,
            "optimizations": optimization_suggestions,
            "estimated_improvement": f"{len(optimization_suggestions) * 15}%" if optimization_suggestions else "0%"
        }

    @feature_flag("ingestion_monitoring_enabled", default_enabled=True)
    @telemetry(event_type="agent_monitoring_setup")
    def setup_ingestion_monitoring(self, monitoring_config: Dict[str, Any]) -> Dict[str, Any]:
        """Set up comprehensive monitoring for ingestion processes"""
        monitoring_setup = {
            "telemetry_enabled": True,
            "performance_monitoring": True,
            "feature_flags": ["ingestion_enabled", "federal_bills_ingestion_enabled", "federal_committees_ingestion_enabled"],
            "alerts_configured": [],
            "dashboards": []
        }

        # Configure alerts based on monitoring config
        if monitoring_config.get("alert_on_failure_rate", True):
            monitoring_setup["alerts_configured"].append({
                "type": "failure_rate",
                "threshold": monitoring_config.get("failure_threshold", 0.05),
                "action": "notify_team"
            })

        if monitoring_config.get("alert_on_slow_performance", True):
            monitoring_setup["alerts_configured"].append({
                "type": "performance",
                "threshold_seconds": monitoring_config.get("slow_threshold", 30),
                "action": "log_warning"
            })

        # Set up dashboards
        monitoring_setup["dashboards"] = [
            {
                "name": "Ingestion Performance Dashboard",
                "metrics": ["success_rate", "avg_execution_time", "records_processed", "api_calls"],
                "refresh_interval": "5m"
            },
            {
                "name": "System Health Dashboard",
                "metrics": ["memory_usage", "cpu_usage", "error_rate"],
                "refresh_interval": "1m"
            }
        ]

        return monitoring_setup

    @telemetry(event_type="agent_ingestion_recovery")
    def handle_ingestion_failure(self, failure_details: Dict[str, Any]) -> Dict[str, Any]:
        """Handle and recover from ingestion failures"""
        failure_type = failure_details.get("failure_type", "unknown")
        error_message = failure_details.get("error_message", "")
        affected_records = failure_details.get("affected_records", 0)

        recovery_plan = {
            "failure_analysis": {
                "type": failure_type,
                "message": error_message,
                "severity": "high" if affected_records > 1000 else "medium" if affected_records > 100 else "low"
            },
            "immediate_actions": [],
            "recovery_steps": [],
            "preventive_measures": []
        }

        # Determine recovery strategy based on failure type
        if "rate_limit" in error_message.lower():
            recovery_plan["immediate_actions"].append("Implement exponential backoff")
            recovery_plan["recovery_steps"].append("Resume ingestion with reduced batch size")
            recovery_plan["preventive_measures"].append("Add rate limiting configuration")

        elif "connection" in error_message.lower():
            recovery_plan["immediate_actions"].append("Check network connectivity")
            recovery_plan["recovery_steps"].append("Retry with different endpoint if available")
            recovery_plan["preventive_measures"].append("Implement connection pooling")

        elif "database" in error_message.lower():
            recovery_plan["immediate_actions"].append("Check database connectivity")
            recovery_plan["recovery_steps"].append("Rollback transaction and retry")
            recovery_plan["preventive_measures"].append("Add database connection monitoring")

        else:
            recovery_plan["immediate_actions"].append("Log detailed error information")
            recovery_plan["recovery_steps"].append("Retry with exponential backoff")
            recovery_plan["preventive_measures"].append("Add comprehensive error handling")

        return recovery_plan

    def generate_ingestion_report(self, report_type: str = "comprehensive") -> str:
        """Generate detailed ingestion performance report"""
        if report_type == "performance":
            return get_performance_report()
        elif report_type == "comprehensive":
            # Export full telemetry and generate comprehensive report
            export_telemetry_to_file("ingestion_report.json")

            analysis = self.analyze_ingestion_performance()

            report = f"""
# OpenLegislation Data Ingestion Report
Generated: {datetime.utcnow().isoformat()}

## Executive Summary
- Total ingestion functions monitored: {len(analysis.get('performance_metrics', {}))}
- Active telemetry events: {analysis.get('telemetry_events', 0)}
- Optimization recommendations: {len(analysis.get('recommendations', []))}

## Performance Analysis
{json.dumps(analysis, indent=2)}

## Recommendations
{chr(10).join(f"- {rec['type'].upper()}: {rec['recommendation']}" for rec in analysis.get('recommendations', []))}
"""
            return report
        else:
            return "Invalid report type specified"


class FederalDataIngestionAgent(DataIngestionAgent):
    """Specialized agent for federal legislative data ingestion"""

    def __init__(self, **kwargs):
        super().__init__(
            role="Federal Data Ingestion Specialist",
            goal="Manage federal legislative data ingestion from congress.gov API with optimal performance and reliability",
            backstory="""You are a specialist in federal legislative data systems, with deep expertise in congress.gov API,
            federal data structures, and congressional processes. You ensure accurate, complete, and efficient
            ingestion of bills, committees, and related federal legislative data.""",
            **kwargs
        )

    def optimize_congress_api_ingestion(self, congress_number: int, data_type: str) -> Dict[str, Any]:
        """Optimize ingestion strategy for congress.gov API"""
        optimization = {
            "congress": congress_number,
            "data_type": data_type,
            "strategy": {},
            "expected_performance": {}
        }

        if data_type == "bills":
            optimization["strategy"] = {
                "batch_size": 250,
                "rate_limit_delay": 0.5,
                "concurrent_requests": 1,  # API limitations
                "pagination_strategy": "offset_based",
                "error_handling": "exponential_backoff"
            }
            optimization["expected_performance"] = {
                "records_per_minute": 120,
                "success_rate": 0.98,
                "estimated_duration_hours": 24  # For full congress
            }

        elif data_type == "committees":
            optimization["strategy"] = {
                "batch_size": 250,
                "rate_limit_delay": 0.3,
                "concurrent_requests": 1,
                "pagination_strategy": "offset_based",
                "error_handling": "retry_with_backoff"
            }
            optimization["expected_performance"] = {
                "records_per_minute": 200,
                "success_rate": 0.99,
                "estimated_duration_hours": 2
            }

        return optimization

    def validate_federal_data_quality(self, data_sample: Dict[str, Any]) -> Dict[str, Any]:
        """Validate quality of ingested federal data"""
        validation_results = {
            "overall_quality": "unknown",
            "checks_passed": 0,
            "total_checks": 0,
            "issues": [],
            "recommendations": []
        }

        # Required field checks
        required_fields = ["bill_print_no", "congress", "bill_type"] if "bill" in data_sample else ["name", "chamber"]
        for field in required_fields:
            validation_results["total_checks"] += 1
            if field not in data_sample or not data_sample[field]:
                validation_results["issues"].append(f"Missing required field: {field}")
            else:
                validation_results["checks_passed"] += 1

        # Data format validation
        if "congress" in data_sample:
            validation_results["total_checks"] += 1
            congress = data_sample["congress"]
            if isinstance(congress, int) and 110 <= congress <= 120:
                validation_results["checks_passed"] += 1
            else:
                validation_results["issues"].append(f"Invalid congress number: {congress}")

        # Calculate overall quality
        if validation_results["total_checks"] > 0:
            quality_score = validation_results["checks_passed"] / validation_results["total_checks"]
            if quality_score >= 0.9:
                validation_results["overall_quality"] = "excellent"
            elif quality_score >= 0.7:
                validation_results["overall_quality"] = "good"
            elif quality_score >= 0.5:
                validation_results["overall_quality"] = "fair"
            else:
                validation_results["overall_quality"] = "poor"

        return validation_results


class StateDataIngestionAgent(DataIngestionAgent):
    """Specialized agent for state legislative data ingestion"""

    def __init__(self, **kwargs):
        super().__init__(
            role="State Data Ingestion Specialist",
            goal="Manage state legislative data ingestion with support for multiple state systems and data formats",
            backstory="""You are an expert in state legislative data systems, familiar with the diverse data formats,
            APIs, and processes used by different state legislatures. You ensure comprehensive coverage
            of state legislative data across all 50 states.""",
            **kwargs
        )

    def analyze_state_data_sources(self, state_code: str) -> Dict[str, Any]:
        """Analyze available data sources for a specific state"""
        # This would contain logic to analyze state-specific data sources
        # For now, return a template structure
        return {
            "state": state_code,
            "available_sources": ["api", "bulk_download", "web_scraping"],
            "data_types": ["bills", "committees", "votes", "transcripts"],
            "update_frequency": "daily",
            "reliability_score": 0.85,
            "recommended_strategy": "api_with_fallback"
        }

    def coordinate_multi_state_ingestion(self, states: List[str]) -> Dict[str, Any]:
        """Coordinate ingestion across multiple states"""
        coordination_plan = {
            "states": states,
            "parallelization_strategy": "state_based",
            "rate_limiting": "per_state",
            "error_isolation": True,
            "progress_tracking": "individual_and_aggregate",
            "estimated_duration_hours": len(states) * 4
        }

        return coordination_plan


# Convenience functions for creating agents
def create_data_ingestion_agent(model_name: str = "gpt-4") -> DataIngestionAgent:
    """Create a data ingestion agent with specified model"""
    return DataIngestionAgent(llm=model_name)

def create_federal_ingestion_agent(model_name: str = "gpt-4") -> FederalDataIngestionAgent:
    """Create a federal data ingestion agent"""
    return FederalDataIngestionAgent(llm=model_name)

def create_state_ingestion_agent(model_name: str = "gpt-4") -> StateDataIngestionAgent:
    """Create a state data ingestion agent"""
    return StateDataIngestionAgent(llm=model_name)
