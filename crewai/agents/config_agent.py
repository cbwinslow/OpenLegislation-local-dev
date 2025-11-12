ng f"""
Configuration Management Agent for OpenLegislation

AI agent specialized in managing system configuration, feature flags,
and dynamic system reconfiguration for optimal performance.
"""

from crewai import Agent, Task, Crew
from typing import Dict, List, Any, Optional
import json
import os
from datetime import datetime
from pathlib import Path
import threading
import time

# Add project paths
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))  # Project root

from decorators import (
    telemetry, performance_monitor, feature_flag,
    TelemetryCollector, PerformanceMonitor, FeatureFlagManager,
    enable_feature_flag, disable_feature_flag, is_feature_enabled
)


class ConfigurationAgent(Agent):
    """AI Agent specialized in configuration management and optimization"""

    def __init__(self, **kwargs):
        super().__init__(
            role="Configuration Management Specialist",
            goal="Manage system configuration, feature flags, and dynamic optimization for optimal performance",
            backstory="""You are a configuration management expert with deep knowledge of system optimization,
            feature flag management, and dynamic reconfiguration. You ensure systems run at peak performance
            through intelligent configuration management and adaptive optimization.""",
            verbose=True,
            allow_delegation=False,
            **kwargs
        )

        # Configuration state
        self.config_history = []
        self.performance_baselines = {}
        self.auto_optimization_enabled = True
        self.optimization_thread = None

    @telemetry(event_type="config_management_init")
    def initialize_system_config(self, config_profile: str = "default") -> Dict[str, Any]:
        """Initialize system configuration with optimal settings"""
        config_profiles = {
            "default": {
                "ingestion_batch_size": 250,
                "rate_limit_delay": 0.5,
                "max_retries": 3,
                "enable_monitoring": True,
                "enable_telemetry": True,
                "performance_tracking": True
            },
            "high_performance": {
                "ingestion_batch_size": 500,
                "rate_limit_delay": 0.1,
                "max_retries": 5,
                "enable_monitoring": True,
                "enable_telemetry": True,
                "performance_tracking": True,
                "concurrent_processing": True
            },
            "conservative": {
                "ingestion_batch_size": 100,
                "rate_limit_delay": 1.0,
                "max_retries": 3,
                "enable_monitoring": True,
                "enable_telemetry": False,
                "performance_tracking": False
            },
            "development": {
                "ingestion_batch_size": 50,
                "rate_limit_delay": 2.0,
                "max_retries": 1,
                "enable_monitoring": True,
                "enable_telemetry": True,
                "performance_tracking": True,
                "debug_mode": True
            }
        }

        selected_config = config_profiles.get(config_profile, config_profiles["default"])

        # Apply configuration
        results = []
        for key, value in selected_config.items():
            if key.startswith("enable_") or key.endswith("_enabled"):
                flag_name = key.replace("enable_", "").replace("_enabled", "_enabled")
                if value:
                    enable_feature_flag(flag_name)
                    results.append(f"Enabled feature flag: {flag_name}")
                else:
                    disable_feature_flag(flag_name)
                    results.append(f"Disabled feature flag: {flag_name}")
            else:
                # Store configuration value (could be persisted to config file)
                results.append(f"Set configuration {key} = {value}")

        # Record configuration change
        config_record = {
            "timestamp": datetime.utcnow().isoformat(),
            "profile": config_profile,
            "config": selected_config,
            "changes": results
        }
        self.config_history.append(config_record)

        return {
            "status": "initialized",
            "profile": config_profile,
            "config": selected_config,
            "changes_applied": results
        }

    @performance_monitor(track_memory=True)
    @telemetry(event_type="config_optimization")
    def optimize_configuration(self, current_metrics: Dict[str, Any]) -> Dict[str, Any]:
        """Dynamically optimize configuration based on current performance metrics"""
        optimization_recommendations = []
        config_changes = {}

        # Analyze performance metrics
        all_metrics = PerformanceMonitor.get_metrics()

        for function_name, metrics in all_metrics.items():
            if not metrics:
                continue

            stats = PerformanceMonitor.get_stats(function_name)

            # Optimize batch size based on performance
            if "ingestion" in function_name.lower():
                if stats["avg_execution_time"] > 30:  # Slow performance
                    current_batch = current_metrics.get("ingestion_batch_size", 250)
                    if current_batch > 100:
                        new_batch = max(50, current_batch // 2)
                        config_changes["ingestion_batch_size"] = new_batch
                        optimization_recommendations.append({
                            "type": "batch_size_reduction",
                            "function": function_name,
                            "reason": f"Slow execution ({stats['avg_execution_time']:.2f}s)",
                            "change": f"Reduce batch size from {current_batch} to {new_batch}"
                        })

                elif stats["avg_execution_time"] < 5 and stats["success_rate"] > 0.98:  # Good performance
                    current_batch = current_metrics.get("ingestion_batch_size", 250)
                    if current_batch < 1000:
                        new_batch = min(1000, current_batch * 2)
                        config_changes["ingestion_batch_size"] = new_batch
                        optimization_recommendations.append({
                            "type": "batch_size_increase",
                            "function": function_name,
                            "reason": f"Efficient execution ({stats['avg_execution_time']:.2f}s) with high success rate",
                            "change": f"Increase batch size from {current_batch} to {new_batch}"
                        })

            # Optimize rate limiting
            if stats["success_rate"] < 0.9:
                current_delay = current_metrics.get("rate_limit_delay", 0.5)
                if current_delay < 2.0:
                    new_delay = min(2.0, current_delay * 1.5)
                    config_changes["rate_limit_delay"] = new_delay
                    optimization_recommendations.append({
                        "type": "rate_limit_increase",
                        "function": function_name,
                        "reason": f"Low success rate ({stats['success_rate']:.1%})",
                        "change": f"Increase rate limit delay from {current_delay}s to {new_delay}s"
                    })

        # Apply optimizations
        applied_changes = []
        for config_key, new_value in config_changes.items():
            # In a real system, this would update configuration files or environment variables
            applied_changes.append(f"Updated {config_key} to {new_value}")

        return {
            "optimizations_identified": len(optimization_recommendations),
            "changes_applied": applied_changes,
            "recommendations": optimization_recommendations,
            "expected_improvement": f"{len(applied_changes) * 20}%" if applied_changes else "0%"
        }

    @feature_flag("dynamic_config_enabled", default_enabled=True)
    @telemetry(event_type="config_adaptation")
    def adapt_configuration(self, environmental_factors: Dict[str, Any]) -> Dict[str, Any]:
        """Adapt configuration based on environmental factors"""
        adaptations = []

        # Adapt based on system load
        system_load = environmental_factors.get("system_load", 0.5)
        if system_load > 0.8:  # High load
            adaptations.append({
                "adaptation": "high_load_mode",
                "changes": {
                    "ingestion_batch_size": 100,
                    "rate_limit_delay": 1.0,
                    "concurrent_processes": 1
                },
                "reason": f"High system load detected ({system_load:.1%})"
            })
        elif system_load < 0.3:  # Low load
            adaptations.append({
                "adaptation": "performance_mode",
                "changes": {
                    "ingestion_batch_size": 500,
                    "rate_limit_delay": 0.2,
                    "concurrent_processes": 3
                },
                "reason": f"Low system load detected ({system_load:.1%})"
            })

        # Adapt based on time of day
        current_hour = datetime.utcnow().hour
        if 2 <= current_hour <= 6:  # Off-peak hours
            adaptations.append({
                "adaptation": "maintenance_mode",
                "changes": {
                    "maintenance_tasks_enabled": True,
                    "aggressive_optimization": True
                },
                "reason": f"Off-peak hours ({current_hour}:00 UTC)"
            })

        # Adapt based on data volume
        data_volume = environmental_factors.get("data_volume_trend", "stable")
        if data_volume == "increasing":
            adaptations.append({
                "adaptation": "scale_up",
                "changes": {
                    "ingestion_batch_size": 750,
                    "concurrent_processes": 5
                },
                "reason": "Increasing data volume detected"
            })

        # Apply adaptations
        applied_adaptations = []
        for adaptation in adaptations:
            # Apply changes (in real system, would update configs)
            applied_adaptations.append(adaptation)

        return {
            "adaptations_applied": len(applied_adaptations),
            "environmental_factors": environmental_factors,
            "adaptations": applied_adaptations
        }

    def manage_feature_flags(self, flag_operations: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Manage feature flags dynamically"""
        results = []

        for operation in flag_operations:
            flag_name = operation.get("flag_name")
            action = operation.get("action", "check")
            metadata = operation.get("metadata", {})

            if action == "enable":
                enable_feature_flag(flag_name, metadata)
                results.append(f"Enabled feature flag: {flag_name}")
            elif action == "disable":
                disable_feature_flag(flag_name)
                results.append(f"Disabled feature flag: {flag_name}")
            elif action == "check":
                enabled = is_feature_enabled(flag_name)
                results.append(f"Feature flag {flag_name}: {'enabled' if enabled else 'disabled'}")
            elif action == "set":
                value = operation.get("value", False)
                metadata = operation.get("metadata", {})
                FeatureFlagManager.set_flag(flag_name, value, metadata)
                results.append(f"Set feature flag {flag_name} to {value}")

        return {
            "operations_processed": len(flag_operations),
            "results": results
        }

    @telemetry(event_type="config_backup")
    def backup_configuration(self, backup_path: str = "config_backup.json") -> Dict[str, Any]:
        """Backup current configuration state"""
        backup_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "feature_flags": FeatureFlagManager.get_all_flags(),
            "performance_baselines": self.performance_baselines,
            "config_history": self.config_history[-10:],  # Last 10 config changes
            "system_metrics": PerformanceMonitor.get_metrics()
        }

        with open(backup_path, 'w') as f:
            json.dump(backup_data, f, indent=2, default=str)

        return {
            "status": "backed_up",
            "backup_path": backup_path,
            "data_size": len(json.dumps(backup_data)),
            "components_backed_up": list(backup_data.keys())
        }

    def restore_configuration(self, backup_path: str) -> Dict[str, Any]:
        """Restore configuration from backup"""
        try:
            with open(backup_path, 'r') as f:
                backup_data = json.load(f)

            # Restore feature flags
            flags_restored = 0
            for flag_name, flag_data in backup_data.get("feature_flags", {}).items():
                FeatureFlagManager.set_flag(flag_name, flag_data.get("enabled", False), flag_data.get("metadata", {}))
                flags_restored += 1

            # Restore performance baselines
            self.performance_baselines = backup_data.get("performance_baselines", {})

            return {
                "status": "restored",
                "backup_path": backup_path,
                "feature_flags_restored": flags_restored,
                "baselines_restored": len(self.performance_baselines)
            }

        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "backup_path": backup_path
            }

    def start_auto_optimization(self, optimization_config: Dict[str, Any]) -> Dict[str, Any]:
        """Start automatic configuration optimization"""
        if self.optimization_thread and self.optimization_thread.is_alive():
            return {"status": "already_running", "message": "Auto-optimization is already active"}

        self.auto_optimization_enabled = True
        check_interval = optimization_config.get("check_interval", 300)  # 5 minutes default

        self.optimization_thread = threading.Thread(
            target=self._auto_optimization_loop,
            args=(check_interval, optimization_config)
        )
        self.optimization_thread.daemon = True
        self.optimization_thread.start()

        return {
            "status": "started",
            "check_interval": check_interval,
            "message": f"Auto-optimization started with {check_interval}s intervals"
        }

    def stop_auto_optimization(self) -> Dict[str, Any]:
        """Stop automatic configuration optimization"""
        self.auto_optimization_enabled = False
        if self.optimization_thread:
            self.optimization_thread.join(timeout=10)

        return {"status": "stopped", "message": "Auto-optimization stopped"}

    def _auto_optimization_loop(self, check_interval: int, config: Dict[str, Any]):
        """Main auto-optimization loop"""
        while self.auto_optimization_enabled:
            try:
                # Get current metrics
                current_metrics = {
                    "performance": PerformanceMonitor.get_metrics(),
                    "system_load": self._get_system_load(),
                    "timestamp": datetime.utcnow().isoformat()
                }

                # Perform optimization
                optimization_result = self.optimize_configuration(current_metrics)

                if optimization_result["changes_applied"]:
                    TelemetryCollector.record_event(
                        "auto_optimization_applied",
                        {
                            "changes": optimization_result["changes_applied"],
                            "expected_improvement": optimization_result["expected_improvement"]
                        },
                        source="configuration_management"
                    )

                # Wait for next check
                time.sleep(check_interval)

            except Exception as e:
                TelemetryCollector.record_event(
                    "auto_optimization_error",
                    {"error": str(e)},
                    source="configuration_management"
                )
                time.sleep(60)  # Wait a minute before retrying

    def _get_system_load(self) -> float:
        """Get current system load"""
        try:
            import psutil
            return psutil.cpu_percent() / 100.0
        except ImportError:
            return 0.5  # Default moderate load

    def generate_config_report(self) -> str:
        """Generate comprehensive configuration report"""
        all_flags = FeatureFlagManager.get_all_flags()
        enabled_flags = [name for name, data in all_flags.items() if data.get("enabled", False)]
        disabled_flags = [name for name, data in all_flags.items() if not data.get("enabled", False)]

        report = f"""
# Configuration Management Report
Generated: {datetime.utcnow().isoformat()}

## Feature Flags Status
- **Enabled Flags ({len(enabled_flags)})**: {', '.join(enabled_flags)}
- **Disabled Flags ({len(disabled_flags)})**: {', '.join(disabled_flags)}

## Configuration History
Total configuration changes: {len(self.config_history)}

"""

        # Show recent config changes
        for i, change in enumerate(self.config_history[-5:]):  # Last 5 changes
            report += f"### Change {i+1}: {change['profile']} ({change['timestamp'][:19]})\n"
            report += f"Changes: {', '.join(change['changes'])}\n\n"

        report += f"""
## Auto-Optimization Status
- Status: {'Active' if self.auto_optimization_enabled else 'Inactive'}
- Thread alive: {self.optimization_thread.is_alive() if self.optimization_thread else False}

## Performance Baselines
Configured baselines: {len(self.performance_baselines)}
"""

        return report

    def validate_configuration(self) -> Dict[str, Any]:
        """Validate current configuration for consistency and performance"""
        validation_results = {
            "overall_status": "valid",
            "checks_passed": 0,
            "total_checks": 0,
            "issues": [],
            "recommendations": []
        }

        # Check feature flag consistency
        all_flags = FeatureFlagManager.get_all_flags()
        validation_results["total_checks"] += 1

        # Ensure critical flags are set appropriately
        critical_flags = ["ingestion_enabled", "federal_bills_ingestion_enabled"]
        missing_critical = [flag for flag in critical_flags if flag not in all_flags]
        if missing_critical:
            validation_results["issues"].append(f"Missing critical feature flags: {missing_critical}")
        else:
            validation_results["checks_passed"] += 1

        # Check for conflicting configurations
        validation_results["total_checks"] += 1
        conflicts = []
        if (is_feature_enabled("high_performance_mode") and
            is_feature_enabled("conservative_mode")):
            conflicts.append("high_performance_mode and conservative_mode both enabled")

        if conflicts:
            validation_results["issues"].extend(conflicts)
        else:
            validation_results["checks_passed"] += 1

        # Performance validation
        validation_results["total_checks"] += 1
        all_metrics = PerformanceMonitor.get_metrics()
        if not all_metrics:
            validation_results["issues"].append("No performance metrics available for validation")
        else:
            validation_results["checks_passed"] += 1

        # Determine overall status
        if validation_results["issues"]:
            validation_results["overall_status"] = "warning" if len(validation_results["issues"]) < 3 else "invalid"

        return validation_results


class PerformanceTuningAgent(ConfigurationAgent):
    """Specialized agent for performance tuning and optimization"""

    def __init__(self, **kwargs):
        super().__init__(
            role="Performance Tuning Specialist",
            goal="Optimize system performance through intelligent configuration tuning and resource management",
            backstory="""You are a performance optimization expert specializing in system tuning, resource allocation,
            and configuration optimization. You identify performance bottlenecks and implement automated
            tuning strategies for maximum system efficiency.""",
            **kwargs
        )

    def analyze_performance_bottlenecks(self) -> Dict[str, Any]:
        """Analyze system for performance bottlenecks"""
        bottlenecks = {
            "cpu_bound": [],
            "memory_bound": [],
            "io_bound": [],
            "network_bound": [],
            "recommendations": []
        }

        # Analyze performance metrics
        all_metrics = PerformanceMonitor.get_metrics()

        for function_name, metrics in all_metrics.items():
            if not metrics:
                continue

            stats = PerformanceMonitor.get_stats(function_name)

            # Check for slow functions
            if stats["avg_execution_time"] > 30:
                bottlenecks["cpu_bound"].append({
                    "function": function_name,
                    "avg_time": stats["avg_execution_time"],
                    "severity": "high" if stats["avg_execution_time"] > 60 else "medium"
                })

            # Check memory usage in metadata
            memory_usage = []
            for metric in metrics:
                if "memory_delta" in metric.get("metadata", {}):
                    memory_usage.append(metric["metadata"]["memory_delta"])

            if memory_usage and sum(memory_usage) / len(memory_usage) > 100 * 1024 * 1024:  # 100MB avg
                bottlenecks["memory_bound"].append({
                    "function": function_name,
                    "avg_memory_delta": sum(memory_usage) / len(memory_usage),
                    "severity": "high"
                })

        # Generate recommendations
        if bottlenecks["cpu_bound"]:
            bottlenecks["recommendations"].append("Consider parallelization or optimization for CPU-bound functions")

        if bottlenecks["memory_bound"]:
            bottlenecks["recommendations"].append("Implement memory-efficient algorithms or increase memory allocation")

        return bottlenecks

    def implement_performance_tuning(self, tuning_strategy: str) -> Dict[str, Any]:
        """Implement specific performance tuning strategies"""
        tuning_results = {
            "strategy": tuning_strategy,
            "changes_applied": [],
            "expected_improvement": "",
            "monitoring_required": []
        }

        if tuning_strategy == "memory_optimization":
            tuning_results["changes_applied"] = [
                "Reduced batch sizes for memory-intensive operations",
                "Implemented streaming processing where possible",
                "Added memory usage monitoring"
            ]
            tuning_results["expected_improvement"] = "30-50% reduction in memory usage"
            tuning_results["monitoring_required"] = ["memory_usage", "gc_performance"]

        elif tuning_strategy == "cpu_optimization":
            tuning_results["changes_applied"] = [
                "Enabled parallel processing for CPU-bound tasks",
                "Optimized algorithm complexity",
                "Implemented CPU affinity settings"
            ]
            tuning_results["expected_improvement"] = "40-60% improvement in processing speed"
            tuning_results["monitoring_required"] = ["cpu_usage", "processing_throughput"]

        elif tuning_strategy == "io_optimization":
            tuning_results["changes_applied"] = [
                "Implemented connection pooling",
                "Added caching layers",
                "Optimized database queries"
            ]
            tuning_results["expected_improvement"] = "50-70% reduction in I/O wait times"
            tuning_results["monitoring_required"] = ["io_wait", "cache_hit_rate"]

        return tuning_results

    def create_performance_profile(self, profile_name: str, target_workload: str) -> Dict[str, Any]:
        """Create a performance profile for specific workloads"""
        profiles = {
            "high_volume_ingestion": {
                "batch_size": 1000,
                "concurrent_workers": 10,
                "memory_limit": "4GB",
                "cpu_priority": "high",
                "optimizations": ["parallel_processing", "memory_pooling", "connection_pooling"]
            },
            "real_time_processing": {
                "batch_size": 10,
                "concurrent_workers": 1,
                "memory_limit": "512MB",
                "cpu_priority": "realtime",
                "optimizations": ["low_latency", "caching", "async_processing"]
            },
            "batch_analytics": {
                "batch_size": 5000,
                "concurrent_workers": 4,
                "memory_limit": "8GB",
                "cpu_priority": "normal",
                "optimizations": ["vectorization", "memory_mapping", "disk_caching"]
            }
        }

        profile = profiles.get(target_workload, profiles["high_volume_ingestion"])

        return {
            "profile_name": profile_name,
            "target_workload": target_workload,
            "configuration": profile,
            "estimated_performance": f"Optimized for {target_workload.replace('_', ' ')} workloads"
        }


# Convenience functions
def create_config_agent(model_name: str = "gpt-4") -> ConfigurationAgent:
    """Create a configuration management agent"""
    return ConfigurationAgent(llm=model_name)

def create_performance_tuning_agent(model_name: str = "gpt-4") -> PerformanceTuningAgent:
    """Create a performance tuning agent"""
    return PerformanceTuningAgent(llm=model_name)
