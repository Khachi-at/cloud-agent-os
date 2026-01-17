from abc import ABC, abstractmethod
from typing import Any, Dict

from src.context import ExecutionContext


class PolicyDecision(str):
    ALLOW = "allow"
    DENY = "deny"
    APPROVE = "approve"


class PolicyEngine(ABC):
    @abstractmethod
    def evaluate(
        self, subject: str, action: str, resource: Dict[str, Any], ctx: ExecutionContext
    ) -> Dict[str, Any]:
        """
        返回:
        {
          decision: allow|deny|approve
          reason: str
          risk_score: int
        }
        """
        pass
