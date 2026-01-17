from abc import ABC, abstractmethod
from typing import Any, Dict


class ControlPlane(ABC):
    @abstractmethod
    def apply(self, kind: str, spec: Dict[str, Any]) -> Dict[str, Any]:
        """
        创建 / 更新资源
        """
        pass

    @abstractmethod
    def get(self, kind: str, resource_id: str) -> Dict[str, Any]:
        """
        查询资源状态
        """
        pass
