from enum import Enum

from pydantic import BaseModel, Field


class AgentRole(str, Enum):
    RESEARCHER="researcher"
    BUILDER="builder"
    REVIEWER="reviewer"

class AgentJob(BaseModel):
    id: str
    role: AgentRole
    instruction: str

class ExecutionPlan(BaseModel):
    jobs: list[AgentJob] = Field(min_length=1)

class AgentResult(BaseModel):
    job_id: str
    role: AgentRole
    success: bool = True
    output: str

class VerificationResult(BaseModel):
    passed: bool
    issues: list[str] = []

class OrchestrationRequest(BaseModel):
    objective: str = Field(min_length=3)
    context: str | None = None

class OrchestrationResult(BaseModel):
    objective: str
    plan: ExecutionPlan
    results: list[AgentResult]
    verification: VerificationResult
