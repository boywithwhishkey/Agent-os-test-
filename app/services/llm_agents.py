from __future__ import annotations

import asyncio
from collections.abc import Iterable
from dataclasses import dataclass

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
    error: str | None = None

class ParallelAgentExecutor:
    def __init__(self, provider: LLMProvider, max_parallel: int = 3, max_retries: int = 2):
        self.provider = provider
        self.semaphore = asyncio.Semaphore(max_parallel)
        self.max_retries = max_retries

    async def _run_one(self, job: SpecialistJob) -> SpecialistResult:
        async with self.semaphore:
            last_error: Exception | None = None
            attempts = 0
            for attempt in range(1, self.max_retries + 2):
                attempts = attempt
                try:
                    output = await self.provider.generate(
                        LLMRequest(system=job.system_prompt, prompt=job.task)
                    )
                    if not output.strip():
                        raise ValueError("LLM returned an empty response")
                    return SpecialistResult(job.name, output, attempt)
                except asyncio.CancelledError:
                    raise
                except Exception as exc:  # noqa: BLE001 - isolated per specialist, see run()
                    last_error = exc
            return SpecialistResult(
                job.name,
                "",
                attempts,
                error=f"{type(last_error).__name__}: {last_error}",
            )

    async def run(self, jobs: Iterable[SpecialistJob]) -> list[SpecialistResult]:
        """Runs specialists in parallel; one specialist's exhausted retries does not
        abort the others — failures surface as a result with `error` set."""
        return list(await asyncio.gather(*(self._run_one(job) for job in jobs)))
