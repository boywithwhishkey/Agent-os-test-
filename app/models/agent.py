from enum import StrEnum

from pydantic import BaseModel, Field


class AgentRole(StrEnum):
    MASTER = "master"
    DEVELOPER = "developer"
    REVIEWER = "reviewer"
    RESEARCH = "research"
    DEVOPS = "devops"
    COMMUNICATION = "communication"


class AgentTaskRequest(BaseModel):
    task_id: str
    from_agent: AgentRole
    to_agent: AgentRole
    objective: str = Field(min_length=3)
    context: dict[str, object] = Field(default_factory=dict)
    expected_output: list[str] = Field(default_factory=list)


class AgentTaskResult(BaseModel):
    task_id: str
    agent: AgentRole
    status: str
    output: dict[str, object] = Field(default_factory=dict)
    requires_approval: bool = False
