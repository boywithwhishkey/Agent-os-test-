import asyncio
from app.models.orchestration import OrchestrationRequest, OrchestrationResult
from app.services.agents import AgentRegistry
from app.services.planner import Planner
from app.services.verifier import Verifier

class Orchestrator:
    def __init__(self):
        self.planner, self.registry, self.verifier = Planner(), AgentRegistry(), Verifier()

    async def run(self, request: OrchestrationRequest) -> OrchestrationResult:
        plan = self.planner.create_plan(request)
        results = list(await asyncio.gather(*(self.registry.execute(j) for j in plan.jobs)))
        return OrchestrationResult(objective=request.objective, plan=plan, results=results,
                                   verification=self.verifier.verify(plan.jobs, results))
