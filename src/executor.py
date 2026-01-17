from abc import ABC, abstractmethod

from context import ExecutionContext
from models import Task


class Executor(ABC):
    @abstractmethod
    def execute(self, task: Task, ctx: ExecutionContext) -> None:
        """
        执行任务，更新 task.result / task.status
        """
        pass

    @abstractmethod
    def rollback(self, task: Task, ctx: ExecutionContext) -> None:
        """
        回滚任务副作用
        """
        pass
