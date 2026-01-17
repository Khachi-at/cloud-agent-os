import json

from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from pydantic import ValidationError

from src.context import ExecutionContext
from src.models import Plan, Task, TaskStatus
from src.planner import Planner
from src.planners.schema import PLANNER_SYSTEM_PROMPT, LLMPlan


class LangChainPlanner(Planner):
    def __init__(self, model="deepseek-chat", temperature=0) -> None:
        self.llm = ChatOpenAI(
            model=model,
            base_url="https://api.deepseek.com",
            temperature=temperature,
        )
        self.prompt = ChatPromptTemplate.from_messages(
            [("system", PLANNER_SYSTEM_PROMPT), ("human", "{goal}")]
        )

    def _call_llm(self, goal: str) -> str | list[str | dict]:
        chain = self.prompt | self.llm
        response = chain.invoke({"goal": goal})
        return response.content

    def _parse(self, raw: str) -> LLMPlan:
        try:
            data = json.loads(raw)
            return LLMPlan(**data)
        except (json.JSONDecodeError, ValidationError) as e:
            raise ValueError(f"Invalid LLM output: {e}") from e

    def plan(self, goal: str, ctx: ExecutionContext) -> Plan:
        for attempt in range(3):
            try:
                raw = self._call_llm(goal)
                llm_plan = self._parse(raw)
                return self._convert(llm_plan)
            except Exception:
                if attempt == 2:
                    raise
        raise RuntimeError("Planner failed")

    def replan(self, plan: Plan, failed_task: Task, ctx: ExecutionContext) -> Plan:
        repair_prompt = f"""
A plan failed.

Goal: {plan.goal}
Failed Task: {failed_task.name}
Error: {failed_task.error}

Generate a new plan that safely recovers.
Output ONLY JSON.
"""
        raw = self._call_llm(repair_prompt)
        llm_plan = self._parse(raw)
        return self._convert(llm_plan)

    def _convert(self, llm_plan: LLMPlan) -> Plan:
        tasks = []
        for t in llm_plan.tasks:
            tasks.append(
                Task(
                    id=t.id,
                    name=t.name,
                    action=t.action,
                    params=t.params,
                    depends=t.depends,
                    status=TaskStatus.PENDING,
                )
            )
        return Plan(goal=llm_plan.goal, tasks=tasks)
