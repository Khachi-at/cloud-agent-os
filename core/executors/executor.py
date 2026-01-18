"""
Simple Executor implementation for testing and basic task execution.

This executor provides a handler registration system for mapping actions to
callables, with optional rollback support, execution history tracking, and
batch processing capabilities.
"""

from typing import Any, Callable, Dict, List, Optional

from core.context import ExecutionContext
from core.control_plane import ControlPlane
from core.executor import Executor
from core.models import Task, TaskStatus


class SimpleExecutor(Executor):
    """
    Simple executor implementation with handler registration pattern.

    This executor allows registering handlers (callables) for different action types.
    Each handler is called with task parameters and execution context, and optionally
    supports rollback handlers for cleanup.

    Features:
    - Handler registration and unregistration
    - Execution and rollback tracking
    - Batch task execution
    - Execution statistics

    Useful for:
    - Testing and mocking
    - Simple sequential task execution
    - Development and debugging
    """

    def __init__(self) -> None:
        """Initialize the executor with empty handler registries and history."""
        self._handlers: Dict[
            str, Callable[[Dict[str, Any], ExecutionContext, Optional[ControlPlane]], Any]
        ] = {}
        self._rollback_handlers: Dict[
            str, Callable[[Dict[str, Any], ExecutionContext, Optional[ControlPlane]], None]
        ] = {}
        self._execution_history: List[Dict[str, Any]] = []
        self._rollback_history: List[Dict[str, Any]] = []
        self._stats: Dict[str, int] = {
            "total_executions": 0,
            "successful_executions": 0,
            "failed_executions": 0,
            "total_rollbacks": 0,
        }

    def register(
        self,
        action: str,
        handler: Callable[[Dict[str, Any], ExecutionContext, Optional[ControlPlane]], Any],
        rollback: Optional[
            Callable[[Dict[str, Any], ExecutionContext, Optional[ControlPlane]], None]
        ] = None,
    ) -> None:
        """
        Register a handler for an action.

        Args:
            action: The action name to handle (e.g., 'create_instance').
            handler: A callable that executes the action. Signature:
                The handler receives task parameters, execution context, and control plane.
            rollback: Optional rollback handler for cleanup. Signature:
        """
        self._handlers[action] = handler
        if rollback:
            self._rollback_handlers[action] = rollback

    def unregister(self, action: str) -> None:
        """
        Unregister a handler for an action.

        Removes both the action handler and its rollback handler if present.

        Args:
            action: The action name to unregister.
        """
        self._handlers.pop(action, None)
        self._rollback_handlers.pop(action, None)

    def has_handler(self, action: str) -> bool:
        """
        Check if a handler is registered for an action.

        Args:
            action: The action name to check.

        Returns:
            True if a handler is registered, False otherwise.
        """
        return action in self._handlers

    def has_rollback_handler(self, action: str) -> bool:
        """
        Check if a rollback handler is registered for an action.

        Args:
            action: The action name to check.

        Returns:
            True if a rollback handler is registered, False otherwise.
        """
        return action in self._rollback_handlers

    def execute(
        self,
        task: Task,
        ctx: ExecutionContext,
        control_plane: Optional[ControlPlane] = None,
    ) -> None:
        """
        Execute a task using a registered handler.

        Looks up the handler for task.action, calls it with task parameters,
        execution context, and control plane, then updates task status and result.
        On error, marks task as failed. Tracks execution in history.

        Args:
            task: The task to execute.
            ctx: The execution context.
            control_plane: Optional control plane instance for resource management.

        Sets:
            task.status: RUNNING during execution, SUCCESS or FAILED after.
            task.result: Handler output on success.
            task.error: Error message on failure.
        """
        if task.action not in self._handlers:
            task.status = TaskStatus.FAILED
            task.error = f"No handler for {task.action}"
            self._stats["total_executions"] += 1
            self._stats["failed_executions"] += 1
            self._record_execution(task, "FAILED")
            return

        try:
            task.status = TaskStatus.RUNNING
            result = self._handlers[task.action](task.params, ctx, control_plane)
            task.result = result
            task.status = TaskStatus.SUCCESS
            self._stats["total_executions"] += 1
            self._stats["successful_executions"] += 1
            self._record_execution(task, "SUCCESS")
        except Exception as e:
            task.status = TaskStatus.FAILED
            task.error = str(e)
            self._stats["total_executions"] += 1
            self._stats["failed_executions"] += 1
            self._record_execution(task, "FAILED")

    def rollback(
        self,
        task: Task,
        ctx: ExecutionContext,
        control_plane: Optional[ControlPlane] = None,
    ) -> None:
        """
        Rollback a task using its registered rollback handler.

        If a rollback handler is registered for this action, calls it with task
        parameters, execution context, and control plane to clean up side effects.
        Updates task status on success. Tracks rollback in history.

        Args:
            task: The task to rollback.
            ctx: The execution context.
            control_plane: Optional control plane instance for resource cleanup.

        Sets:
            task.status: ROLLED_BACK on successful rollback.
            task.error: Updated with rollback error if rollback fails.
        """
        if task.action and task.action in self._rollback_handlers:
            try:
                self._rollback_handlers[task.action](task.params, ctx, control_plane)
                task.status = TaskStatus.ROLLED_BACK
                self._stats["total_rollbacks"] += 1
                self._record_rollback(task)
            except Exception as e:
                task.error = f"Rollback failed: {str(e)}"

    def execute_batch(
        self,
        tasks: List[Task],
        ctx: ExecutionContext,
        control_plane: Optional[ControlPlane] = None,
    ) -> List[Dict[str, Any]]:
        """
        Execute multiple tasks in sequence.

        Executes each task and returns a list of execution results.
        Continues execution even if some tasks fail.

        Args:
            tasks: List of tasks to execute.
            ctx: The execution context.
            control_plane: Optional control plane instance.

        Returns:
            List of result dicts with keys:
                task_id, action, status, result (optional), error (optional).
        """
        results = []
        for task in tasks:
            self.execute(task, ctx, control_plane)
            result_dict = {
                "task_id": task.id,
                "action": task.action,
                "status": task.status.value,
            }
            if task.result:
                result_dict["result"] = task.result
            if task.error:
                result_dict["error"] = task.error
            results.append(result_dict)
        return results

    def get_execution_history(self) -> List[Dict[str, Any]]:
        """
        Get the execution history.

        Returns:
            List of execution records with task_id, action, and status.
        """
        return self._execution_history.copy()

    def clear_execution_history(self) -> None:
        """Clear the execution history."""
        self._execution_history.clear()

    def get_rollback_history(self) -> List[Dict[str, Any]]:
        """
        Get the rollback history.

        Returns:
            List of rollback records with task_id and action.
        """
        return self._rollback_history.copy()

    def get_stats(self) -> Dict[str, int]:
        """
        Get executor statistics.

        Returns:
            Dict with keys: total_executions, successful_executions,
            failed_executions, total_rollbacks.
        """
        return self._stats.copy()

    def _record_execution(self, task: Task, status: str) -> None:
        """
        Record an execution in history.

        Args:
            task: The executed task.
            status: The execution status (SUCCESS or FAILED).
        """
        # Convert status string to lowercase enum value
        status_value = status.lower() if isinstance(status, str) else str(status)
        self._execution_history.append(
            {
                "task_id": task.id,
                "action": task.action,
                "status": status_value,
            }
        )

    def _record_rollback(self, task: Task) -> None:
        """
        Record a rollback in history.

        Args:
            task: The rolled back task.
        """
        self._rollback_history.append(
            {
                "task_id": task.id,
                "action": task.action,
            }
        )
