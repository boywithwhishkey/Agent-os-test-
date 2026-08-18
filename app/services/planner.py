from uuid import uuid4
from app.models.orchestration import AgentJob, AgentRole, ExecutionPlan, OrchestrationRequest

class Planner:
    def create_plan(self, request: OrchestrationRequest) -> ExecutionPlan:
        o=request.objective.strip()
        return ExecutionPlan(jobs=[
            AgentJob(id=str(uuid4()), role=AgentRole.RESEARCHER, instruction=f"Analyze requirements and risks for: {o}"),
            AgentJob(id=str(uuid4()), role=AgentRole.BUILDER, instruction=f"Produce an implementation approach for: {o}"),
            AgentJob(id=str(uuid4()), role=AgentRole.REVIEWER, instruction=f"Define acceptance checks for: {o}")
        ])
