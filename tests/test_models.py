"""Tests for data models"""
import sys
from pathlib import Path

from core.models import Plan, Task, TaskStatus

sys.path.insert(0, str(Path(__file__).parent.parent))


class TestTaskStatus:
    """Test TaskStatus enum"""

    def test_task_status_values(self):
        """Test that TaskStatus has expected values"""
        assert TaskStatus.PENDING.value == "pending"
        assert TaskStatus.RUNNING.value == "running"
        assert TaskStatus.SUCCESS.value == "success"
        assert TaskStatus.FAILED.value == "failed"
        assert TaskStatus.ROLLED_BACK.value == "rolled_back"

    def test_task_status_is_string_enum(self):
        """Test that TaskStatus is a string enum"""
        assert isinstance(TaskStatus.PENDING, str)
        assert TaskStatus.PENDING == "pending"


class TestTask:
    """Test Task model"""

    def test_task_creation(self):
        """Test basic task creation"""
        task = Task(
            id="task-1",
            name="Deploy App",
            action="deploy",
            params={"app": "myapp", "version": "1.0"},
        )

        assert task.id == "task-1"
        assert task.name == "Deploy App"
        assert task.action == "deploy"
        assert task.params == {"app": "myapp", "version": "1.0"}
        assert task.status == TaskStatus.PENDING
        assert task.result is None
        assert task.error is None

    def test_task_with_dependencies(self):
        """Test task creation with dependencies"""
        task = Task(id="task-2", name="Test App", action="test", depends=["task-1"])

        assert task.depends == ["task-1"]

    def test_task_with_multiple_dependencies(self):
        """Test task with multiple dependencies"""
        task = Task(id="task-3", name="Deploy", action="deploy", depends=["task-1", "task-2"])

        assert len(task.depends) == 2
        assert "task-1" in task.depends
        assert "task-2" in task.depends

    def test_task_status_transitions(self):
        """Test task status transitions"""
        task = Task(id="task-1", name="Test", action="test")

        # Initial state
        assert task.status == TaskStatus.PENDING

        # Transition to running
        task.status = TaskStatus.RUNNING
        assert task.status == TaskStatus.RUNNING

        # Transition to success
        task.status = TaskStatus.SUCCESS
        assert task.status == TaskStatus.SUCCESS

    def test_task_with_result(self):
        """Test task with result"""
        task = Task(
            id="task-1",
            name="Fetch Data",
            action="fetch",
            status=TaskStatus.SUCCESS,
            result={"data": [1, 2, 3]},
        )

        assert task.result == {"data": [1, 2, 3]}

    def test_task_with_error(self):
        """Test task with error"""
        task = Task(
            id="task-1",
            name="Deploy",
            action="deploy",
            status=TaskStatus.FAILED,
            error="Connection timeout",
        )

        assert task.error == "Connection timeout"

    def test_task_empty_params(self):
        """Test task creation with empty params"""
        task = Task(id="task-1", name="Simple", action="simple")
        assert task.params == {}

    def test_task_empty_depends(self):
        """Test task creation with empty depends"""
        task = Task(id="task-1", name="Independent", action="independent")
        assert task.depends == []


class TestPlan:
    """Test Plan model"""

    def test_plan_creation(self):
        """Test basic plan creation"""
        task1 = Task(id="task-1", name="Build", action="build")
        task2 = Task(id="task-2", name="Test", action="test", depends=["task-1"])

        plan = Plan(goal="Deploy application", tasks=[task1, task2])

        assert plan.goal == "Deploy application"
        assert len(plan.tasks) == 2
        assert plan.status == "planned"

    def test_plan_with_single_task(self):
        """Test plan with single task"""
        task = Task(id="task-1", name="Simple", action="simple")
        plan = Plan(goal="Simple goal", tasks=[task])

        assert len(plan.tasks) == 1
        assert plan.tasks[0].id == "task-1"

    def test_plan_with_empty_tasks(self):
        """Test plan with empty task list"""
        plan = Plan(goal="Empty goal", tasks=[])
        assert plan.tasks == []
        assert len(plan.tasks) == 0

    def test_plan_status_update(self):
        """Test plan status updates"""
        plan = Plan(goal="Test goal", tasks=[])
        assert plan.status == "planned"

        plan.status = "executing"
        assert plan.status == "executing"

        plan.status = "completed"
        assert plan.status == "completed"

    def test_plan_with_complex_dependency_graph(self):
        """Test plan with complex dependency graph"""
        task1 = Task(id="task-1", name="Prepare", action="prepare")
        task2 = Task(id="task-2", name="Build", action="build", depends=["task-1"])
        task3 = Task(id="task-3", name="Test", action="test", depends=["task-2"])
        task4 = Task(id="task-4", name="Deploy", action="deploy", depends=["task-2", "task-3"])

        plan = Plan(goal="Full pipeline", tasks=[task1, task2, task3, task4])

        assert len(plan.tasks) == 4
        assert plan.tasks[3].depends == ["task-2", "task-3"]
