from __future__ import annotations

from dataclasses import dataclass

from app.llm.base import LLMProvider, LLMRequest
from app.services.llm_agents import SpecialistResult


@dataclass(slots=True)
class VerificationResult:
    approved: bool
    feedback: str

class LLMVerifier:
    def __init__(self, provider: LLMProvider):
        self.provider = provider

    async def verify(self, objective: str, results: list[SpecialistResult]) -> VerificationResult:
        if not results or any(not r.output.strip() for r in results):
            return VerificationResult(False, "Missing specialist output.")

        joined = "\n\n".join(f"{r.name}: {r.output}" for r in results)
        response = await self.provider.generate(
            LLMRequest(
                system=(
                    "You are a verification agent. Review specialist work against the objective. "
                    "Start your reply with 'Approved' if the work satisfies the objective, or "
                    "'Rejected' if it does not, followed by a concise assessment."
                ),
                prompt=f"OBJECTIVE:\n{objective}\n\nRESULTS:\n{joined}",
            )
        )
        feedback = response.strip()
        approved = feedback.lower().startswith("approved")
        return VerificationResult(approved, feedback or "Verifier returned no feedback.")
