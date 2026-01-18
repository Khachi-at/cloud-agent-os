"""
Scheduler module for managing task execution scheduling.

This module provides the abstract base class for implementing scheduling strategies.
Schedulers determine the order and batching of tasks from a plan for execution.
"""

from abc import ABC, abstractmethod
from typing import List

from core.models import Plan, Task


class Scheduler(ABC):
    """
    Abstract base class for task scheduling strategies.

    A scheduler determines how tasks from a plan are organized and executed,
    including task ordering, batching, and dependency resolution.
    """

    @abstractmethod
    def next_batch(self, plan: Plan) -> List[Task]:
        """
        Get the next batch of tasks to execute from the plan.

        This method determines which tasks should be executed next based on the
        scheduling strategy. Tasks may be returned individually or in groups
        (batches) depending on the specific scheduler implementation.

        Args:
            plan: A Plan object containing the tasks to be scheduled.

        Returns:
            A list of Task objects representing the next batch to execute.
            An empty list indicates no more tasks are available for execution.

        Raises:
            NotImplementedError: This is an abstract method and must be implemented
                by subclasses.
        """
