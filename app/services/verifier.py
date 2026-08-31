from app.models.orchestration import AgentJob, AgentResult, VerificationResult


class Verifier:
    def verify(self, jobs: list[AgentJob], results: list[AgentResult]) -> VerificationResult:
        received={r.job_id for r in results if r.success}
        issues=[f"Missing successful result for job {j.id}" for j in jobs if j.id not in received]
        return VerificationResult(passed=not issues, issues=issues)
