"""
Tests for automation components.

This module tests the automation functionality including:
- Ingestion scheduler
- Queue monitor agent
- Automated workflows
- Scheduling and triggering
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock, AsyncMock
from tests.utils.test_helpers import assert_no_exceptions


class TestIngestionScheduler:
    """Test ingestion scheduler functionality."""

    @pytest.fixture
    def ingestion_scheduler(self):
        """Create an IngestionScheduler instance for testing."""
        from automation.ingestion_scheduler import IngestionScheduler
        return IngestionScheduler()

    @pytest.mark.unit
    def test_scheduler_initialization(self, ingestion_scheduler):
        """Test ingestion scheduler initialization."""
        assert ingestion_scheduler is not None
        assert hasattr(ingestion_scheduler, 'scheduled_jobs')
        assert hasattr(ingestion_scheduler, 'active_schedules')

    @pytest.mark.unit
    def test_schedule_creation(self, ingestion_scheduler):
        """Test creating ingestion schedules."""
        schedule_config = {
            "name": "daily_bill_ingestion",
            "schedule_type": "daily",
            "time": "02:00",
            "jurisdiction": "federal",
            "data_types": ["bills", "members"]
        }

        schedule_id = ingestion_scheduler.create_schedule(schedule_config)

        assert schedule_id is not None
        assert schedule_id in ingestion_scheduler.scheduled_jobs

    @pytest.mark.unit
    def test_cron_schedule_parsing(self, ingestion_scheduler):
        """Test cron schedule parsing."""
        cron_expression = "0 2 * * *"  # Daily at 2 AM

        next_run = ingestion_scheduler.parse_cron_schedule(cron_expression)

        assert next_run is not None
        assert isinstance(next_run, datetime)

    @pytest.mark.asyncio
    async def test_schedule_execution(self, ingestion_scheduler):
        """Test schedule execution."""
        schedule_config = {
            "name": "test_schedule",
            "schedule_type": "immediate",
            "jurisdiction": "federal",
            "data_types": ["bills"]
        }

        schedule_id = ingestion_scheduler.create_schedule(schedule_config)

        # Mock the execution
        with patch.object(ingestion_scheduler, 'execute_ingestion_job', return_value=True):
            result = await ingestion_scheduler.execute_schedule(schedule_id)

            assert result is True

    @pytest.mark.unit
    def test_schedule_status_monitoring(self, ingestion_scheduler):
        """Test schedule status monitoring."""
        # Create a test schedule
        schedule_id = ingestion_scheduler.create_schedule({
            "name": "test_schedule",
            "schedule_type": "daily"
        })

        status = ingestion_scheduler.get_schedule_status(schedule_id)

        assert status is not None
        assert "status" in status
        assert "next_run" in status

    @pytest.mark.unit
    def test_schedule_cancellation(self, ingestion_scheduler):
        """Test schedule cancellation."""
        schedule_id = ingestion_scheduler.create_schedule({
            "name": "test_schedule",
            "schedule_type": "daily"
        })

        result = ingestion_scheduler.cancel_schedule(schedule_id)

        assert result is True
        assert schedule_id not in ingestion_scheduler.active_schedules


class TestQueueMonitorAgent:
    """Test queue monitor agent functionality."""

    @pytest.fixture
    def queue_monitor_agent(self):
        """Create a QueueMonitorAgent instance for testing."""
        from agents.queue_monitor_agent import QueueMonitorAgent
        return QueueMonitorAgent()

    @pytest.mark.unit
    def test_agent_initialization(self, queue_monitor_agent):
        """Test queue monitor agent initialization."""
        assert queue_monitor_agent is not None
        assert hasattr(queue_monitor_agent, 'name')
        assert hasattr(queue_monitor_agent, 'role')

    @pytest.mark.unit
    def test_queue_status_checking(self, queue_monitor_agent):
        """Test queue status checking."""
        # Mock queue manager
        mock_queue_manager = Mock()
        mock_queue_manager.get_queue_status.return_value = {
            "total_jobs": 10,
            "queued": 3,
            "running": 2,
            "completed": 4,
            "failed": 1
        }

        with patch('agents.queue_monitor_agent.QueueManager', return_value=mock_queue_manager):
            status = queue_monitor_agent.check_queue_status()

            assert status["total_jobs"] == 10
            assert status["queued"] == 3

    @pytest.mark.unit
    def test_performance_monitoring(self, queue_monitor_agent):
        """Test performance monitoring."""
        metrics = queue_monitor_agent.monitor_performance()

        assert isinstance(metrics, dict)
        assert "cpu_usage" in metrics or "memory_usage" in metrics

    @pytest.mark.unit
    def test_alert_generation(self, queue_monitor_agent):
        """Test alert generation for queue issues."""
        # Mock problematic queue status
        mock_queue_status = {
            "failed": 5,
            "queued": 50,
            "total_jobs": 55
        }

        alerts = queue_monitor_agent.generate_alerts(mock_queue_status)

        assert isinstance(alerts, list)
        assert len(alerts) > 0  # Should generate alerts for high failure rate

    @pytest.mark.unit
    def test_queue_optimization_suggestions(self, queue_monitor_agent):
        """Test queue optimization suggestions."""
        queue_metrics = {
            "average_wait_time": 300,  # 5 minutes
            "throughput": 10,  # jobs per minute
            "error_rate": 0.15  # 15%
        }

        suggestions = queue_monitor_agent.optimize_queue(queue_metrics)

        assert isinstance(suggestions, list)
        assert len(suggestions) > 0


class TestAutomatedWorkflows:
    """Test automated workflow functionality."""

    @pytest.fixture
    def automated_workflow(self):
        """Create an automated workflow instance for testing."""
        # This would be a hypothetical automated workflow class
        # For now, we'll create a mock implementation
        class MockAutomatedWorkflow:
            def __init__(self):
                self.workflows = {}

            def create_workflow(self, config):
                workflow_id = f"workflow_{len(self.workflows) + 1}"
                self.workflows[workflow_id] = config
                return workflow_id

            def execute_workflow(self, workflow_id):
                return {"status": "executed", "workflow_id": workflow_id}

        return MockAutomatedWorkflow()

    @pytest.mark.unit
    def test_workflow_creation(self, automated_workflow):
        """Test automated workflow creation."""
        workflow_config = {
            "name": "bill_ingestion_workflow",
            "steps": [
                {"type": "crawl", "target": "congress.gov"},
                {"type": "process", "data_type": "bills"},
                {"type": "ingest", "table": "bills"}
            ],
            "triggers": ["schedule", "api_call"]
        }

        workflow_id = automated_workflow.create_workflow(workflow_config)

        assert workflow_id is not None
        assert workflow_id in automated_workflow.workflows

    @pytest.mark.unit
    def test_workflow_execution(self, automated_workflow):
        """Test workflow execution."""
        workflow_id = automated_workflow.create_workflow({
            "name": "test_workflow",
            "steps": [{"type": "test"}]
        })

        result = automated_workflow.execute_workflow(workflow_id)

        assert result["status"] == "executed"
        assert result["workflow_id"] == workflow_id

    @pytest.mark.unit
    def test_workflow_error_handling(self, automated_workflow):
        """Test workflow error handling."""
        # Create workflow that might fail
        workflow_id = automated_workflow.create_workflow({
            "name": "failing_workflow",
            "steps": [{"type": "failing_step"}]
        })

        # Should handle errors gracefully
        assert_no_exceptions(automated_workflow.execute_workflow, workflow_id)


class TestSchedulingSystem:
    """Test scheduling system functionality."""

    @pytest.fixture
    def scheduling_system(self):
        """Create a scheduling system instance for testing."""
        class MockSchedulingSystem:
            def __init__(self):
                self.schedules = {}

            def add_schedule(self, name, cron_expression, job_func):
                schedule_id = f"schedule_{len(self.schedules) + 1}"
                self.schedules[schedule_id] = {
                    "name": name,
                    "cron": cron_expression,
                    "job": job_func,
                    "active": True
                }
                return schedule_id

            def remove_schedule(self, schedule_id):
                if schedule_id in self.schedules:
                    self.schedules[schedule_id]["active"] = False
                    return True
                return False

            def list_schedules(self):
                return list(self.schedules.values())

        return MockSchedulingSystem()

    @pytest.mark.unit
    def test_schedule_addition(self, scheduling_system):
        """Test adding schedules."""
        def test_job():
            return "executed"

        schedule_id = scheduling_system.add_schedule(
            "daily_backup",
            "0 2 * * *",
            test_job
        )

        assert schedule_id is not None
        assert schedule_id in scheduling_system.schedules

    @pytest.mark.unit
    def test_schedule_removal(self, scheduling_system):
        """Test removing schedules."""
        def test_job():
            return "executed"

        schedule_id = scheduling_system.add_schedule("test", "0 2 * * *", test_job)
        result = scheduling_system.remove_schedule(schedule_id)

        assert result is True
        assert not scheduling_system.schedules[schedule_id]["active"]

    @pytest.mark.unit
    def test_schedule_listing(self, scheduling_system):
        """Test listing schedules."""
        def job1():
            pass

        def job2():
            pass

        scheduling_system.add_schedule("schedule1", "0 2 * * *", job1)
        scheduling_system.add_schedule("schedule2", "0 3 * * *", job2)

        schedules = scheduling_system.list_schedules()

        assert len(schedules) == 2
        assert all(schedule["active"] for schedule in schedules)


class TestTriggerSystem:
    """Test trigger system functionality."""

    @pytest.fixture
    def trigger_system(self):
        """Create a trigger system instance for testing."""
        class MockTriggerSystem:
            def __init__(self):
                self.triggers = {}

            def add_trigger(self, name, condition, action):
                trigger_id = f"trigger_{len(self.triggers) + 1}"
                self.triggers[trigger_id] = {
                    "name": name,
                    "condition": condition,
                    "action": action,
                    "active": True
                }
                return trigger_id

            def check_triggers(self, event_data):
                activated = []
                for trigger_id, trigger in self.triggers.items():
                    if trigger["active"] and trigger["condition"](event_data):
                        activated.append(trigger_id)
                        trigger["action"]()
                return activated

        return MockTriggerSystem()

    @pytest.mark.unit
    def test_trigger_creation(self, trigger_system):
        """Test trigger creation."""
        def condition_func(data):
            return data.get("error_count", 0) > 5

        def action_func():
            print("Alert triggered!")

        trigger_id = trigger_system.add_trigger(
            "error_alert",
            condition_func,
            action_func
        )

        assert trigger_id is not None
        assert trigger_id in trigger_system.triggers

    @pytest.mark.unit
    def test_trigger_activation(self, trigger_system):
        """Test trigger activation."""
        triggered = False

        def condition_func(data):
            return data.get("status") == "error"

        def action_func():
            nonlocal triggered
            triggered = True

        trigger_system.add_trigger("error_trigger", condition_func, action_func)

        # Test with non-triggering data
        activated = trigger_system.check_triggers({"status": "success"})
        assert len(activated) == 0
        assert not triggered

        # Test with triggering data
        activated = trigger_system.check_triggers({"status": "error"})
        assert len(activated) == 1
        assert triggered


class TestIntegrationTests:
    """Integration tests for automation components."""

    @pytest.mark.integration
    async def test_scheduler_and_queue_integration(self):
        """Test integration between scheduler and queue system."""
        from automation.ingestion_scheduler import IngestionScheduler
        from agents.queue_monitor_agent import QueueMonitorAgent

        scheduler = IngestionScheduler()
        monitor = QueueMonitorAgent()

        # Create a scheduled job
        schedule_config = {
            "name": "integration_test",
            "schedule_type": "immediate",
            "jurisdiction": "federal",
            "data_types": ["bills"]
        }

        schedule_id = scheduler.create_schedule(schedule_config)

        # Check queue status
        status = monitor.check_queue_status()

        assert schedule_id is not None
        assert isinstance(status, dict)

    @pytest.mark.integration
    def test_full_automation_workflow(self):
        """Test full automation workflow."""
        # This would test the complete automation pipeline
        # For now, we'll test component interactions

        from automation.ingestion_scheduler import IngestionScheduler
        from agents.queue_monitor_agent import QueueMonitorAgent

        scheduler = IngestionScheduler()
        monitor = QueueMonitorAgent()

        # Create multiple schedules
        schedules = []
        for i in range(3):
            schedule_config = {
                "name": f"test_schedule_{i}",
                "schedule_type": "daily",
                "jurisdiction": "federal",
                "data_types": ["bills"]
            }
            schedule_id = scheduler.create_schedule(schedule_config)
            schedules.append(schedule_id)

        # Verify all schedules were created
        assert len(schedules) == 3
        assert all(sid in scheduler.scheduled_jobs for sid in schedules)

        # Check monitoring
        status = monitor.check_queue_status()
        assert isinstance(status, dict)