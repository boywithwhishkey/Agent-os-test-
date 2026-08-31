from __future__ import annotations

import os

from app.llm.factory import build_llm_provider
from app.services.llm_agents import ParallelAgentExecutor, SpecialistJob
from app.services.llm_verifier import LLMVerifier


async def execute_phase3(objective: str, tasks: list[str]) -> dict:
    provider = build_llm_provider()
    executor = ParallelAgentExecutor(
        provider,
        max_parallel=int(os.getenv("AGENT_OS_MAX_PARALLEL", "3")),
        max_retries=int(os.getenv("AGENT_OS_MAX_RETRIES", "2")),
    )
    jobs = [
        SpecialistJob(name=f"specialist-{index}", task=task)
        for index, task in enumerate(tasks, start=1)
    ]
    results = await executor.run(jobs)
    verification = await LLMVerifier(provider).verify(objective, results)
    return {
        "objective": objective,
        "results": [
            {"name": r.name, "output": r.output, "attempts": r.attempts}
            for r in results
        ],
        "verification": {
            "approved": verification.approved,
            "feedback": verification.feedback,
        },
    }
