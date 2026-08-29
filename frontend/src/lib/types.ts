// Types mirror backend Pydantic contracts exactly (app/models, app/*/models.py).
// Do not add fields the backend does not return.

export type TaskStatus = "pending" | "running" | "completed" | "failed";
export type TaskPriority = "low" | "normal" | "high" | "critical";

export interface Task {
  id: string;
  objective: string;
  priority: TaskPriority;
  status: TaskStatus;
  project_id: string | null;
  created_at: string;
}

export interface TaskCreate {
  objective: string;
  priority?: TaskPriority;
  project_id?: string | null;
}

// --- Orchestration ---
export type AgentRole = "researcher" | "builder" | "reviewer";

export interface AgentJob {
  id: string;
  role: AgentRole;
  instruction: string;
}

export interface ExecutionPlan {
  jobs: AgentJob[];
}

export interface AgentResult {
  job_id: string;
  role: AgentRole;
  success: boolean;
  output: string;
}

export interface VerificationResultOrchestration {
  passed: boolean;
  issues: string[];
}

export interface OrchestrationRequest {
  objective: string;
  context?: string | null;
}

export interface OrchestrationResult {
  objective: string;
  plan: ExecutionPlan;
  results: AgentResult[];
  verification: VerificationResultOrchestration;
}

// --- Autonomous (phase5) ---
export interface AutonomousRunRequest {
  objective: string;
  context?: string | null;
  project_id?: string | null;
  task_id?: string | null;
  session_id?: string | null;
}

export interface SpecialistJob {
  name: string;
  task: string;
  system_prompt: string;
}

export interface SpecialistResult {
  name: string;
  output: string;
  attempts: number;
  error: string | null;
}

export interface AutonomousVerification {
  approved: boolean;
  feedback: string;
}

export interface AutonomousRunResult {
  objective: string;
  plan: { jobs: SpecialistJob[] };
  results: SpecialistResult[];
  verification: AutonomousVerification;
  final_answer: string;
}

// --- Memory ---
export type MemoryScope = "session" | "task" | "project" | "decision" | "agent_run";

export interface MemoryRecord {
  id: string;
  scope: MemoryScope;
  key: string;
  content: string;
  project_id: string | null;
  task_id: string | null;
  session_id: string | null;
  agent: string | null;
  tags: string[];
  metadata: Record<string, unknown>;
  importance: number;
  created_at: string;
  score: number | null;
  semantic_score: number | null;
  lexical_score: number | null;
}

export interface MemoryWrite {
  scope: MemoryScope;
  key: string;
  content: string;
  project_id?: string | null;
  task_id?: string | null;
  session_id?: string | null;
  agent?: string | null;
  tags?: string[];
  metadata?: Record<string, unknown>;
  importance?: number;
}

export interface MemoryQuery {
  query?: string | null;
  scopes?: MemoryScope[];
  project_id?: string | null;
  task_id?: string | null;
  session_id?: string | null;
  agent?: string | null;
  tags?: string[];
  limit?: number;
}

export interface MemoryContext {
  records: MemoryRecord[];
  rendered: string;
}

// --- Workflows ---
export type StepType = "noop" | "tool" | "agent" | "integration";
export type StepStatus =
  | "pending"
  | "running"
  | "completed"
  | "failed"
  | "skipped"
  | "waiting_approval";
export type WorkflowStatus = "pending" | "running" | "paused" | "completed" | "failed";

export interface WorkflowStep {
  id: string;
  type: StepType;
  depends_on: string[];
  input: Record<string, unknown>;
  condition_key?: string | null;
  condition_equals?: unknown;
  max_retries: number;
  timeout_seconds: number;
}

export interface WorkflowDefinition {
  id: string;
  name: string;
  steps: WorkflowStep[];
}

export interface StepRun {
  step_id: string;
  status: StepStatus;
  attempts: number;
  output: unknown;
  error: string | null;
  approval_id: string | null;
}

export interface WorkflowRun {
  id: string;
  workflow_id: string;
  status: WorkflowStatus;
  context: Record<string, unknown>;
  steps: Record<string, StepRun>;
}

// --- Tools ---
export type ToolRisk = "read" | "write" | "high_risk";

export interface ToolInfo {
  name: string;
  description: string;
  risk: ToolRisk;
}

export interface ToolCall {
  tool: string;
  arguments: Record<string, unknown>;
}

export interface ToolExecutionResult {
  tool: string;
  success: boolean;
  risk: ToolRisk;
  output: unknown;
  error: string | null;
  approval_required: boolean;
  approval_id: string | null;
}

export interface ApprovalGrant {
  approval_id: string;
  tool: string;
  approved_by: string;
  reason: string | null;
}

export interface ToolAuditEvent {
  timestamp: string;
  tool: string;
  success: boolean;
  risk: string;
  approval_required: boolean;
  error: string | null;
}

// --- Runtime ---
export type ExecutionStatus = "pending" | "running" | "succeeded" | "failed" | "rejected";

export interface RuntimeRequest {
  provider: string;
  workflow: string;
  payload?: Record<string, unknown>;
  idempotency_key?: string | null;
  correlation_id?: string | null;
  timeout_seconds?: number;
  max_retries?: number;
}

export interface RuntimeExecution {
  id: string;
  provider: string;
  workflow: string;
  status: ExecutionStatus;
  attempts: number;
  correlation_id: string | null;
  idempotency_key: string | null;
  data: unknown;
  error: string | null;
  created_at: string;
  updated_at: string;
}

export interface CircuitBreakerStatus {
  state: "closed" | "open";
  failures: number;
  recovers_in_seconds: number | null;
}

export interface RateLimitStatus {
  used: number;
  limit: number;
  window_seconds: number;
}

export interface RuntimeStatus {
  provider: string;
  workflow: string;
  circuit_breaker: CircuitBreakerStatus;
  rate_limit: RateLimitStatus;
}

// --- Integrations ---
export interface IntegrationRequest {
  workflow: string;
  payload?: Record<string, unknown>;
  correlation_id?: string | null;
  timeout_seconds?: number;
}

export interface IntegrationResult {
  provider: string;
  workflow: string;
  success: boolean;
  status_code: number | null;
  data: unknown;
  error: string | null;
  correlation_id: string | null;
}

export interface IntegrationStatus {
  provider: string;
  name: string;
  configured: boolean;
  requires: string[];
  connected: boolean | null;
  last_check: string | null;
  last_check_latency_ms: number | null;
  last_check_error: string | null;
  last_execution: string | null;
  last_execution_success: boolean | null;
}

// --- System ---
export interface HealthResponse {
  status: string;
  service: string;
  environment: string;
  llm_provider: string;
  backends: Record<string, string>;
}

export interface ReadinessResponse {
  status: "ready" | "degraded";
  checks: Record<string, "ok" | "unconfigured" | "unavailable">;
}
