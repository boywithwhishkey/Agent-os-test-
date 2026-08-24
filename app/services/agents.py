from __future__ import annotations

from app.llm.base import LLMRequest
from app.llm.factory import build_llm_provider
from app.models.orchestration import AgentJob, AgentResult


class AgentRegistry:
    """Executes orchestration jobs through the configured LLM provider."""

    def __init__(self):
        self.provider = build_llm_provider()

    async def execute(self, job: AgentJob) -> AgentResult:
        system_prompt = (
            f"You are the {job.role.value} agent in a multi-agent orchestration system. "
            "Complete only the assigned task. Be concrete, concise, and actionable."
        )

        output = await self.provider.generate(
            LLMRequest(
                system=system_prompt,
                prompt=job.instruction,
            )
        )

        return AgentResult(
            job_id=job.id,
            role=job.role,
            success=True,
            output=output.strip(),
        )
