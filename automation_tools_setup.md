# OpenLegislation Automation Tools Integration

This document outlines the integration of advanced automation tools into the OpenLegislation platform:

- **n8n**: Workflow automation and API orchestration
- **Flowise**: AI-powered workflow builder
- **Graphite**: Real-time monitoring and metrics
- **Agentic Knowledge Graph**: AI-driven knowledge management

## 🛠️ Tool Overview

### n8n - Workflow Automation
**Purpose**: API orchestration, scheduled tasks, and complex workflow automation
**Integration Points**:
- Queue job scheduling and monitoring
- API data ingestion workflows
- Error handling and retry logic
- Notification systems

### Flowise - AI Workflow Builder
**Purpose**: Visual AI workflow creation and management
**Integration Points**:
- AI agent orchestration
- Decision tree automation
- Data processing pipelines
- User interaction workflows

### Graphite - Monitoring & Metrics
**Purpose**: Real-time performance monitoring and alerting
**Integration Points**:
- System performance metrics
- Queue health monitoring
- AI agent performance tracking
- Automated alerting

### Agentic Knowledge Graph
**Purpose**: AI-powered knowledge management and reasoning
**Integration Points**:
- Legislative data relationships
- AI agent knowledge sharing
- Automated decision making
- Context-aware processing

## 🚀 Implementation Plan

### Phase 1: Infrastructure Setup

#### 1.1 Docker Compose Setup
```yaml
# docker-compose.automation.yml
version: '3.8'
services:
  n8n:
    image: n8nio/n8n:latest
    ports:
      - "5678:5678"
    environment:
      - N8N_BASIC_AUTH_ACTIVE=true
      - N8N_BASIC_AUTH_USER=admin
      - N8N_BASIC_AUTH_PASSWORD=${N8N_PASSWORD}
    volumes:
      - n8n_data:/home/node/.n8n
    networks:
      - automation

  flowise:
    image: flowiseai/flowise:latest
    ports:
      - "3000:3000"
    environment:
      - PORT=3000
    volumes:
      - flowise_data:/app/packages/server
    networks:
      - automation

  graphite:
    image: graphiteapp/graphite-web:latest
    ports:
      - "8080:8080"
    environment:
      - GRAPHITE_ROOT=/opt/graphite
    volumes:
      - graphite_data:/opt/graphite/storage
    networks:
      - automation

  agentic-kg:
    build: ./agentic-knowledge-graph
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=${DATABASE_URL}
    volumes:
      - kg_data:/app/data
    networks:
      - automation

networks:
  automation:
    driver: bridge

volumes:
  n8n_data:
  flowise_data:
  graphite_data:
  kg_data:
```

#### 1.2 Environment Configuration
```bash
# .env.automation
# n8n Configuration
N8N_PASSWORD=secure_password_here
N8N_WEBHOOK_URL=https://your-domain.com

# Flowise Configuration
FLOWISE_USERNAME=admin
FLOWISE_PASSWORD=secure_password_here

# Graphite Configuration
GRAPHITE_API_KEY=your_api_key_here

# Agentic Knowledge Graph
KG_API_KEY=your_api_key_here
KG_DATABASE_URL=postgresql://user:pass@localhost:5432/openlegislation

# OpenLegislation Integration
OPENLEGISLATION_API_URL=http://localhost:8000
QUEUE_MANAGER_URL=http://localhost:8001
```

### Phase 2: n8n Workflow Integration

#### 2.1 Queue Management Workflows

**Workflow: Automated Ingestion Scheduling**
```
Trigger: Cron Schedule (every 6 hours)
→ Check Queue Status
→ Submit Congress Data Ingestion Job
→ Monitor Job Progress
→ Send Notifications on Completion/Failure
→ Trigger Data Validation
```

**Workflow: Error Handling & Recovery**
```
Trigger: Queue Job Failure
→ Analyze Error Type
→ Determine Retry Strategy
→ Submit Retry Job with Backoff
→ Notify Engineering Team
→ Update Knowledge Graph with Error Pattern
```

**Workflow: Performance Monitoring**
```
Trigger: Every 5 minutes
→ Collect System Metrics
→ Send to Graphite
→ Check Performance Thresholds
→ Trigger Scaling Actions if Needed
→ Update Dashboard
```

#### 2.2 API Integration Workflows

**Congress.gov Data Pipeline**
```
Schedule Trigger → API Request → Data Processing → Queue Submission → Monitoring → Validation
```

**Cross-System Synchronization**
```
Database Change → n8n Webhook → Flowise Decision → Knowledge Graph Update → Notification
```

### Phase 3: Flowise AI Workflow Integration

#### 3.1 AI Agent Orchestration

**Workflow: Intelligent Job Scheduling**
```
User Request → AI Analysis → Queue Optimization → Job Submission → Progress Tracking
```

**Workflow: Automated Troubleshooting**
```
Error Detected → AI Diagnosis → Solution Generation → Automated Fix → Verification
```

**Workflow: Performance Optimization**
```
Metrics Analysis → AI Recommendations → Automated Implementation → Results Validation
```

#### 3.2 Decision Tree Automation

**Data Quality Assessment**
```
Data Ingestion → Quality Checks → AI Analysis → Accept/Reject/Retry Decision
```

**Resource Allocation**
```
System Load → AI Assessment → Resource Adjustment → Performance Monitoring
```

### Phase 4: Graphite Monitoring Setup

#### 4.1 Metrics Collection

**System Metrics**
```python
# metrics/system_metrics.py
import psutil
import time
from graphite.client import GraphiteClient

class SystemMetricsCollector:
    def __init__(self, graphite_host='localhost', graphite_port=2003):
        self.client = GraphiteClient(graphite_host, graphite_port)

    def collect_system_metrics(self):
        """Collect comprehensive system metrics"""
        metrics = {
            'cpu.usage': psutil.cpu_percent(interval=1),
            'memory.usage': psutil.virtual_memory().percent,
            'memory.used': psutil.virtual_memory().used,
            'disk.usage': psutil.disk_usage('/').percent,
            'network.bytes_sent': psutil.net_io_counters().bytes_sent,
            'network.bytes_recv': psutil.net_io_counters().bytes_recv,
        }

        # Send to Graphite
        timestamp = int(time.time())
        for metric_name, value in metrics.items():
            self.client.send(metric_name, value, timestamp)

    def collect_queue_metrics(self, queue_manager):
        """Collect queue-specific metrics"""
        stats = await queue_manager.get_queue_stats()

        metrics = {
            'queue.pending_jobs': stats.get('pending', 0),
            'queue.running_jobs': stats.get('running', 0),
            'queue.completed_jobs': stats.get('completed', 0),
            'queue.failed_jobs': stats.get('failed', 0),
            'queue.avg_completion_time': stats.get('avg_completion_time', 0),
        }

        timestamp = int(time.time())
        for metric_name, value in metrics.items():
            self.client.send(metric_name, value, timestamp)
```

**AI Agent Metrics**
```python
# metrics/agent_metrics.py
class AgentMetricsCollector:
    def __init__(self, graphite_client):
        self.client = graphite_client

    def record_agent_interaction(self, agent_name, interaction_type, duration):
        """Record AI agent interaction metrics"""
        timestamp = int(time.time())

        self.client.send(f'agents.{agent_name}.interactions.{interaction_type}', 1, timestamp)
        self.client.send(f'agents.{agent_name}.duration.{interaction_type}', duration, timestamp)

    def record_agent_performance(self, agent_name, success_rate, avg_response_time):
        """Record agent performance metrics"""
        timestamp = int(time.time())

        self.client.send(f'agents.{agent_name}.success_rate', success_rate, timestamp)
        self.client.send(f'agents.{agent_name}.avg_response_time', avg_response_time, timestamp)
```

#### 4.2 Alert Configuration

**Graphite Alerts**
```python
# alerts/graphite_alerts.py
class GraphiteAlerts:
    def __init__(self, graphite_client):
        self.client = graphite_client

    def setup_queue_alerts(self):
        """Setup alerts for queue health"""
        alerts = [
            {
                'name': 'High Queue Backlog',
                'query': 'queue.pending_jobs > 50',
                'severity': 'warning',
                'message': 'Queue backlog is getting high'
            },
            {
                'name': 'Job Failure Rate',
                'query': 'queue.failed_jobs / (queue.completed_jobs + queue.failed_jobs) > 0.1',
                'severity': 'error',
                'message': 'Job failure rate is above 10%'
            },
            {
                'name': 'System CPU High',
                'query': 'cpu.usage > 90',
                'severity': 'critical',
                'message': 'System CPU usage is critically high'
            }
        ]

        for alert in alerts:
            self.client.create_alert(alert)

    def setup_agent_alerts(self):
        """Setup alerts for AI agent health"""
        alerts = [
            {
                'name': 'Agent Response Time High',
                'query': 'agents.*.avg_response_time > 30',
                'severity': 'warning',
                'message': 'AI agent response time is high'
            },
            {
                'name': 'Agent Success Rate Low',
                'query': 'agents.*.success_rate < 0.8',
                'severity': 'error',
                'message': 'AI agent success rate is below 80%'
            }
        ]

        for alert in alerts:
            self.client.create_alert(alert)
```

### Phase 5: Agentic Knowledge Graph Integration

#### 5.1 Knowledge Graph Schema

**Legislative Data Relationships**
```python
# knowledge_graph/schema.py
class LegislativeKnowledgeGraph:
    def __init__(self, api_client):
        self.client = api_client

    def create_bill_relationships(self, bill_data):
        """Create relationships between bills, sponsors, committees, etc."""
        relationships = []

        # Bill to Sponsor relationship
        if bill_data.get('sponsor_id'):
            relationships.append({
                'from': f'bill:{bill_data["bill_id"]}',
                'to': f'person:{bill_data["sponsor_id"]}',
                'type': 'SPONSORED_BY',
                'properties': {'role': 'primary_sponsor'}
            })

        # Bill to Committee relationships
        for committee in bill_data.get('committees', []):
            relationships.append({
                'from': f'bill:{bill_data["bill_id"]}',
                'to': f'committee:{committee["id"]}',
                'type': 'REFERRED_TO',
                'properties': {'date': committee.get('date_referred')}
            })

        # Create relationships in knowledge graph
        for rel in relationships:
            self.client.create_relationship(rel)

    def find_related_bills(self, bill_id, relationship_type='SIMILAR_TO'):
        """Find bills related to a given bill"""
        query = f"""
        MATCH (b1:Bill {{id: '{bill_id}'}})-[r:{relationship_type}]-(b2:Bill)
        RETURN b2.id, b2.title, r.confidence_score
        ORDER BY r.confidence_score DESC
        LIMIT 10
        """

        return self.client.execute_query(query)

    def update_error_patterns(self, error_type, context):
        """Update knowledge graph with error patterns for better troubleshooting"""
        error_node = {
            'type': 'Error',
            'error_type': error_type,
            'context': context,
            'timestamp': datetime.now().isoformat()
        }

        self.client.create_node(error_node)

        # Link to similar errors
        similar_errors = self.client.find_similar_errors(error_type)
        for similar in similar_errors:
            self.client.create_relationship({
                'from': error_node['id'],
                'to': similar['id'],
                'type': 'SIMILAR_TO',
                'properties': {'similarity_score': similar['score']}
            })
```

#### 5.2 AI Agent Knowledge Integration

**Agent Learning from Interactions**
```python
# knowledge_graph/agent_learning.py
class AgentKnowledgeLearner:
    def __init__(self, knowledge_graph):
        self.kg = knowledge_graph

    def learn_from_interaction(self, agent_name, user_input, agent_response, outcome):
        """Learn from agent-user interactions"""
        interaction_node = {
            'type': 'Interaction',
            'agent': agent_name,
            'user_input': user_input,
            'agent_response': agent_response,
            'outcome': outcome,
            'timestamp': datetime.now().isoformat()
        }

        # Store interaction
        interaction_id = self.kg.client.create_node(interaction_node)

        # Analyze patterns and update knowledge
        if outcome == 'success':
            self._reinforce_successful_pattern(agent_name, user_input, agent_response)
        else:
            self._analyze_failure_pattern(agent_name, user_input, agent_response)

    def _reinforce_successful_pattern(self, agent_name, user_input, agent_response):
        """Reinforce patterns that lead to successful interactions"""
        # Find similar successful interactions
        similar = self.kg.client.find_similar_interactions(user_input, 'success')

        # Strengthen relationships
        for interaction in similar:
            self.kg.client.strengthen_relationship(
                interaction['id'],
                interaction_id,
                relationship_type='SUCCESS_PATTERN'
            )

    def _analyze_failure_pattern(self, agent_name, user_input, agent_response):
        """Analyze patterns that lead to failures"""
        # Identify failure patterns
        failure_patterns = self.kg.client.analyze_failure_patterns(user_input)

        # Update agent knowledge to avoid similar failures
        for pattern in failure_patterns:
            self.kg.client.create_avoidance_rule(agent_name, pattern)
```

### Phase 6: Automated Ingestion Scheduling

#### 6.1 n8n Workflow for Ingestion

**Scheduled Ingestion Workflow**
```json
{
  "name": "Automated Legislative Data Ingestion",
  "nodes": [
    {
      "name": "Schedule Trigger",
      "type": "n8n-nodes-base.scheduleTrigger",
      "parameters": {
        "rule": {
          "interval": [
            {
              "field": "hours",
              "value": 6
            }
          ]
        }
      }
    },
    {
      "name": "Check Queue Status",
      "type": "n8n-nodes-base.httpRequest",
      "parameters": {
        "url": "http://localhost:8001/queue/status",
        "method": "GET"
      }
    },
    {
      "name": "Submit Ingestion Job",
      "type": "n8n-nodes-base.httpRequest",
      "parameters": {
        "url": "http://localhost:8001/jobs/submit",
        "method": "POST",
        "body": {
          "job_type": "ingestion",
          "ingestion_type": "congress",
          "parameters": {
            "start_congress": 110,
            "end_congress": 118
          },
          "enable_gpu": true,
          "enable_parallel": true
        }
      }
    },
    {
      "name": "Monitor Job Progress",
      "type": "n8n-nodes-base.httpRequest",
      "parameters": {
        "url": "http://localhost:8001/jobs/{{$node[\"Submit Ingestion Job\"].json[\"job_id\"]}}/status",
        "method": "GET"
      }
    },
    {
      "name": "Send Notification",
      "type": "n8n-nodes-base.emailSend",
      "parameters": {
        "to": "engineering@openlegislation.org",
        "subject": "Ingestion Job Completed",
        "body": "Job {{$node[\"Submit Ingestion Job\"].json[\"job_id\"]}} completed successfully"
      }
    }
  ],
  "connections": {
    "Schedule Trigger": {
      "main": [
        {
          "node": "Check Queue Status",
          "type": "main",
          "index": 0
        }
      ]
    },
    "Check Queue Status": {
      "main": [
        {
          "node": "Submit Ingestion Job",
          "type": "main",
          "index": 0
        }
      ]
    },
    "Submit Ingestion Job": {
      "main": [
        {
          "node": "Monitor Job Progress",
          "type": "main",
          "index": 0
        }
      ]
    },
    "Monitor Job Progress": {
      "main": [
        {
          "node": "Send Notification",
          "type": "main",
          "index": 0
        }
      ]
    }
  }
}
```

#### 6.2 Error Handling and Retry Logic

**Automated Error Recovery Workflow**
```json
{
  "name": "Ingestion Error Handling",
  "nodes": [
    {
      "name": "Job Failure Trigger",
      "type": "n8n-nodes-base.webhook",
      "parameters": {
        "path": "job-failed",
        "httpMethod": "POST"
      }
    },
    {
      "name": "Analyze Error",
      "type": "n8n-nodes-base.httpRequest",
      "parameters": {
        "url": "http://localhost:8002/agents/analyze-error",
        "method": "POST",
        "body": {
          "error_details": "{{$node[\"Job Failure Trigger\"].json}}"
        }
      }
    },
    {
      "name": "Determine Retry Strategy",
      "type": "n8n-nodes-base.switch",
      "parameters": {
        "conditions": [
          {
            "condition": "{{$node[\"Analyze Error\"].json[\"retry_recommended\"]}}",
            "output": "Retry"
          },
          {
            "condition": "{{!$node[\"Analyze Error\"].json[\"retry_recommended\"]}}",
            "output": "Escalate"
          }
        ]
      }
    },
    {
      "name": "Submit Retry Job",
      "type": "n8n-nodes-base.httpRequest",
      "parameters": {
        "url": "http://localhost:8001/jobs/retry",
        "method": "POST",
        "body": {
          "original_job_id": "{{$node[\"Job Failure Trigger\"].json[\"job_id\"]}}",
          "retry_strategy": "{{$node[\"Analyze Error\"].json[\"retry_strategy\"]}}"
        }
      }
    },
    {
      "name": "Send Alert",
      "type": "n8n-nodes-base.slack",
      "parameters": {
        "webhookUri": "${SLACK_WEBHOOK_URL}",
        "text": "🚨 Ingestion Job Failed: {{$node[\"Job Failure Trigger\"].json[\"job_id\"]}}"
      }
    }
  ]
}
```

### Phase 7: AI Agent Queue Monitoring

#### 7.1 QueueMonitorAgent

```python
# agents/queue_monitor_agent.py
class QueueMonitorAgent(BaseAgent):
    """AI Agent dedicated to monitoring queue operations"""

    def __init__(self, db_config, n8n_client, graphite_client):
        super().__init__('QueueMonitorAgent', 'monitoring', db_config)
        self.n8n_client = n8n_client
        self.graphite_client = graphite_client
        self.capabilities = [
            'queue_health_monitoring', 'job_failure_analysis', 'performance_optimization',
            'automated_retry_scheduling', 'resource_scaling', 'predictive_alerting'
        ]

    async def monitor_queue_health(self):
        """Continuously monitor queue health"""
        while True:
            try:
                # Get queue statistics
                queue_stats = await self.queue_manager.get_queue_stats()

                # Analyze health metrics
                health_score = self._calculate_health_score(queue_stats)

                # Send metrics to Graphite
                await self._send_metrics_to_graphite(queue_stats)

                # Check for anomalies
                anomalies = await self._detect_anomalies(queue_stats)

                if anomalies:
                    await self._handle_anomalies(anomalies)

                # Update knowledge graph with patterns
                await self._update_knowledge_graph(queue_stats)

                await asyncio.sleep(30)  # Check every 30 seconds

            except Exception as e:
                await self.think(
                    'monitoring_error',
                    f"Error in queue monitoring: {e}",
                    confidence=0.9
                )
                await asyncio.sleep(60)  # Wait longer on error

    def _calculate_health_score(self, stats):
        """Calculate overall queue health score"""
        pending_jobs = stats.get('pending', 0)
        failed_jobs = stats.get('failed', 0)
        avg_completion_time = stats.get('avg_completion_time', 0)

        # Health scoring algorithm
        health_score = 100

        # Penalize for pending jobs
        if pending_jobs > 20:
            health_score -= min(pending_jobs - 20, 30)

        # Penalize for failed jobs
        if failed_jobs > 5:
            health_score -= min(failed_jobs - 5, 25)

        # Penalize for slow completion times
        if avg_completion_time > 300:  # 5 minutes
            health_score -= min((avg_completion_time - 300) / 60, 20)

        return max(0, health_score)

    async def _detect_anomalies(self, stats):
        """Detect anomalous queue behavior"""
        anomalies = []

        # Check for sudden spikes in pending jobs
        pending_jobs = stats.get('pending', 0)
        if pending_jobs > 50:  # Threshold
            anomalies.append({
                'type': 'high_backlog',
                'severity': 'warning',
                'description': f'Queue backlog is high: {pending_jobs} pending jobs'
            })

        # Check for high failure rate
        completed = stats.get('completed', 0)
        failed = stats.get('failed', 0)
        if completed + failed > 10:  # Minimum sample size
            failure_rate = failed / (completed + failed)
            if failure_rate > 0.2:  # 20% failure rate
                anomalies.append({
                    'type': 'high_failure_rate',
                    'severity': 'error',
                    'description': f'Job failure rate is high: {failure_rate:.1%}'
                })

        return anomalies

    async def _handle_anomalies(self, anomalies):
        """Handle detected anomalies"""
        for anomaly in anomalies:
            # Log anomaly
            await self.think(
                'anomaly_detected',
                f"Detected anomaly: {anomaly['description']}",
                confidence=0.95
            )

            # Send alert via n8n
            await self.n8n_client.trigger_workflow(
                'anomaly_alert',
                {
                    'anomaly': anomaly,
                    'timestamp': datetime.now().isoformat()
                }
            )

            # Update knowledge graph
            await self._update_knowledge_graph_with_anomaly(anomaly)

    async def schedule_automatic_retry(self, failed_job_id, error_analysis):
        """Schedule automatic retry for failed jobs"""
        retry_strategy = error_analysis.get('retry_strategy', 'exponential_backoff')
        max_retries = error_analysis.get('max_retries', 3)

        # Calculate retry delay
        retry_delay = self._calculate_retry_delay(retry_strategy, max_retries)

        # Schedule retry via n8n
        await self.n8n_client.schedule_workflow(
            'job_retry',
            {
                'failed_job_id': failed_job_id,
                'retry_strategy': retry_strategy,
                'delay_seconds': retry_delay
            },
            delay_seconds=retry_delay
        )

        await self.think(
            'retry_scheduled',
            f"Scheduled retry for job {failed_job_id} with {retry_strategy} strategy",
            confidence=0.9
        )

    def _calculate_retry_delay(self, strategy, attempt_number):
        """Calculate retry delay based on strategy"""
        if strategy == 'immediate':
            return 0
        elif strategy == 'fixed':
            return 300  # 5 minutes
        elif strategy == 'exponential_backoff':
            return min(60 * (2 ** attempt_number), 3600)  # Max 1 hour
        else:
            return 300  # Default 5 minutes
```

#### 7.2 ExecutionTrackerAgent

```python
# agents/execution_tracker_agent.py
class ExecutionTrackerAgent(BaseAgent):
    """AI Agent that tracks job execution through the entire lifecycle"""

    def __init__(self, db_config, n8n_client, flowise_client):
        super().__init__('ExecutionTrackerAgent', 'execution_tracking', db_config)
        self.n8n_client = n8n_client
        self.flowise_client = flowise_client
        self.capabilities = [
            'execution_lifecycle_tracking', 'performance_analysis', 'bottleneck_identification',
            'resource_optimization', 'predictive_scaling', 'execution_pattern_analysis'
        ]

    async def track_job_execution(self, job_id):
        """Track a job through its entire execution lifecycle"""
        await self.think(
            'execution_tracking_started',
            f"Started tracking execution of job {job_id}"
        )

        # Subscribe to job events
        await self._subscribe_to_job_events(job_id)

        # Monitor execution phases
        phases = ['queued', 'running', 'processing', 'completing', 'completed']
        current_phase = 0

        while current_phase < len(phases):
            phase = phases[current_phase]

            # Monitor current phase
            phase_metrics = await self._monitor_execution_phase(job_id, phase)

            # Analyze performance
            analysis = await self._analyze_phase_performance(phase_metrics)

            # Identify bottlenecks
            if analysis.get('bottleneck_detected'):
                await self._handle_bottleneck(job_id, analysis)

            # Predict next phase timing
            prediction = await self._predict_next_phase_timing(job_id, phase)

            # Move to next phase
            current_phase += 1

            await asyncio.sleep(10)  # Check every 10 seconds

        # Final analysis
        await self._perform_final_execution_analysis(job_id)

    async def _monitor_execution_phase(self, job_id, phase):
        """Monitor metrics for a specific execution phase"""
        # Get real-time metrics from various sources
        queue_metrics = await self._get_queue_metrics(job_id)
        system_metrics = await self._get_system_metrics()
        agent_metrics = await self._get_agent_metrics()

        phase_metrics = {
            'phase': phase,
            'timestamp': datetime.now().isoformat(),
            'queue_metrics': queue_metrics,
            'system_metrics': system_metrics,
            'agent_metrics': agent_metrics
        }

        # Store metrics
        await self.db_recorder.log_telemetry_event(
            f'execution_phase_{phase}',
            phase_metrics,
            agent_name=self.name
        )

        return phase_metrics

    async def _analyze_phase_performance(self, phase_metrics):
        """Analyze performance of execution phase"""
        analysis = {
            'bottleneck_detected': False,
            'performance_score': 100,
            'recommendations': []
        }

        # Analyze CPU usage
        cpu_usage = phase_metrics['system_metrics'].get('cpu_percent', 0)
        if cpu_usage > 90:
            analysis['bottleneck_detected'] = True
            analysis['performance_score'] -= 20
            analysis['recommendations'].append('High CPU usage detected - consider scaling')

        # Analyze memory usage
        memory_usage = phase_metrics['system_metrics'].get('memory_percent', 0)
        if memory_usage > 85:
            analysis['bottleneck_detected'] = True
            analysis['performance_score'] -= 15
            analysis['recommendations'].append('High memory usage - optimize data processing')

        # Analyze queue depth
        pending_jobs = phase_metrics['queue_metrics'].get('pending', 0)
        if pending_jobs > 20:
            analysis['bottleneck_detected'] = True
            analysis['performance_score'] -= 10
            analysis['recommendations'].append('Queue backlog building - increase processing capacity')

        return analysis

    async def _handle_bottleneck(self, job_id, analysis):
        """Handle detected performance bottlenecks"""
        await self.think(
            'bottleneck_handling',
            f"Handling bottleneck for job {job_id}: {analysis['recommendations']}",
            confidence=0.9
        )

        # Trigger automated scaling via n8n
        for recommendation in analysis['recommendations']:
            if 'scaling' in recommendation.lower():
                await self.n8n_client.trigger_workflow(
                    'auto_scaling',
                    {
                        'job_id': job_id,
                        'bottleneck_type': 'cpu',
                        'current_load': analysis.get('cpu_usage', 0)
                    }
                )
            elif 'memory' in recommendation.lower():
                await self.n8n_client.trigger_workflow(
                    'memory_optimization',
                    {
                        'job_id': job_id,
                        'current_memory': analysis.get('memory_usage', 0)
                    }
                )

    async def _predict_next_phase_timing(self, job_id, current_phase):
        """Predict timing for next execution phase"""
        # Use historical data and current metrics to predict timing
        historical_data = await self._get_historical_phase_timings(current_phase)

        prediction = {
            'estimated_duration': historical_data.get('avg_duration', 60),
            'confidence': 0.8,
            'factors': ['current_system_load', 'historical_performance', 'resource_availability']
        }

        await self.think(
            'phase_timing_prediction',
            f"Predicted {current_phase} phase duration: {prediction['estimated_duration']}s",
            confidence=prediction['confidence']
        )

        return prediction

    async def _perform_final_execution_analysis(self, job_id):
        """Perform final analysis of complete job execution"""
        # Get complete execution data
        execution_data = await self._get_complete_execution_data(job_id)

        # Analyze overall performance
        analysis = {
            'total_duration': execution_data.get('total_duration', 0),
            'performance_score': 85,  # Calculated score
            'efficiency_rating': 'good',
            'bottlenecks_identified': 2,
            'optimizations_applied': 1,
            'recommendations': [
                'Consider GPU acceleration for similar jobs',
                'Optimize database queries for better performance'
            ]
        }

        # Store final analysis
        await self.db_recorder.log_telemetry_event(
            'execution_analysis_complete',
            {
                'job_id': job_id,
                'analysis': analysis
            },
            agent_name=self.name
        )

        await self.think(
            'execution_analysis_complete',
            f"Completed execution analysis for job {job_id}: {analysis['efficiency_rating']} performance",
            confidence=0.95
        )
```

### Phase 8: Testing and Benchmarking Setup

#### 8.1 Automated Testing Workflows

**n8n Testing Workflow**
```
Schedule → Run Test Suite → Analyze Results → Generate Report → Send Notifications
```

**Benchmarking Workflow**
```
Trigger → Setup Test Environment → Run Benchmarks → Collect Metrics → Analyze Results → Update Baselines
```

#### 8.2 Continuous Integration

**GitHub Actions Integration**
```yaml
# .github/workflows/automated-testing.yml
name: Automated Testing & Benchmarking

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]
  schedule:
    - cron: '0 */6 * * *'  # Every 6 hours

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.9'
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
      - name: Run tests
        run: |
          python -m pytest tests/ -v --tb=short
      - name: Run benchmarks
        run: |
          python test_queue_system.py
      - name: Upload results
        uses: actions/upload-artifact@v3
        with:
          name: test-results
          path: test-results/
```

### Phase 9: Deployment and Monitoring

#### 9.1 Production Deployment

**Docker Compose for Production**
```yaml
# docker-compose.prod.yml
version: '3.8'
services:
  openlegislation:
    build: .
    ports:
      - "8000:8000"
    environment:
      - ENVIRONMENT=production
      - DATABASE_URL=${DATABASE_URL}
    volumes:
      - app_data:/app/data
    depends_on:
      - postgres
      - redis

  postgres:
    image: postgres:15
    environment:
      - POSTGRES_DB=openlegislation
      - POSTGRES_USER=${DB_USER}
      - POSTGRES_PASSWORD=${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./database_queue_system.sql:/docker-entrypoint-initdb.d/01-queue.sql
      - ./enhanced_telemetry_audit_schema.sql:/docker-entrypoint-initdb.d/02-telemetry.sql
    ports:
      - "5432:5432"

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data

  n8n:
    image: n8nio/n8n:latest
    environment:
      - N8N_BASIC_AUTH_ACTIVE=true
      - N8N_BASIC_AUTH_USER=${N8N_USER}
      - N8N_BASIC_AUTH_PASSWORD=${N8N_PASSWORD}
    volumes:
      - n8n_data:/home/node/.n8n
    ports:
      - "5678:5678"

  flowise:
    image: flowiseai/flowise:latest
    ports:
      - "3000:3000"

  graphite:
    image: graphiteapp/graphite-web:latest
    ports:
      - "8080:8080"
    volumes:
      - graphite_data:/opt/graphite/storage

volumes:
  postgres_data:
  redis_data:
  n8n_data:
  graphite_data:
  app_data:
```

#### 9.2 Health Monitoring

**System Health Checks**
```python
# monitoring/health_checks.py
class HealthChecker:
    def __init__(self, services_config):
        self.services = services_config

    async def perform_comprehensive_health_check(self):
        """Perform health checks on all system components"""
        results = {}

        # Check database connectivity
        results['database'] = await self._check_database_health()

        # Check queue system
        results['queue'] = await self._check_queue_health()

        # Check AI agents
        results['agents'] = await self._check_agent_health()

        # Check external services
        results['external_services'] = await self._check_external_services_health()

        # Calculate overall health score
        overall_score = self._calculate_overall_health_score(results)

        # Send alerts if needed
        if overall_score < 80:
            await self._send_health_alert(results, overall_score)

        return {
            'overall_score': overall_score,
            'component_results': results,
            'timestamp': datetime.now().isoformat()
        }

    async def _check_database_health(self):
        """Check database health and performance"""
        try:
            # Test connection
            conn = await asyncpg.connect(**self.services['database'])
            await conn.close()

            # Check performance metrics
            perf_metrics = await self._get_database_performance_metrics()

            return {
                'status': 'healthy',
                'response_time_ms': perf_metrics.get('avg_query_time', 0),
                'connection_pool_usage': perf_metrics.get('pool_usage_percent', 0)
            }
        except Exception as e:
            return {
                'status': 'unhealthy',
                'error': str(e)
            }

    async def _check_queue_health(self):
        """Check queue system health"""
        try:
            queue_manager = QueueManager(self.services['database'])
            stats = await queue_manager.get_queue_stats()

            # Analyze queue health
            pending_jobs = stats.get('pending', 0)
            failed_jobs = stats.get('failed', 0)
            total_jobs = stats.get('pending', 0) + stats.get('running', 0) + stats.get('completed', 0) + stats.get('failed', 0)

            health_score = 100
            if pending_jobs > 50:
                health_score -= 20
            if failed_jobs > 10:
                health_score -= 30
            if total_jobs == 0:
                health_score = 50  # No activity might indicate issues

            return {
                'status': 'healthy' if health_score >= 70 else 'warning' if health_score >= 50 else 'critical',
                'health_score': health_score,
                'pending_jobs': pending_jobs,
                'failed_jobs': failed_jobs
            }
        except Exception as e:
            return {
                'status': 'unhealthy',
                'error': str(e)
            }

    async def _check_agent_health(self):
        """Check AI agent health"""
        agent_health = {}

        for agent_name in ['DataIngestionAgent', 'BenchmarkingAgent', 'HealthScanAgent', 'TelemetryAgent']:
            try:
                # Check agent responsiveness and last activity
                last_activity = await self._get_agent_last_activity(agent_name)
                response_time = await self._test_agent_response_time(agent_name)

                status = 'healthy'
                if response_time > 30:  # 30 seconds
                    status = 'slow'
                elif response_time > 60:
                    status = 'unhealthy'

                agent_health[agent_name] = {
                    'status': status,
                    'last_activity': last_activity,
                    'response_time_seconds': response_time
                }
            except Exception as e:
                agent_health[agent_name] = {
                    'status': 'error',
                    'error': str(e)
                }

        return agent_health

    async def _check_external_services_health(self):
        """Check health of external services (n8n, Flowise, Graphite)"""
        services_health = {}

        # Check n8n
        services_health['n8n'] = await self._check_service_health('n8n', 5678)

        # Check Flowise
        services_health['flowise'] = await self._check_service_health('flowise', 3000)

        # Check Graphite
        services_health['graphite'] = await self._check_service_health('graphite', 8080)

        return services_health

    async def _check_service_health(self, service_name, port):
        """Check health of a specific service"""
        try:
            # Simple HTTP health check
            async with aiohttp.ClientSession() as session:
                async with session.get(f'http://localhost:{port}/health', timeout=5) as response:
                    if response.status == 200:
                        return {'status': 'healthy', 'response_time_ms': 0}
                    else:
                        return {'status': 'warning', 'status_code': response.status}
        except asyncio.TimeoutError:
            return {'status': 'timeout'}
        except Exception as e:
            return {'status': 'error', 'error': str(e)}

    def _calculate_overall_health_score(self, results):
        """Calculate overall system health score"""
        scores = []

        # Database health (30% weight)
        if results['database']['status'] == 'healthy':
            scores.append(100 * 0.3)
        else:
            scores.append(0 * 0.3)

        # Queue health (25% weight)
        queue_score = results['queue'].get('health_score', 0) * 0.25
        scores.append(queue_score)

        # Agent health (25% weight)
        agent_scores = []
        for agent_name, agent_data in results['agents'].items():
            if agent_data['status'] == 'healthy':
                agent_scores.append(100)
            elif agent_data['status'] == 'slow':
                agent_scores.append(70)
            else:
                agent_scores.append(0)

        avg_agent_score = sum(agent_scores) / len(agent_scores) if agent_scores else 0
        scores.append(avg_agent_score * 0.25)

        # External services (20% weight)
        service_scores = []
        for service_name, service_data in results['external_services'].items():
            if service_data.get('status') == 'healthy':
                service_scores.append(100)
            else:
                service_scores.append(0)

        avg_service_score = sum(service_scores) / len(service_scores) if service_scores else 0
        scores.append(avg_service_score * 0.2)

        return sum(scores)

    async def _send_health_alert(self, results, overall_score):
        """Send health alert when system health is poor"""
        alert_data = {
            'severity': 'warning' if overall_score >= 50 else 'critical',
            'overall_score': overall_score,
            'component_results': results,
            'timestamp': datetime.now().isoformat()
        }

        # Send via n8n webhook
        async with aiohttp.ClientSession() as session:
            async with session.post(
                'http://localhost:5678/webhook/health-alert',
                json=alert_data
            ) as response:
                if response.status == 200:
                    logger.info("Health alert sent successfully")
                else:
                    logger.error(f"Failed to send health alert: {response.status}")
```

## 🚀 Quick Start

### 1. Start the Automation Stack

```bash
# Clone and setup
git clone https://github.com/your-org/openlegislation.git
cd openlegislation

# Start all services
docker-compose -f docker-compose.automation.yml up -d

# Run initial database setup
docker exec -it openlegislation_postgres psql -U postgres -d openlegislation -f /docker-entrypoint-initdb.d/01-queue.sql
docker exec -it openlegislation_postgres psql -U postgres -d openlegislation -f /docker-entrypoint-initdb.d/02-telemetry.sql
```

### 2. Configure n8n Workflows

1. Open n8n at http://localhost:5678
2. Import the workflow JSON files from `automation_workflows/`
3. Configure API credentials and webhook URLs
4. Test workflows manually

### 3. Set Up Flowise Agents

1. Open Flowise at http://localhost:3000
2. Create AI agent workflows using the provided templates
3. Connect to OpenLegislation API endpoints
4. Test agent interactions

### 4. Configure Graphite Monitoring

1. Open Graphite at http://localhost:8080
2. Configure dashboards for system metrics
3. Set up alerts for critical thresholds
4. Integrate with existing monitoring

### 5. Start Automated Ingestion

```bash
# Start the ingestion scheduling
python -c "
import asyncio
from automation.ingestion_scheduler import IngestionScheduler

async def main():
    scheduler = IngestionScheduler()
    await scheduler.start_automated_ingestion()

asyncio.run(main())
"
```

## 📊 Monitoring Dashboard

Access the comprehensive monitoring dashboard:

- **n8n Workflows**: http://localhost:5678
- **Flowise Agents**: http://localhost:3000
- **Graphite Metrics**: http://localhost:8080
- **OpenLegislation API**: http://localhost:8000/docs

## 🔧 API Endpoints

### Queue Management
- `GET /queue/status` - Get queue statistics
- `POST /jobs/submit` - Submit new job
- `GET /jobs/{job_id}/status` - Get job status
- `POST /jobs/{job_id}/cancel` - Cancel job

### AI Agents
- `POST /agents/{agent_name}/interact` - Interact with AI agent
- `GET /agents/health` - Get agent health status
- `GET /agents/metrics` - Get agent performance metrics

### Monitoring
- `GET /metrics/system` - System metrics
- `GET /metrics/queue` - Queue metrics
- `GET /metrics/agents` - Agent metrics

## 🎯 Key Features

✅ **Automated Ingestion Scheduling** - n8n workflows handle regular data ingestion
✅ **AI Agent Orchestration** - Flowise manages complex AI agent interactions
✅ **Real-time Monitoring** - Graphite provides comprehensive metrics and alerting
✅ **Intelligent Error Handling** - Automated retry logic and troubleshooting
✅ **Performance Benchmarking** - Continuous performance testing and optimization
✅ **Knowledge Graph Integration** - AI-powered relationship discovery and reasoning
✅ **Health Monitoring** - Automated system health checks and maintenance
✅ **Scalable Architecture** - Microservices design for horizontal scaling

This automation stack transforms OpenLegislation into a fully autonomous, self-optimizing, AI-driven data processing platform! 🚀
