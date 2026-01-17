"""Integration tests for Cloud Agent OS"""
from unittest.mock import Mock

from src.models import Plan, Task, TaskStatus
from src.orchestrator import Orchestrator


class TestIntegration:
    """Integration tests"""

    def test_full_workflow(self, execution_context):
        """Test a complete workflow from plan to execution"""
        # Setup all components
        planner = Mock()
        policy = Mock()
        scheduler = Mock()
        executor = Mock()
        auditor = Mock()

        # Create a realistic workflow
        task1 = Task(id="t1", name="Checkout", action="checkout", params={"repo": "myrepo"})
        task2 = Task(
            id="t2", name="Build", action="build", params={"target": "all"}, depends=["t1"]
        )
        task3 = Task(id="t3", name="Test", action="test", depends=["t2"])
        task4 = Task(id="t4", name="Deploy", action="deploy", depends=["t2", "t3"])

        plan = Plan(goal="CI/CD Pipeline", tasks=[task1, task2, task3, task4])

        # Configure mocks
        planner.plan.return_value = plan
        scheduler.next_batch.side_effect = [
            [task1],  # Batch 1: Checkout
            [task2],  # Batch 2: Build
            [task3],  # Batch 3: Test
            [task4],  # Batch 4: Deploy
            [],  # End
        ]
        policy.evaluate.return_value = {"decision": "allow"}

        # Create orchestrator
        orchestrator = Orchestrator(
            planner=planner, policy=policy, scheduler=scheduler, executor=executor, auditor=auditor
        )

        # Run workflow
        result = orchestrator.run("CI/CD Pipeline", execution_context)

        # Verify workflow completed
        assert result.goal == "CI/CD Pipeline"
        assert executor.execute.call_count == 4
        assert all(task.status == TaskStatus.SUCCESS for task in [task1, task2, task3, task4])

    def test_workflow_with_policy_failure(self, execution_context):
        """Test workflow that fails policy check"""
        planner = Mock()
        policy = Mock()
        scheduler = Mock()
        executor = Mock()
        auditor = Mock()

        task1 = Task(id="t1", name="Safe", action="safe")
        task2 = Task(id="t2", name="Dangerous", action="dangerous", depends=["t1"])

        plan = Plan(goal="Mixed workflow", tasks=[task1, task2])

        planner.plan.return_value = plan
        scheduler.next_batch.side_effect = [[task1], [task2], []]

        # First task allowed, second denied
        policy.evaluate.side_effect = [
            {"decision": "allow"},
            {"decision": "deny", "reason": "Dangerous operation"},
        ]

        orchestrator = Orchestrator(
            planner=planner, policy=policy, scheduler=scheduler, executor=executor, auditor=auditor
        )

        orchestrator.run("Mixed workflow", execution_context)

        # Verify first task succeeded
        assert task1.status == TaskStatus.SUCCESS

        # Verify second task failed
        assert task2.status == TaskStatus.FAILED
        assert task2.error == "Policy denied"

    def test_workflow_with_partial_failure(self, execution_context):
        """Test workflow with task execution failure"""
        planner = Mock()
        policy = Mock()
        scheduler = Mock()
        executor = Mock()
        auditor = Mock()

        task1 = Task(id="t1", name="Task1", action="action1")
        task2 = Task(id="t2", name="Task2", action="action2", depends=["t1"])
        task3 = Task(id="t3", name="Task3", action="action3", depends=["t1"])

        plan = Plan(goal="Partial failure", tasks=[task1, task2, task3])

        planner.plan.return_value = plan
        scheduler.next_batch.side_effect = [[task1], [task2, task3], []]
        policy.evaluate.return_value = {"decision": "allow"}

        # Task 2 fails, task 3 succeeds
        executor.execute.side_effect = [None, Exception("Task2 failed"), None]

        orchestrator = Orchestrator(
            planner=planner, policy=policy, scheduler=scheduler, executor=executor, auditor=auditor
        )

        orchestrator.run("Partial failure", execution_context)

        # Verify statuses
        assert task1.status == TaskStatus.SUCCESS
        assert task2.status == TaskStatus.FAILED
        assert task3.status == TaskStatus.SUCCESS
