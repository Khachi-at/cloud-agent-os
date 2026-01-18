"""
Planner module for AI agent planning and replanning strategies.

This module provides the abstract base class for implementing planning strategies.
Planners are responsible for converting high-level goals into executable task plans,
and for replanning when tasks fail during execution.
"""

from abc import ABC, abstractmethod

from core.context import ExecutionContext
from core.models import Plan, Task


class Planner(ABC):
    """
    Abstract base class for AI agent planning strategies.

    A planner is responsible for creating and managing task plans based on
    goals and execution context. It handles both initial planning and replanning
    when failures occur during task execution.
    """

    @abstractmethod
    def plan(self, goal: str, ctx: ExecutionContext) -> Plan:
        """
        Create an initial plan to achieve a given goal.

        Given a goal description and execution context, generates a comprehensive
        plan consisting of tasks that should be executed in sequence or in parallel
        to achieve the specified goal.

        Args:
            goal: A string description of the goal to be achieved.
            ctx: An ExecutionContext object containing the current execution state,
                environment information, and available resources.

        Returns:
            A Plan object representing the tasks and their dependencies needed
            to achieve the goal.

        Raises:
            NotImplementedError: This is an abstract method and must be implemented
                by subclasses.
        """

    @abstractmethod
    def replan(self, plan: Plan, failed_task: Task, ctx: ExecutionContext) -> Plan:
        """
        Create a revised plan when a task fails during execution.

        When a task in the current plan fails, this method is called to generate
        a new or modified plan that accounts for the failure. This might involve
        skipping the failed task, retrying with different parameters, or choosing
        an alternative approach to achieve the goal.

        Args:
            plan: The original Plan object that included the failed task.
            failed_task: The Task object that failed during execution.
            ctx: An ExecutionContext object containing the current execution state,
                updated with information about the failure.

        Returns:
            A revised Plan object that represents an alternative approach to
            achieve the goal, potentially incorporating lessons from the failure.

        Raises:
            NotImplementedError: This is an abstract method and must be implemented
                by subclasses.
        """
