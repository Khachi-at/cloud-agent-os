from audit import Auditor
from context import ExecutionContext
from executor import Executor
from models import Task, TaskStatus
from planner import Planner
from policy import PolicyEngine
from scheduler import Scheduler


class Orchestrator:
    def __init__(
        self,
        planner: Planner,
        policy: PolicyEngine,
        scheduler: Scheduler,
        executor: Executor,
        auditor: Auditor,
    ):
        self.planner = planner
        self.policy = policy
        self.scheduler = scheduler
        self.executor = executor
        self.auditor = auditor

    def run(self, goal: str, ctx: ExecutionContext):
        plan = self.planner.plan(goal, ctx)
        self.auditor.record({"event": "plan_created", "plan": plan.goal})

        while True:
            batch = self.scheduler.next_batch(plan)
            if not batch:
                break

            for task in batch:
                self._run_task(task, ctx)

        return plan

    def _run_task(self, task: Task, ctx: ExecutionContext):
        decision = self.policy.evaluate(
            subject="ai-agent", action=task.action, resource=task.params, ctx=ctx
        )

        self.auditor.record({"event": "policy_decision", "task": task.id, "decision": decision})

        if decision["decision"] != "allow":
            task.status = TaskStatus.FAILED
            task.error = "Policy denied"
            return

        try:
            task.status = TaskStatus.RUNNING
            self.executor.execute(task, ctx)
            task.status = TaskStatus.SUCCESS
        except Exception as e:
            task.status = TaskStatus.FAILED
            task.error = str(e)
            self._rollback(task, ctx)

    def _rollback(self, failed_task, ctx):
        # 简化版：反向回滚已成功任务
        pass
