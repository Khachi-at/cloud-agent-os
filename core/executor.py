"""
Executor module for task execution on cloud resources.

This module defines the abstract interface for task executors. Executors handle
the actual execution of tasks against cloud resources through the control plane,
and support rollback of task side effects.
"""

from abc import ABC, abstractmethod

from core.context import ExecutionContext
from core.control_plane import ControlPlane
from core.models import Task


class Executor(ABC):
    """
    Abstract base class for task execution strategies.

    An executor is responsible for translating task specifications into
    concrete operations on cloud resources. It interacts with the control
    plane to manage resources and supports rollback functionality.
    """

    @abstractmethod
    def execute(self, task: Task, ctx: ExecutionContext, control_plane: ControlPlane) -> None:
        """
        Execute a task using the provided control plane.

        The executor translates the task's action and parameters into control
        plane operations. It updates the task with results and status information.

        Args:
            task: The Task object to execute. Task properties include:
                - action: The operation type (e.g., 'create_instance', 'apply_config')
                - params: Dictionary of action parameters
                - id: Unique task identifier for tracking
            ctx: The execution context containing tenant, region, and metadata.
            control_plane: The ControlPlane instance for resource management.
                Used to apply configurations and query resource state.

        Raises:
            Exception: If execution fails. The exception message should be
                descriptive for audit logging and user feedback.
        """
        pass

    @abstractmethod
    def rollback(self, task: Task, ctx: ExecutionContext, control_plane: ControlPlane) -> None:
        """
        Rollback a successfully executed task to undo its side effects.

        This method is called when a subsequent task fails, allowing the executor
        to clean up or revert changes made by this task. Rollback should be
        idempotent and handle cases where partial cleanup may have occurred.

        Args:
            task: The Task object to rollback. Should contain result information
                from the original execution.
            ctx: The execution context containing tenant, region, and metadata.
            control_plane: The ControlPlane instance for resource management.
                Used to delete or revert configurations.

        Raises:
            Exception: If rollback fails. Critical errors should be logged as
                they may leave resources in an inconsistent state.
        """
        pass
