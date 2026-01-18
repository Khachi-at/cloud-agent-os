"""
Orchestrator module for coordinating cloud automation tasks.

The orchestrator acts as the central coordinator, orchestrating the execution of
cloud operations through a pipeline of planning, policy evaluation, scheduling,
and execution. It integrates with the control plane for resource management.

Architecture:
    1. Planner: Converts goals into task plans
    2. Scheduler: Determines task execution order and batching
    3. PolicyEngine: Evaluates security and compliance policies
    4. ControlPlane: Manages cloud resources and infrastructure
    5. Executor: Executes tasks using the control plane
    6. Auditor: Records all actions and decisions
"""

from core.agent.planner import Planner
from core.audit import Auditor
from core.context import ExecutionContext
from core.control_plane import ControlPlane
from core.executor import Executor
from core.models import Plan, Task, TaskStatus
from core.policy import PolicyEngine
from core.scheduler import Scheduler


class Orchestrator:
    """
    Central orchestrator for cloud automation workflows.

    Coordinates the execution of plans by orchestrating multiple components:
    - Planner: Generates task plans from goals
    - Scheduler: Orders and batches task execution
    - PolicyEngine: Evaluates security/compliance policies
    - ControlPlane: Manages cloud resources and state
    - Executor: Executes tasks on the control plane
    - Auditor: Tracks all operations and decisions

    The orchestrator implements a pipeline architecture where each task is
    evaluated for policy compliance before execution, and all actions are
    recorded for audit trails.
    """

    def __init__(
        self,
        planner: Planner,
        policy: PolicyEngine,
        scheduler: Scheduler,
        executor: Executor,
        control_plane: ControlPlane,
        auditor: Auditor,
    ):
        """
        Initialize the orchestrator with all required components.

        Args:
            planner: The planner instance for generating task plans.
            policy: The policy engine for evaluating security policies.
            scheduler: The scheduler for ordering task execution.
            executor: The executor for running tasks.
            control_plane: The control plane for managing cloud resources.
            auditor: The auditor for recording operations and decisions.
        """
        self.planner = planner
        self.policy = policy
        self.scheduler = scheduler
        self.executor = executor
        self.control_plane = control_plane
        self.auditor = auditor
        self.executed_tasks = []  # Track executed tasks for rollback

    def run(self, goal: str, ctx: ExecutionContext) -> Plan:
        """
        Execute a plan to achieve a given goal.

        Orchestrates the complete workflow:
        1. Generate a plan from the goal
        2. Schedule tasks for execution
        3. Evaluate policy for each task
        4. Execute approved tasks via the control plane
        5. Audit all actions and decisions

        Args:
            goal: The high-level goal to achieve.
            ctx: The execution context containing tenant, region, and metadata.

        Returns:
            The completed Plan object with task results and statuses.

        Raises:
            Exception: If planning or execution fails critically.
        """
        # Generate plan from goal
        plan = self.planner.plan(goal, ctx)
        self.auditor.record(
            {"event": "plan_created", "plan": plan.goal, "task_count": len(plan.tasks)}
        )

        # Execute scheduled batches
        while True:
            batch = self.scheduler.next_batch(plan)
            if not batch:
                break

            for task in batch:
                self._run_task(task, ctx)

        self.auditor.record({"event": "plan_completed", "plan": plan.goal})
        return plan

    def _run_task(self, task: Task, ctx: ExecutionContext) -> None:
        """
        Execute a single task through the policy-controlled pipeline.

        Process:
        1. Evaluate policy compliance
        2. Query resource state from control plane
        3. Execute task via executor
        4. Record results and audit events

        Args:
            task: The task to execute.
            ctx: The execution context.
        """
        # Step 1: Policy evaluation
        decision = self.policy.evaluate(
            subject="ai-agent", action=task.action, resource=task.params, ctx=ctx
        )

        self.auditor.record(
            {
                "event": "policy_decision",
                "task": task.id,
                "action": task.action,
                "decision": decision["decision"],
                "reason": decision.get("reason"),
            }
        )

        # Deny execution if policy rejects
        if decision["decision"] != "allow":
            task.status = TaskStatus.FAILED
            task.error = f"Policy denied: {decision.get('reason', 'unknown')}"
            return

        # Step 2: Execute task
        try:
            task.status = TaskStatus.RUNNING

            # Execute via executor which uses control plane
            self.executor.execute(task, ctx, self.control_plane)

            task.status = TaskStatus.SUCCESS
            self.executed_tasks.append(task)  # Track for potential rollback

            self.auditor.record(
                {
                    "event": "task_completed",
                    "task": task.id,
                    "action": task.action,
                    "result": task.result,
                }
            )
        except Exception as e:
            # Handle execution failure
            task.status = TaskStatus.FAILED
            task.error = str(e)

            self.auditor.record(
                {
                    "event": "task_failed",
                    "task": task.id,
                    "action": task.action,
                    "error": str(e),
                }
            )

            # Attempt rollback
            self._rollback(task, ctx)

    def _rollback(self, failed_task: Task, ctx: ExecutionContext) -> None:
        """
        Rollback tasks in reverse order when a failure occurs.

        Attempts to undo the side effects of successfully executed tasks
        by calling their rollback methods. Rollback happens in reverse
        order of execution to maintain consistency.

        Args:
            failed_task: The task that failed, triggering rollback.
            ctx: The execution context.
        """
        self.auditor.record(
            {
                "event": "rollback_started",
                "failed_task": failed_task.id,
                "rollback_count": len(self.executed_tasks),
            }
        )

        # Rollback in reverse order
        for task in reversed(self.executed_tasks):
            try:
                self.executor.rollback(task, ctx, self.control_plane)
                task.status = TaskStatus.ROLLED_BACK

                self.auditor.record(
                    {
                        "event": "task_rolled_back",
                        "task": task.id,
                        "action": task.action,
                    }
                )
            except Exception as e:
                self.auditor.record(
                    {
                        "event": "rollback_failed",
                        "task": task.id,
                        "error": str(e),
                    }
                )
