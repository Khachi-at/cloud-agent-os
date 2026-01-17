from abc import ABC, abstractmethod
from typing import Dict, Any


class Auditor(ABC):

    @abstractmethod
    def record(self, event: Dict[str, Any]) -> None:
        """
        记录所有决策和执行事件
        """
        pass
