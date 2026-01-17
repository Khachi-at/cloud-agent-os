from abc import ABC, abstractmethod

from context import ExecutionContext
from models import Plan, Task


class Planner(ABC):
    @abstractmethod
    def plan(self, goal: str, ctx: ExecutionContext) -> Plan:
        """
        将目标拆解成可执行任务 DAG
        """
        pass

    @abstractmethod
    def replan(self, plan: Plan, failed_task: Task, ctx: ExecutionContext) -> Plan:
        """
        执行失败时生成恢复计划
        """
        pass
