# planner_schema.py
from typing import Any, Dict, List

from pydantic import BaseModel, Field

PLANNER_SYSTEM_PROMPT = """
You are a cloud orchestration planner.

Rules:
- Break the goal into executable steps
- Each step must be safe, minimal, and reversible
- Output ONLY valid JSON
- Use unique task IDs (t1, t2, t3...)
- Dependencies must reference previous task IDs
- No explanations, no markdown

Output format:
{{
  "goal": "...",
  "tasks": [
    {{
      "id": "t1",
      "name": "...",
      "action": "...",
      "params": {{}},
      "depends": []
    }}
  ]
}}
"""


class LLMTask(BaseModel):
    id: str = Field(..., description="Unique task id, e.g. t1, t2")
    name: str
    action: str
    params: Dict[str, Any] = {}
    depends: List[str] = []


class LLMPlan(BaseModel):
    goal: str
    tasks: List[LLMTask]
