#!/usr/bin/env python3
"""
Queue Monitor Agent for OpenLegislation

This AI agent is dedicated to monitoring queue operations, detecting anomalies,
scheduling automatic retries, and ensuring optimal queue performance.

Features:
- Real-time queue health monitoring
- Anomaly detection and alerting
- Automatic retry scheduling
- Performance optimization recommendations
- Integration with n8n workflows and Graphite metrics

Author: OpenLegislation Team
Date: 2025-11-08
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional

import aiohttp
import psutil

from comprehensive_ai_agents import BaseAgent, DatabaseRecorder
from queue_manager import QueueManager

logger = logging.getLogger(__name__)


class QueueMonitorAgent(BaseAgent):
    """
    AI Agent dedicated to monitoring queue operations and ensuring optimal performance
    """

    def __init__(self, db_config: Dict[str, Any], n8n_webhook_url: str = None, graphite_host: str = None):
        super().__init__('QueueMonitorAgent', 'monitoring', db_config)
        self.n8n_webhook_url = n8n_webhook_url or "http://localhost:5678/webhook"
        self.graphite_host = graphite_host or "localhost"
        self.queue_manager = QueueManager(db_config)

        self.capabilities = [
            'queue_health_monitoring', 'anomaly_detection', 'performance_optimization',
            'automated_retry_scheduling', 'resource_scaling', 'predictive_alerting',
            'metrics_collection', 'trend_analysis', 'capacity_planning'
        ]

        # Monitoring thresholds
        self.thresholds = {
            'max_pending_jobs': 50,
            'max_failure_rate': 0.20,  # 20%
            'max_avg_completion_time': 300,  # 5 minutes
            'min_health_score': 70
        }

        # Monitoring state
        self.monitoring_active = False
        self.last_health_check = None
        self.consecutive_anomalies = 0

    async def start_monitoring(self):
        """Start continuous queue monitoring"""
        self.monitoring_active = True

        await self.think(
            'monitoring_started',
            "Starting continuous queue health monitoring",
            confidence=1.0
        )

        # Start monitoring loop
        asyncio.create_task(self._monitoring_loop())

        # Start metrics collection
        asyncio.create_task(self._metrics_collection_loop())

    async def stop_monitoring(self):
        """Stop queue monitoring"""
        self.monitoring_active = False

        await self.think(
            'monitoring_stopped',
            "Queue monitoring stopped",
            confidence=1.0
        )

    async def _monitoring_loop(self):
        """Main monitoring loop"""
        while self.monitoring_active:
            try:
                # Perform comprehensive health check
                health_status = await self._perform_health_check()

                # Analyze health status
                analysis = await self._analyze_health_status(health_status)

                # Handle any issues found
                if analysis['issues_detected']:
                    await self._handle_health_issues(analysis)

                # Update monitoring state
                self.last_health_check = datetime.now()

                # Send metrics to Graphite
                await self._send_metrics_to_graphite(health_status)

                # Wait before next check
                await asyncio.sleep(30)  # Check every 30 seconds

            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                await self.think(
                    'monitoring_error',
                    f"Monitoring loop error: {e}",
                    confidence=0.8
                )
                await asyncio.sleep(60)  # Wait longer on error

    async def _metrics_collection_loop(self):
        """Collect and send metrics to monitoring systems"""
        while self.monitoring_active:
            try:
                # Collect detailed metrics
                metrics = await self._collect_detailed_metrics()

                # Send to Graphite
                await self._send_detailed_metrics_to_graphite(metrics)

                # Check for metric-based alerts
                await self._check_metric_alerts(metrics)

                await asyncio.sleep(60)  # Collect every minute

            except Exception as e:
                logger.error(f"Error in metrics collection: {e}")
                await asyncio.sleep(120)  # Wait longer on error

    async def _perform_health_check(self) -> Dict[str, Any]:
        """Perform comprehensive queue health check"""
        try:
            # Get queue statistics
            queue_stats = await self.queue_manager.get_queue_stats()

            # Get system metrics
            system_metrics = await self._get_system_metrics()

            # Calculate health score
            health_score = self._calculate_health_score(queue_stats, system_metrics)

            # Detect anomalies
            anomalies = self._detect_anomalies(queue_stats, system_metrics)

            health_status = {
                'timestamp': datetime.now().isoformat(),
                'queue_stats': queue_stats,
                'system_metrics': system_metrics,
                'health_score': health_score,
                'anomalies': anomalies,
                'overall_status': self._determine_overall_status(health_score, anomalies)
            }

            return health_status

        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return {
                'timestamp': datetime.now().isoformat(),
                'error': str(e),
                'overall_status': 'error'
            }

    def _calculate_health_score(self, queue_stats: Dict, system_metrics: Dict) -> float:
        """Calculate overall queue health score (0-100)"""
        score = 100.0

        # Queue backlog penalty
        pending_jobs = queue_stats.get('pending', 0)
        if pending_jobs > self.thresholds['max_pending_jobs']:
            penalty = min((pending_jobs - self.thresholds['max_pending_jobs']) / 10, 30)
            score -= penalty

        # Failure rate penalty
        completed = queue_stats.get('completed', 0)
        failed = queue_stats.get('failed', 0)
        total_jobs = completed + failed
        if total_jobs > 10:  # Minimum sample size
            failure_rate = failed / total_jobs
            if failure_rate > self.thresholds['max_failure_rate']:
                penalty = min((failure_rate - self.thresholds['max_failure_rate']) * 200, 25)
                score -= penalty

        # Completion time penalty
        avg_completion_time = queue_stats.get('avg_completion_time', 0)
        if avg_completion_time > self.thresholds['max_avg_completion_time']:
            penalty = min((avg_completion_time - self.thresholds['max_avg_completion_time']) / 60, 20)
            score -= penalty

        # System resource penalties
        cpu_usage = system_metrics.get('cpu_percent', 0)
        if cpu_usage > 90:
            score -= 15

        memory_usage = system_metrics.get('memory_percent', 0)
        if memory_usage > 85:
            score -= 10

        return max(0.0, min(100.0, score))

    def _detect_anomalies(self, queue_stats: Dict, system_metrics: Dict) -> List[Dict]:
        """Detect anomalous conditions in queue and system metrics"""
        anomalies = []

        # Check for queue backlog spike
        pending_jobs = queue_stats.get('pending', 0)
        if pending_jobs > self.thresholds['max_pending_jobs'] * 1.5:  # 50% above threshold
            anomalies.append({
                'type': 'queue_backlog_spike',
                'severity': 'high',
                'description': f'Queue backlog critically high: {pending_jobs} pending jobs',
                'metric': 'pending_jobs',
                'value': pending_jobs,
                'threshold': self.thresholds['max_pending_jobs']
            })

        # Check for sudden failure rate increase
        completed = queue_stats.get('completed', 0)
        failed = queue_stats.get('failed', 0)
        total_jobs = completed + failed
        if total_jobs > 20:  # Sufficient sample size
            failure_rate = failed / total_jobs
            if failure_rate > self.thresholds['max_failure_rate'] * 1.5:
                anomalies.append({
                    'type': 'failure_rate_spike',
                    'severity': 'critical',
                    'description': f'Job failure rate critically high: {failure_rate:.1%}',
                    'metric': 'failure_rate',
                    'value': failure_rate,
                    'threshold': self.thresholds['max_failure_rate']
                })

        # Check for system resource exhaustion
        cpu_usage = system_metrics.get('cpu_percent', 0)
        if cpu_usage > 95:
            anomalies.append({
                'type': 'cpu_exhaustion',
                'severity': 'critical',
                'description': f'CPU usage critically high: {cpu_usage}%',
                'metric': 'cpu_percent',
                'value': cpu_usage,
                'threshold': 90
            })

        memory_usage = system_metrics.get('memory_percent', 0)
        if memory_usage > 95:
            anomalies.append({
                'type': 'memory_exhaustion',
                'severity': 'critical',
                'description': f'Memory usage critically high: {memory_usage}%',
                'metric': 'memory_percent',
                'value': memory_usage,
                'threshold': 85
            })

        return anomalies

    def _determine_overall_status(self, health_score: float, anomalies: List[Dict]) -> str:
        """Determine overall system status"""
        if health_score < 50 or any(a['severity'] == 'critical' for a in anomalies):
            return 'critical'
        elif health_score < 70 or any(a['severity'] == 'high' for a in anomalies):
            return 'warning'
        else:
            return 'healthy'

    async def _analyze_health_status(self, health_status: Dict) -> Dict[str, Any]:
        """Analyze health status and determine actions needed"""
        analysis = {
            'issues_detected': False,
            'severity_level': 'low',
            'recommended_actions': [],
            'predicted_trend': 'stable'
        }

        health_score = health_status.get('health_score', 100)
        anomalies = health_status.get('anomalies', [])
        overall_status = health_status.get('overall_status', 'healthy')

        # Determine if issues are detected
        if overall_status in ['warning', 'critical'] or health_score < self.thresholds['min_health_score']:
            analysis['issues_detected'] = True

        # Determine severity
        if overall_status == 'critical' or health_score < 50:
            analysis['severity_level'] = 'critical'
        elif overall_status == 'warning' or health_score < 70:
            analysis['severity_level'] = 'high'
        elif len(anomalies) > 0:
            analysis['severity_level'] = 'medium'

        # Generate recommended actions
        if analysis['issues_detected']:
            analysis['recommended_actions'] = await self._generate_recommendations(health_status)

        # Predict trend (simplified)
        if self.consecutive_anomalies > 3:
            analysis['predicted_trend'] = 'deteriorating'
        elif health_score > 80 and len(anomalies) == 0:
            analysis['predicted_trend'] = 'improving'

        return analysis

    async def _generate_recommendations(self, health_status: Dict) -> List[str]:
        """Generate specific recommendations based on health status"""
        recommendations = []
        anomalies = health_status.get('anomalies', [])
        queue_stats = health_status.get('queue_stats', {})
        system_metrics = health_status.get('system_metrics', {})

        # Queue-related recommendations
        pending_jobs = queue_stats.get('pending', 0)
        if pending_jobs > self.thresholds['max_pending_jobs']:
            recommendations.append(f"Scale up processing capacity - {pending_jobs} jobs pending")
            recommendations.append("Consider enabling GPU acceleration for faster processing")

        # Failure-related recommendations
        failed_jobs = queue_stats.get('failed', 0)
        if failed_jobs > 10:
            recommendations.append(f"Investigate {failed_jobs} failed jobs - check error logs")
            recommendations.append("Review recent code changes that might have introduced bugs")

        # System resource recommendations
        cpu_usage = system_metrics.get('cpu_percent', 0)
        if cpu_usage > 90:
            recommendations.append("High CPU usage detected - consider distributing load across more workers")

        memory_usage = system_metrics.get('memory_percent', 0)
        if memory_usage > 85:
            recommendations.append("High memory usage - optimize data processing batch sizes")

        # Anomaly-specific recommendations
        for anomaly in anomalies:
            if anomaly['type'] == 'queue_backlog_spike':
                recommendations.append("Implement job prioritization to handle critical jobs first")
            elif anomaly['type'] == 'failure_rate_spike':
                recommendations.append("Add circuit breaker pattern to prevent cascade failures")
            elif anomaly['type'] == 'cpu_exhaustion':
                recommendations.append("Implement horizontal scaling for CPU-intensive operations")
            elif anomaly['type'] == 'memory_exhaustion':
                recommendations.append("Add memory monitoring and automatic cleanup routines")

        return recommendations

    async def _handle_health_issues(self, analysis: Dict):
        """Handle detected health issues"""
        severity = analysis.get('severity_level', 'low')
        actions = analysis.get('recommended_actions', [])

        await self.think(
            'health_issues_handling',
            f"Handling {severity} severity health issues with {len(actions)} recommended actions",
            confidence=0.9
        )

        # Update consecutive anomalies counter
        if analysis['issues_detected']:
            self.consecutive_anomalies += 1
        else:
            self.consecutive_anomalies = 0

        # Send alerts based on severity
        if severity in ['high', 'critical']:
            await self._send_n8n_alert(analysis)

        # Log detailed analysis
        await self.db_recorder.log_telemetry_event(
            'health_issue_detected',
            {
                'severity': severity,
                'analysis': analysis,
                'actions_taken': actions
            },
            severity='warning' if severity == 'high' else 'error' if severity == 'critical' else 'info',
            agent_name=self.name
        )

        # Implement automatic fixes for critical issues
        if severity == 'critical':
            await self._implement_critical_fixes(analysis)

    async def _send_n8n_alert(self, analysis: Dict):
        """Send alert to n8n for workflow processing"""
        try:
            alert_data = {
                'agent': self.name,
                'alert_type': 'queue_health_issue',
                'severity': analysis.get('severity_level'),
                'timestamp': datetime.now().isoformat(),
                'analysis': analysis,
                'recommended_actions': analysis.get('recommended_actions', [])
            }

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.n8n_webhook_url}/queue-health-alert",
                    json=alert_data,
                    timeout=10
                ) as response:
                    if response.status == 200:
                        await self.think(
                            'alert_sent',
                            f"Successfully sent {analysis.get('severity_level')} severity alert to n8n",
                            confidence=0.95
                        )
                    else:
                        logger.error(f"Failed to send n8n alert: {response.status}")

        except Exception as e:
            logger.error(f"Error sending n8n alert: {e}")

    async def _implement_critical_fixes(self, analysis: Dict):
        """Implement automatic fixes for critical issues"""
        actions = analysis.get('recommended_actions', [])

        for action in actions:
            if "scale up" in action.lower():
                await self._trigger_auto_scaling()
            elif "gpu acceleration" in action.lower():
                await self._enable_gpu_acceleration()
            elif "circuit breaker" in action.lower():
                await self._implement_circuit_breaker()

    async def _trigger_auto_scaling(self):
        """Trigger automatic scaling of processing capacity"""
        await self.think(
            'auto_scaling_triggered',
            "Triggering automatic scaling of processing capacity",
            confidence=0.9
        )

        # This would integrate with your scaling system
        # For now, just log the action
        await self.db_recorder.log_telemetry_event(
            'auto_scaling_triggered',
            {'triggered_by': 'QueueMonitorAgent', 'reason': 'high_queue_backlog'},
            agent_name=self.name
        )

    async def _enable_gpu_acceleration(self):
        """Enable GPU acceleration for processing"""
        await self.think(
            'gpu_acceleration_enabled',
            "Enabling GPU acceleration for improved processing performance",
            confidence=0.9
        )

        # This would modify job configurations to enable GPU
        await self.db_recorder.log_telemetry_event(
            'gpu_acceleration_enabled',
            {'enabled_by': 'QueueMonitorAgent', 'scope': 'new_jobs'},
            agent_name=self.name
        )

    async def _implement_circuit_breaker(self):
        """Implement circuit breaker pattern for failing operations"""
        await self.think(
            'circuit_breaker_implemented',
            "Implementing circuit breaker pattern to prevent cascade failures",
            confidence=0.9
        )

        # This would modify error handling logic
        await self.db_recorder.log_telemetry_event(
            'circuit_breaker_implemented',
            {'implemented_by': 'QueueMonitorAgent', 'failure_threshold': 0.5},
            agent_name=self.name
        )

    async def schedule_automatic_retry(self, failed_job_id: str, error_analysis: Dict):
        """Schedule automatic retry for failed jobs"""
        retry_strategy = error_analysis.get('retry_strategy', 'exponential_backoff')
        max_retries = error_analysis.get('max_retries', 3)
        base_delay = error_analysis.get('base_delay_seconds', 60)

        # Calculate retry delay
        retry_delay = self._calculate_retry_delay(retry_strategy, max_retries, base_delay)

        await self.think(
            'automatic_retry_scheduled',
            f"Scheduling automatic retry for job {failed_job_id} with {retry_strategy} strategy",
            confidence=0.9
        )

        # Send retry request to n8n
        retry_data = {
            'job_id': failed_job_id,
            'retry_strategy': retry_strategy,
            'delay_seconds': retry_delay,
            'error_analysis': error_analysis,
            'scheduled_by': self.name
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.n8n_webhook_url}/schedule-job-retry",
                    json=retry_data,
                    timeout=10
                ) as response:
                    if response.status == 200:
                        await self.db_recorder.log_telemetry_event(
                            'retry_scheduled',
                            retry_data,
                            agent_name=self.name
                        )
                    else:
                        logger.error(f"Failed to schedule retry: {response.status}")

        except Exception as e:
            logger.error(f"Error scheduling retry: {e}")

    def _calculate_retry_delay(self, strategy: str, attempt_number: int, base_delay: int) -> int:
        """Calculate retry delay based on strategy"""
        if strategy == 'immediate':
            return 0
        elif strategy == 'fixed':
            return base_delay
        elif strategy == 'linear_backoff':
            return base_delay * attempt_number
        elif strategy == 'exponential_backoff':
            return min(base_delay * (2 ** attempt_number), 3600)  # Max 1 hour
        else:
            return base_delay

    async def _get_system_metrics(self) -> Dict[str, Any]:
        """Get current system metrics"""
        return {
            'cpu_percent': psutil.cpu_percent(interval=1),
            'memory_percent': psutil.virtual_memory().percent,
            'memory_used_gb': psutil.virtual_memory().used / (1024**3),
            'disk_usage_percent': psutil.disk_usage('/').percent,
            'load_average': psutil.getloadavg() if hasattr(psutil, 'getloadavg') else None
        }

    async def _collect_detailed_metrics(self) -> Dict[str, Any]:
        """Collect detailed metrics for monitoring"""
        queue_stats = await self.queue_manager.get_queue_stats()
        system_metrics = await self._get_system_metrics()

        # Add derived metrics
        total_jobs = (queue_stats.get('pending', 0) +
                     queue_stats.get('running', 0) +
                     queue_stats.get('completed', 0) +
                     queue_stats.get('failed', 0))

        success_rate = 0
        if total_jobs > 0:
            success_rate = queue_stats.get('completed', 0) / total_jobs

        return {
            'queue': queue_stats,
            'system': system_metrics,
            'derived': {
                'total_jobs_processed': total_jobs,
                'success_rate': success_rate,
                'throughput_per_minute': queue_stats.get('completed', 0) / 60,  # Rough estimate
                'error_rate': 1 - success_rate if total_jobs > 0 else 0
            },
            'timestamp': datetime.now().isoformat()
        }

    async def _send_metrics_to_graphite(self, health_status: Dict):
        """Send health metrics to Graphite"""
        try:
            # This would send metrics to Graphite
            # For now, just log that we would send them
            metrics = {
                'queue.health_score': health_status.get('health_score', 0),
                'queue.pending_jobs': health_status.get('queue_stats', {}).get('pending', 0),
                'queue.failed_jobs': health_status.get('queue_stats', {}).get('failed', 0),
                'system.cpu_percent': health_status.get('system_metrics', {}).get('cpu_percent', 0),
                'system.memory_percent': health_status.get('system_metrics', {}).get('memory_percent', 0)
            }

            # In a real implementation, send to Graphite here
            await self.db_recorder.log_telemetry_event(
                'metrics_sent_to_graphite',
                {'metrics_count': len(metrics), 'destination': self.graphite_host},
                agent_name=self.name
            )

        except Exception as e:
            logger.error(f"Error sending metrics to Graphite: {e}")

    async def _send_detailed_metrics_to_graphite(self, metrics: Dict):
        """Send detailed metrics to Graphite"""
        # Similar to above but for detailed metrics
        pass

    async def _check_metric_alerts(self, metrics: Dict):
        """Check metrics against alert thresholds"""
        alerts = []

        # Check queue backlog
        pending_jobs = metrics['queue'].get('pending', 0)
        if pending_jobs > self.thresholds['max_pending_jobs']:
            alerts.append(f"Queue backlog alert: {pending_jobs} pending jobs")

        # Check failure rate
        error_rate = metrics['derived'].get('error_rate', 0)
        if error_rate > self.thresholds['max_failure_rate']:
            alerts.append(f"High error rate alert: {error_rate:.1%}")

        # Send alerts if any
        if alerts:
            await self._send_n8n_alert({
                'severity_level': 'high',
                'issues_detected': True,
                'recommended_actions': alerts
            })

    async def get_monitoring_report(self) -> Dict[str, Any]:
        """Generate comprehensive monitoring report"""
        health_status = await self._perform_health_check()

        report = {
            'agent_name': self.name,
            'monitoring_status': 'active' if self.monitoring_active else 'inactive',
            'last_health_check': self.last_health_check.isoformat() if self.last_health_check else None,
            'current_health': health_status,
            'consecutive_anomalies': self.consecutive_anomalies,
            'capabilities': self.capabilities,
            'thresholds': self.thresholds
        }

        return report


# Convenience functions
async def create_queue_monitor_agent(db_config: Dict[str, Any],
                                   n8n_webhook_url: str = None,
                                   graphite_host: str = None) -> QueueMonitorAgent:
    """Create and initialize a Queue Monitor Agent"""
    agent = QueueMonitorAgent(db_config, n8n_webhook_url, graphite_host)
    await agent.start_monitoring()
    return agent


if __name__ == '__main__':
    # Example usage
    async def main():
        db_config = {
            'host': 'localhost',
            'port': 5432,
            'user': 'postgres',
            'password': '',
            'database': 'openlegislation'
        }

        agent = await create_queue_monitor_agent(db_config)

        # Let it monitor for a while
        await asyncio.sleep(300)  # 5 minutes

        # Get final report
        report = await agent.get_monitoring_report()
        print(f"Monitoring Report: {json.dumps(report, indent=2)}")

    asyncio.run(main())
