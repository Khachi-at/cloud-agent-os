from typing import List

from core.models import Plan, Task, TaskStatus
from core.scheduler import Scheduler


class DAGScheduler(Scheduler):
    def __init__(self, max_parallel: int = 4) -> None:
        self.max_parallel = max_parallel

    def next_batch(self, plan: Plan) -> List[Task]:
        ready = []
        task_map = {t.id: t for t in plan.tasks}

        for task in plan.tasks:
            if task.status != TaskStatus.PENDING:
                continue
            if all(task_map[dep].status == TaskStatus.SUCCESS for dep in task.depends):
                ready.append(task)

        return ready[: self.max_parallel]
