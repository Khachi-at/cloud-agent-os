"""
LangChain-based planner implementation for cloud orchestration.

This module provides a concrete implementation of the Planner interface using
LangChain and OpenAI/DeepSeek models. It generates task plans from natural language
goals and handles replanning when failures occur.
"""

import json

from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from pydantic import ValidationError

from core.agent.planner import Planner
from core.agent.planners.schema import PLANNER_SYSTEM_PROMPT, LLMPlan
from core.context import ExecutionContext
from core.models import Plan, Task, TaskStatus


class LangChainPlanner(Planner):
    """
    LangChain-based implementation of the Planner interface.

    This planner uses a Large Language Model (via LangChain) to generate
    structured task plans from natural language goals. It leverages the
    DeepSeek API for planning and includes retry logic for robustness.

    Attributes:
        llm: ChatOpenAI instance configured for planning tasks.
        prompt: ChatPromptTemplate combining system instructions and user goals.
    """

    def __init__(self, model="deepseek-chat", temperature=0) -> None:
        """
        Initialize the LangChain planner with LLM configuration.

        Args:
            model: The LLM model name (default: "deepseek-chat").
                Compatible with any model available through the DeepSeek API.
            temperature: LLM temperature parameter controlling output randomness
                (default: 0 for deterministic output). Range: [0, 2].
        """
        self.llm = ChatOpenAI(
            model=model,
            base_url="https://api.deepseek.com",
            temperature=temperature,
        )
        self.prompt = ChatPromptTemplate.from_messages(
            [("system", PLANNER_SYSTEM_PROMPT), ("human", "{goal}")]
        )

    def _call_llm(self, goal: str) -> str | list[str | dict]:
        """
        Call the LLM with a goal or prompt and return the raw response.

        Args:
            goal: The goal string or prompt to send to the LLM.

        Returns:
            The LLM's response content as a string or structured format.
        """
        chain = self.prompt | self.llm
        response = chain.invoke({"goal": goal})
        return response.content

    def _parse(self, raw: str) -> LLMPlan:
        """
        Parse raw LLM output into a structured LLMPlan object.

        Validates the JSON response against the LLMPlan schema and converts
        it to a structured Pydantic model.

        Args:
            raw: The raw JSON string from the LLM.

        Returns:
            An LLMPlan object containing the parsed goal and tasks.

        Raises:
            ValueError: If the raw output is invalid JSON or doesn't match
                the expected LLMPlan schema.
        """
        try:
            data = json.loads(raw)
            return LLMPlan(**data)
        except (json.JSONDecodeError, ValidationError) as e:
            raise ValueError(f"Invalid LLM output: {e}") from e

    def plan(self, goal: str, ctx: ExecutionContext) -> Plan:
        """
        Generate an initial plan for the given goal.

        Calls the LLM with the goal and converts the response to a Plan object.
        Includes retry logic (up to 3 attempts) to handle transient failures.

        Args:
            goal: The goal description to plan for.
            ctx: The current execution context (unused in this implementation).

        Returns:
            A Plan object containing tasks with dependencies.

        Raises:
            ValueError: If the LLM output is invalid after all retries.
            RuntimeError: If planning fails after all retry attempts.
        """
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
        """
        Generate a revised plan after a task fails during execution.

        Constructs a repair prompt containing the original goal, failed task name,
        and error information, then calls the LLM to generate a recovery plan.

        Args:
            plan: The original plan that contained the failed task.
            failed_task: The task that failed, including error information.
            ctx: The current execution context (unused in this implementation).

        Returns:
            A new Plan object representing a recovery strategy.

        Raises:
            ValueError: If the LLM output is invalid.
        """
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
        """
        Convert an LLMPlan object to a Plan object with Task instances.

        Transforms the LangChain-compatible LLMPlan into the internal Plan format,
        creating Task objects with PENDING status.

        Args:
            llm_plan: The LLMPlan object from LLM parsing.

        Returns:
            A Plan object ready for execution by the orchestrator.
        """
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
