from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class TaskStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"


@dataclass
class Task:
    id: str
    name: str
    action: str
    params: Dict[str, Any] = field(default_factory=dict)
    depends: List[str] = field(default_factory=list)
    status: TaskStatus = TaskStatus.PENDING
    result: Optional[Any] = None
    error: Optional[str] = None


@dataclass
class Plan:
    goal: str
    tasks: List[Task]
    status: str = "planned"
