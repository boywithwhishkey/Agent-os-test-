from __future__ import annotations

import json
from dataclasses import asdict, dataclass

from app.core.config import settings
from app.llm.base import LLMProvider, LLMRequest
from app.llm.factory import build_llm_provider
from app.services.llm_agents import ParallelAgentExecutor, SpecialistJob, SpecialistResult
from app.services.llm_verifier import LLMVerifier, VerificationResult


@dataclass(slots=True)
class DynamicPlan:
    jobs: list[SpecialistJob]


class LLMPlanner:
    def __init__(self, provider: LLMProvider, max_jobs: int = 6):
        self.provider = provider
        self.max_jobs = max_jobs

    async def create_plan(self, objective: str, context: str | None = None) -> DynamicPlan:
        response = await self.provider.generate(
            LLMRequest(
                system=(
                    "You are the planning agent for a multi-agent system. Decompose the objective "
                    "into independent specialist jobs that can run in parallel. Return ONLY valid JSON "
                    'with this shape: {"jobs":[{"name":"short-name","task":"specific task",'
                    '"system_prompt":"specialist role"}]}. Create 2 to 6 jobs.'
                ),
                prompt=f"OBJECTIVE:\n{objective}\n\nCONTEXT:\n{context or 'None'}",
            )
        )
        payload = self._parse_json(response)
        raw_jobs = payload.get("jobs") if isinstance(payload, dict) else None
        if not isinstance(raw_jobs, list) or not raw_jobs:
            raise ValueError("Planner did not return a non-empty jobs list")

        jobs: list[SpecialistJob] = []
        for index, item in enumerate(raw_jobs[: self.max_jobs], start=1):
            if not isinstance(item, dict):
                continue
            task = str(item.get("task", "")).strip()
            if not task:
                continue
            jobs.append(
                SpecialistJob(
                    name=str(item.get("name") or f"specialist-{index}").strip(),
                    task=task,
                    system_prompt=str(
                        item.get("system_prompt")
                        or "You are a specialist agent. Complete only the assigned task."
                    ).strip(),
                )
            )
        if not jobs:
            raise ValueError("Planner returned no usable specialist jobs")
        return DynamicPlan(jobs=jobs)

    @staticmethod
    def _parse_json(text: str) -> dict:
        value = text.strip()
        if value.startswith("```"):
            lines = value.splitlines()
            if lines and lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            value = "\n".join(lines).strip()
        start, end = value.find("{"), value.rfind("}")
        if start < 0 or end < start:
            raise ValueError("Planner response did not contain JSON")
        return json.loads(value[start : end + 1])


class FinalSynthesizer:
    def __init__(self, provider: LLMProvider):
        self.provider = provider

    async def synthesize(
        self,
        objective: str,
        results: list[SpecialistResult],
        verification: VerificationResult,
    ) -> str:
        joined = "\n\n".join(f"{r.name}:\n{r.output}" for r in results)
        return await self.provider.generate(
            LLMRequest(
                system=(
                    "You are the final synthesis agent. Produce one useful final answer to the user's "
                    "objective using the specialist results and verifier feedback. Do not mention internal "
                    "agent mechanics unless necessary."
                ),
                prompt=(
                    f"OBJECTIVE:\n{objective}\n\nSPECIALIST RESULTS:\n{joined}\n\n"
                    f"VERIFIER FEEDBACK:\n{verification.feedback}"
                ),
            )
        )


async def execute_phase5(objective: str, context: str | None = None) -> dict:
    provider = build_llm_provider()
    planner = LLMPlanner(provider, max_jobs=settings.max_jobs)
    plan = await planner.create_plan(objective, context)
    executor = ParallelAgentExecutor(
        provider,
        max_parallel=settings.max_parallel,
        max_retries=settings.max_retries,
    )
    results = await executor.run(plan.jobs)
    verifier = LLMVerifier(provider)
    verification = await verifier.verify(objective, results)
    final_answer = await FinalSynthesizer(provider).synthesize(objective, results, verification)
    return {
        "objective": objective,
        "plan": {"jobs": [asdict(job) for job in plan.jobs]},
        "results": [asdict(result) for result in results],
        "verification": asdict(verification),
        "final_answer": final_answer,
    }
