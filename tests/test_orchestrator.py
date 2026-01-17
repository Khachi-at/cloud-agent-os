"""Tests for Orchestrator"""
from unittest.mock import Mock

from src.models import Plan, Task, TaskStatus
from src.orchestrator import Orchestrator


class TestOrchestratorInit:
    """Test Orchestrator initialization"""

    def test_orchestrator_initialization(self):
        """Test orchestrator is properly initialized"""
        planner = Mock()
        policy = Mock()
        scheduler = Mock()
        executor = Mock()
        auditor = Mock()

        orchestrator = Orchestrator(
            planner=planner, policy=policy, scheduler=scheduler, executor=executor, auditor=auditor
        )

        assert orchestrator.planner is planner
        assert orchestrator.policy is policy
        assert orchestrator.scheduler is scheduler
        assert orchestrator.executor is executor
        assert orchestrator.auditor is auditor


class TestOrchestratorRun:
    """Test Orchestrator run method"""

    def test_orchestrator_run_basic(self, execution_context):
        """Test basic orchestrator run"""
        # Setup mocks
        planner = Mock()
        policy = Mock()
        scheduler = Mock()
        executor = Mock()
        auditor = Mock()

        # Create tasks
        task = Task(id="task-1", name="Test", action="test")
        plan = Plan(goal="Test goal", tasks=[task])

        # Mock planner to return plan
        planner.plan.return_value = plan

        # Mock scheduler to return batch then empty
        scheduler.next_batch.side_effect = [[task], []]

        # Mock policy to allow
        policy.evaluate.return_value = {"decision": "allow"}

        orchestrator = Orchestrator(
            planner=planner, policy=policy, scheduler=scheduler, executor=executor, auditor=auditor
        )

        result = orchestrator.run("Test goal", execution_context)

        # Verify planner was called
        planner.plan.assert_called_once_with("Test goal", execution_context)

        # Verify plan was recorded
        auditor.record.assert_any_call({"event": "plan_created", "plan": plan.goal})

        # Verify result is returned
        assert result == plan

    def test_orchestrator_run_multiple_batches(self, execution_context):
        """Test orchestrator with multiple batches"""
        planner = Mock()
        policy = Mock()
        scheduler = Mock()
        executor = Mock()
        auditor = Mock()

        # Create tasks
        task1 = Task(id="task-1", name="Build", action="build")
        task2 = Task(id="task-2", name="Test", action="test", depends=["task-1"])
        plan = Plan(goal="Build and test", tasks=[task1, task2])

        planner.plan.return_value = plan
        scheduler.next_batch.side_effect = [[task1], [task2], []]
        policy.evaluate.return_value = {"decision": "allow"}

        orchestrator = Orchestrator(
            planner=planner, policy=policy, scheduler=scheduler, executor=executor, auditor=auditor
        )

        result = orchestrator.run("Build and test", execution_context)

        # Verify both tasks were executed
        assert executor.execute.call_count == 2
        assert result == plan

    def test_orchestrator_run_policy_denied(self, execution_context):
        """Test orchestrator when policy denies task"""
        planner = Mock()
        policy = Mock()
        scheduler = Mock()
        executor = Mock()
        auditor = Mock()

        task = Task(id="task-1", name="Dangerous", action="dangerous")
        plan = Plan(goal="Dangerous goal", tasks=[task])

        planner.plan.return_value = plan
        scheduler.next_batch.side_effect = [[task], []]
        policy.evaluate.return_value = {"decision": "deny", "reason": "Not allowed"}

        orchestrator = Orchestrator(
            planner=planner, policy=policy, scheduler=scheduler, executor=executor, auditor=auditor
        )

        result = orchestrator.run("Dangerous goal", execution_context)

        # Verify task was denied
        assert task.status == TaskStatus.FAILED
        assert task.error == "Policy denied"
        assert result.status == "planned"

        # Verify executor was not called
        executor.execute.assert_not_called()

    def test_orchestrator_run_execution_failure(self, execution_context):
        """Test orchestrator when task execution fails"""
        planner = Mock()
        policy = Mock()
        scheduler = Mock()
        executor = Mock()
        auditor = Mock()

        task = Task(id="task-1", name="Failing", action="failing")
        plan = Plan(goal="Failing goal", tasks=[task])

        planner.plan.return_value = plan
        scheduler.next_batch.side_effect = [[task], []]
        policy.evaluate.return_value = {"decision": "allow"}
        executor.execute.side_effect = Exception("Execution error")

        orchestrator = Orchestrator(
            planner=planner, policy=policy, scheduler=scheduler, executor=executor, auditor=auditor
        )

        result = orchestrator.run("Failing goal", execution_context)

        # Verify task failed
        assert task.status == TaskStatus.FAILED
        assert "Execution error" in task.error
        assert result.status == "planned"

    def test_orchestrator_audit_trail(self, execution_context):
        """Test that orchestrator maintains audit trail"""
        planner = Mock()
        policy = Mock()
        scheduler = Mock()
        executor = Mock()
        auditor = Mock()

        task = Task(id="task-1", name="Audited", action="audited")
        plan = Plan(goal="Audit test", tasks=[task])

        planner.plan.return_value = plan
        scheduler.next_batch.side_effect = [[task], []]
        policy.evaluate.return_value = {"decision": "allow"}

        orchestrator = Orchestrator(
            planner=planner, policy=policy, scheduler=scheduler, executor=executor, auditor=auditor
        )

        orchestrator.run("Audit test", execution_context)

        # Verify audit records were created
        assert auditor.record.call_count >= 2
        # First call should be plan creation
        auditor.record.assert_any_call({"event": "plan_created", "plan": plan.goal})


class TestOrchestratorPrivateMethods:
    """Test Orchestrator private methods"""

    def test_run_task_success(self, execution_context):
        """Test successful task execution"""
        planner = Mock()
        policy = Mock()
        scheduler = Mock()
        executor = Mock()
        auditor = Mock()

        policy.evaluate.return_value = {"decision": "allow"}

        orchestrator = Orchestrator(
            planner=planner, policy=policy, scheduler=scheduler, executor=executor, auditor=auditor
        )

        task = Task(id="task-1", name="Test", action="test")

        orchestrator._run_task(task, execution_context)

        # Verify task succeeded
        assert task.status == TaskStatus.SUCCESS
        executor.execute.assert_called_once()

    def test_run_task_policy_denied(self, execution_context):
        """Test task execution when policy denies"""
        planner = Mock()
        policy = Mock()
        scheduler = Mock()
        executor = Mock()
        auditor = Mock()

        policy.evaluate.return_value = {"decision": "deny"}

        orchestrator = Orchestrator(
            planner=planner, policy=policy, scheduler=scheduler, executor=executor, auditor=auditor
        )

        task = Task(id="task-1", name="Denied", action="denied")

        orchestrator._run_task(task, execution_context)

        # Verify task failed due to policy
        assert task.status == TaskStatus.FAILED
        assert task.error == "Policy denied"
        executor.execute.assert_not_called()

    def test_run_task_execution_error(self, execution_context):
        """Test task execution error handling"""
        planner = Mock()
        policy = Mock()
        scheduler = Mock()
        executor = Mock()
        auditor = Mock()

        policy.evaluate.return_value = {"decision": "allow"}
        executor.execute.side_effect = RuntimeError("Task failed")

        orchestrator = Orchestrator(
            planner=planner, policy=policy, scheduler=scheduler, executor=executor, auditor=auditor
        )

        task = Task(id="task-1", name="Error", action="error")

        orchestrator._run_task(task, execution_context)

        # Verify task failed
        assert task.status == TaskStatus.FAILED
        assert "Task failed" in task.error
