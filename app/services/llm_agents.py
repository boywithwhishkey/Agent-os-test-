from __future__ import annotations
import asyncio
from dataclasses import dataclass
from typing import Iterable

from app.llm.base import LLMProvider, LLMRequest

@dataclass(slots=True)
class SpecialistJob:
    name: str
    task: str
    system_prompt: str = "You are a specialist agent. Complete only the assigned task."

@dataclass(slots=True)
class SpecialistResult:
    name: str
    output: str
    attempts: int

class ParallelAgentExecutor:
    def __init__(self, provider: LLMProvider, max_parallel: int = 3, max_retries: int = 2):
        self.provider = provider
        self.semaphore = asyncio.Semaphore(max_parallel)
        self.max_retries = max_retries

    async def _run_one(self, job: SpecialistJob) -> SpecialistResult:
        async with self.semaphore:
            last_error: Exception | None = None
            for attempt in range(1, self.max_retries + 2):
                try:
                    output = await self.provider.generate(
                        LLMRequest(system=job.system_prompt, prompt=job.task)
                    )
                    if not output.strip():
                        raise ValueError("LLM returned an empty response")
                    return SpecialistResult(job.name, output, attempt)
                except Exception as exc:
                    last_error = exc
            raise RuntimeError(
                f"Specialist {job.name!r} failed after retries"
            ) from last_error

    async def run(self, jobs: Iterable[SpecialistJob]) -> list[SpecialistResult]:
        return list(await asyncio.gather(*(self._run_one(job) for job in jobs)))
