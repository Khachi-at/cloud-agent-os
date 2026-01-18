"""Tests for Executor implementations"""
from unittest.mock import Mock

from core.executors.executor import SimpleExecutor
from core.models import Task, TaskStatus


class TestSimpleExecutorInit:
    """Test SimpleExecutor initialization"""

    def test_simple_executor_init(self):
        """Test SimpleExecutor initializes correctly"""
        executor = SimpleExecutor()
        assert executor is not None


class TestSimpleExecutorRegister:
    """Test handler registration"""

    def test_register_action_handler(self):
        """Test registering a handler for an action"""
        executor = SimpleExecutor()
        handler = Mock()

        executor.register("create_instance", handler)

        # Verify handler is registered (internal state)
        assert "create_instance" in executor._handlers

    def test_register_action_with_rollback(self):
        """Test registering both handler and rollback"""
        executor = SimpleExecutor()
        handler = Mock()
        rollback_handler = Mock()

        executor.register("create_instance", handler, rollback_handler)

        assert "create_instance" in executor._handlers
        assert "create_instance" in executor._rollback_handlers

    def test_register_multiple_handlers(self):
        """Test registering multiple handlers"""
        executor = SimpleExecutor()
        handler1 = Mock()
        handler2 = Mock()

        executor.register("action1", handler1)
        executor.register("action2", handler2)

        assert "action1" in executor._handlers
        assert "action2" in executor._handlers


class TestSimpleExecutorExecute:
    """Test task execution"""

    def test_execute_with_registered_handler(self, execution_context):
        """Test executing a task with a registered handler"""
        executor = SimpleExecutor()
        handler = Mock(return_value={"instance_id": "i-123"})

        executor.register("create_instance", handler)

        task = Task(
            id="t1",
            name="Create",
            action="create_instance",
            params={"instance_type": "t2.micro"},
        )

        executor.execute(task, execution_context)

        # Verify handler was called with params, context, and control_plane
        handler.assert_called_once()
        call_args = handler.call_args
        assert call_args[0][0] == {"instance_type": "t2.micro"}
        assert call_args[0][1] == execution_context
        assert call_args[0][2] is None  # control_plane was None

        # Verify task was updated
        assert task.status == TaskStatus.SUCCESS
        assert task.result == {"instance_id": "i-123"}

    def test_execute_with_unregistered_handler(self, execution_context):
        """Test executing a task with no registered handler"""
        executor = SimpleExecutor()

        task = Task(id="t1", name="Unknown", action="unknown_action", params={})

        executor.execute(task, execution_context)

        # Verify task failed
        assert task.status == TaskStatus.FAILED
        assert "No handler" in task.error

    def test_execute_with_handler_exception(self, execution_context):
        """Test executing when handler raises exception"""
        executor = SimpleExecutor()
        handler = Mock(side_effect=RuntimeError("Handler failed"))

        executor.register("failing_action", handler)

        task = Task(id="t1", name="Fail", action="failing_action", params={})

        executor.execute(task, execution_context)

        # Verify task failed with error
        assert task.status == TaskStatus.FAILED
        assert "Handler failed" in task.error

    def test_execute_updates_task_status(self, execution_context):
        """Test that execute properly updates task status"""
        executor = SimpleExecutor()
        handler = Mock(return_value={"result": "ok"})

        executor.register("action", handler)

        task = Task(id="t1", name="Test", action="action", params={})

        # Task starts as PENDING
        assert task.status == TaskStatus.PENDING

        executor.execute(task, execution_context)

        # Task should be SUCCESS
        assert task.status == TaskStatus.SUCCESS

    def test_execute_with_context(self, execution_context):
        """Test that execution context is passed to handler"""
        executor = SimpleExecutor()
        handler = Mock(return_value={})

        executor.register("action", handler)

        task = Task(id="t1", name="Test", action="action", params={})

        executor.execute(task, execution_context)

        # Verify context was passed
        call_args = handler.call_args
        assert call_args[0][1] == execution_context


class TestSimpleExecutorRollback:
    """Test task rollback"""

    def test_rollback_with_registered_rollback_handler(self, execution_context):
        """Test rollback with a registered handler"""
        executor = SimpleExecutor()
        rollback_handler = Mock()

        executor.register("create_instance", Mock(), rollback_handler)

        task = Task(
            id="t1",
            name="Create",
            action="create_instance",
            params={"instance_id": "i-123"},
            result={"instance_id": "i-123"},
        )

        executor.rollback(task, execution_context)

        # Verify rollback handler was called
        rollback_handler.assert_called_once()
        assert task.status == TaskStatus.ROLLED_BACK

    def test_rollback_without_rollback_handler(self, execution_context):
        """Test rollback when no rollback handler is registered"""
        executor = SimpleExecutor()
        executor.register("action", Mock())  # No rollback handler

        task = Task(id="t1", name="Test", action="action", params={})

        executor.rollback(task, execution_context)

        # Should not raise, just do nothing
        assert task.status != TaskStatus.ROLLED_BACK

    def test_rollback_with_unknown_action(self, execution_context):
        """Test rollback for unknown action"""
        executor = SimpleExecutor()

        task = Task(id="t1", name="Unknown", action="unknown", params={})

        executor.rollback(task, execution_context)

        # Should not raise
        assert task.status != TaskStatus.ROLLED_BACK

    def test_rollback_handler_exception(self, execution_context):
        """Test rollback when handler raises exception"""
        executor = SimpleExecutor()
        rollback_handler = Mock(side_effect=RuntimeError("Rollback failed"))

        executor.register("action", Mock(), rollback_handler)

        task = Task(id="t1", name="Test", action="action", params={})

        executor.rollback(task, execution_context)

        # Verify error is captured
        assert "Rollback failed" in task.error


class TestSimpleExecutorWithControlPlane:
    """Test SimpleExecutor with control plane parameter"""

    def test_execute_with_control_plane(self, execution_context):
        """Test that execute accepts control_plane parameter"""
        executor = SimpleExecutor()
        handler = Mock(return_value={"result": "ok"})
        executor.register("action", handler)

        control_plane = Mock()

        task = Task(id="t1", name="Test", action="action", params={})

        # Should not raise with control_plane parameter
        executor.execute(task, execution_context, control_plane)

        assert task.status == TaskStatus.SUCCESS

    def test_rollback_with_control_plane(self, execution_context):
        """Test that rollback accepts control_plane parameter"""
        executor = SimpleExecutor()
        rollback_handler = Mock()
        executor.register("action", Mock(), rollback_handler)

        control_plane = Mock()

        task = Task(id="t1", name="Test", action="action", params={})

        # Should not raise with control_plane parameter
        executor.rollback(task, execution_context, control_plane)

        assert task.status == TaskStatus.ROLLED_BACK


class TestSimpleExecutorUnregister:
    """Test handler unregistration"""

    def test_unregister_action_handler(self, execution_context):
        """Test unregistering a handler"""
        executor = SimpleExecutor()
        handler = Mock(return_value={"result": "ok"})

        executor.register("action", handler)
        assert "action" in executor._handlers

        executor.unregister("action")

        assert "action" not in executor._handlers

    def test_unregister_nonexistent_handler(self):
        """Test unregistering non-existent handler"""
        executor = SimpleExecutor()

        # Should not raise
        executor.unregister("nonexistent")

    def test_unregister_clears_rollback_handler(self):
        """Test that unregister also clears rollback handler"""
        executor = SimpleExecutor()
        handler = Mock()
        rollback_handler = Mock()

        executor.register("action", handler, rollback_handler)

        executor.unregister("action")

        assert "action" not in executor._handlers
        assert "action" not in executor._rollback_handlers

    def test_unregister_then_execute_fails(self, execution_context):
        """Test that execution fails after handler is unregistered"""
        executor = SimpleExecutor()
        handler = Mock(return_value={"result": "ok"})

        executor.register("action", handler)
        executor.unregister("action")

        task = Task(id="t1", name="Test", action="action", params={})

        executor.execute(task, execution_context)

        assert task.status == TaskStatus.FAILED


class TestSimpleExecutorExists:
    """Test handler existence checks"""

    def test_has_handler_returns_true(self):
        """Test checking if handler exists"""
        executor = SimpleExecutor()
        handler = Mock()

        executor.register("action", handler)

        assert executor.has_handler("action") is True

    def test_has_handler_returns_false(self):
        """Test checking for non-existent handler"""
        executor = SimpleExecutor()

        assert executor.has_handler("nonexistent") is False

    def test_has_rollback_handler_returns_true(self):
        """Test checking if rollback handler exists"""
        executor = SimpleExecutor()
        handler = Mock()
        rollback_handler = Mock()

        executor.register("action", handler, rollback_handler)

        assert executor.has_rollback_handler("action") is True

    def test_has_rollback_handler_returns_false_when_not_registered(self):
        """Test checking for non-existent rollback handler"""
        executor = SimpleExecutor()
        handler = Mock()

        executor.register("action", handler)

        assert executor.has_rollback_handler("action") is False

    def test_has_rollback_handler_returns_false_for_unknown_action(self):
        """Test checking rollback handler for unknown action"""
        executor = SimpleExecutor()

        assert executor.has_rollback_handler("nonexistent") is False


class TestSimpleExecutorExecutionHistory:
    """Test execution history tracking"""

    def test_get_execution_history_empty(self):
        """Test execution history is empty initially"""
        executor = SimpleExecutor()

        history = executor.get_execution_history()

        assert history == []

    def test_get_execution_history_tracks_successful_execution(self, execution_context):
        """Test that successful execution is tracked"""
        executor = SimpleExecutor()
        handler = Mock(return_value={"result": "ok"})

        executor.register("action", handler)

        task = Task(id="t1", name="Test", action="action", params={})

        executor.execute(task, execution_context)

        history = executor.get_execution_history()

        assert len(history) == 1
        assert history[0]["task_id"] == "t1"
        assert history[0]["action"] == "action"
        assert history[0]["status"] == "success"

    def test_get_execution_history_tracks_failed_execution(self, execution_context):
        """Test that failed execution is tracked"""
        executor = SimpleExecutor()

        task = Task(id="t1", name="Test", action="unknown", params={})

        executor.execute(task, execution_context)

        history = executor.get_execution_history()

        assert len(history) == 1
        assert history[0]["status"] == "failed"

    def test_get_execution_history_tracks_multiple_executions(self, execution_context):
        """Test that multiple executions are tracked"""
        executor = SimpleExecutor()
        handler = Mock(return_value={"result": "ok"})

        executor.register("action", handler)

        task1 = Task(id="t1", name="Test1", action="action", params={})
        task2 = Task(id="t2", name="Test2", action="action", params={})

        executor.execute(task1, execution_context)
        executor.execute(task2, execution_context)

        history = executor.get_execution_history()

        assert len(history) == 2
        assert history[0]["task_id"] == "t1"
        assert history[1]["task_id"] == "t2"

    def test_clear_execution_history(self, execution_context):
        """Test clearing execution history"""
        executor = SimpleExecutor()
        handler = Mock(return_value={"result": "ok"})

        executor.register("action", handler)

        task = Task(id="t1", name="Test", action="action", params={})

        executor.execute(task, execution_context)

        assert len(executor.get_execution_history()) == 1

        executor.clear_execution_history()

        assert len(executor.get_execution_history()) == 0


class TestSimpleExecutorRollbackHistory:
    """Test rollback history tracking"""

    def test_get_rollback_history_empty(self):
        """Test rollback history is empty initially"""
        executor = SimpleExecutor()

        history = executor.get_rollback_history()

        assert history == []

    def test_get_rollback_history_tracks_rollback(self, execution_context):
        """Test that rollback is tracked"""
        executor = SimpleExecutor()
        rollback_handler = Mock()

        executor.register("action", Mock(), rollback_handler)

        task = Task(id="t1", name="Test", action="action", params={})

        executor.rollback(task, execution_context)

        history = executor.get_rollback_history()

        assert len(history) == 1
        assert history[0]["task_id"] == "t1"
        assert history[0]["action"] == "action"

    def test_get_rollback_history_tracks_multiple_rollbacks(self, execution_context):
        """Test that multiple rollbacks are tracked"""
        executor = SimpleExecutor()
        rollback_handler = Mock()

        executor.register("action", Mock(), rollback_handler)

        task1 = Task(id="t1", name="Test1", action="action", params={})
        task2 = Task(id="t2", name="Test2", action="action", params={})

        executor.rollback(task1, execution_context)
        executor.rollback(task2, execution_context)

        history = executor.get_rollback_history()

        assert len(history) == 2


class TestSimpleExecutorBatchExecution:
    """Test batch execution"""

    def test_execute_batch_all_succeed(self, execution_context):
        """Test batch execution when all tasks succeed"""
        executor = SimpleExecutor()
        handler = Mock(return_value={"result": "ok"})

        executor.register("action", handler)

        tasks = [
            Task(id="t1", name="Test1", action="action", params={}),
            Task(id="t2", name="Test2", action="action", params={}),
            Task(id="t3", name="Test3", action="action", params={}),
        ]

        results = executor.execute_batch(tasks, execution_context)

        assert len(results) == 3
        assert all(r["status"] == "success" for r in results)
        assert handler.call_count == 3

    def test_execute_batch_with_failure(self, execution_context):
        """Test batch execution with one failing task"""
        executor = SimpleExecutor()
        handler = Mock(return_value={"result": "ok"})

        executor.register("action", handler)

        tasks = [
            Task(id="t1", name="Test1", action="action", params={}),
            Task(id="t2", name="Test2", action="unknown", params={}),
            Task(id="t3", name="Test3", action="action", params={}),
        ]

        results = executor.execute_batch(tasks, execution_context)

        assert len(results) == 3
        assert results[0]["status"] == "success"
        assert results[1]["status"] == "failed"
        assert results[2]["status"] == "success"

    def test_execute_batch_empty_list(self, execution_context):
        """Test batch execution with empty list"""
        executor = SimpleExecutor()

        results = executor.execute_batch([], execution_context)

        assert results == []

    def test_execute_batch_returns_summary(self, execution_context):
        """Test batch execution returns summary info"""
        executor = SimpleExecutor()
        handler = Mock(return_value={"result": "ok"})

        executor.register("action", handler)

        tasks = [
            Task(id="t1", name="Test1", action="action", params={}),
            Task(id="t2", name="Test2", action="action", params={}),
        ]

        results = executor.execute_batch(tasks, execution_context)

        assert all("task_id" in r and "status" in r for r in results)


class TestSimpleExecutorStats:
    """Test executor statistics"""

    def test_get_stats_initial(self):
        """Test initial executor stats"""
        executor = SimpleExecutor()

        stats = executor.get_stats()

        assert stats["total_executions"] == 0
        assert stats["successful_executions"] == 0
        assert stats["failed_executions"] == 0
        assert stats["total_rollbacks"] == 0

    def test_get_stats_after_execution(self, execution_context):
        """Test executor stats after execution"""
        executor = SimpleExecutor()
        handler = Mock(return_value={"result": "ok"})

        executor.register("action", handler)

        task = Task(id="t1", name="Test", action="action", params={})

        executor.execute(task, execution_context)

        stats = executor.get_stats()

        assert stats["total_executions"] == 1
        assert stats["successful_executions"] == 1
        assert stats["failed_executions"] == 0

    def test_get_stats_with_failures(self, execution_context):
        """Test executor stats with failures"""
        executor = SimpleExecutor()

        task1 = Task(id="t1", name="Test1", action="action", params={})
        task2 = Task(id="t2", name="Test2", action="unknown", params={})

        executor.execute(task1, execution_context)
        executor.execute(task2, execution_context)

        stats = executor.get_stats()

        assert stats["total_executions"] == 2
        assert stats["successful_executions"] == 0
        assert stats["failed_executions"] == 2

    def test_get_stats_with_rollbacks(self, execution_context):
        """Test executor stats with rollbacks"""
        executor = SimpleExecutor()
        rollback_handler = Mock()

        executor.register("action", Mock(), rollback_handler)

        task = Task(id="t1", name="Test", action="action", params={})

        executor.rollback(task, execution_context)

        stats = executor.get_stats()

        assert stats["total_rollbacks"] == 1
