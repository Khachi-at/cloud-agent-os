from dataclasses import dataclass
from typing import Dict


@dataclass
class ExecutionContext:
    tenant: str
    region: str
    env: str
    trace_id: str
    metadata: Dict[str, str]
