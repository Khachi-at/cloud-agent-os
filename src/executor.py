from abc import ABC, abstractmethod
from models import Task
from context import ExecutionContext


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
