from abc import ABC, abstractmethod
from typing import List

from src.models import Plan, Task


class Scheduler(ABC):
    @abstractmethod
    def next_batch(self, plan: Plan) -> List[Task]:
        """
        返回当前可执行任务集合（依赖已满足）
        """
        pass
