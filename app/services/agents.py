import asyncio
from app.models.orchestration import AgentJob, AgentResult
class AgentRegistry:
    async def execute(self, job: AgentJob) -> AgentResult:
        await asyncio.sleep(0)
        return AgentResult(job_id=job.id, role=job.role, output=f"{job.role.value} completed: {job.instruction}")
