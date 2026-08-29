import { useMutation, useQuery, useQueryClient, type UseQueryOptions } from "@tanstack/react-query";
import { api } from "./client";
import type {
  ApprovalGrant,
  AutonomousRunRequest,
  AutonomousRunResult,
  ConnectorEntry,
  HealthResponse,
  IntegrationRequest,
  IntegrationResult,
  IntegrationStatus,
  MCPServer,
  MCPServerCreate,
  MemoryContext,
  MemoryQuery,
  MemoryRecord,
  MemoryWrite,
  OrchestrationRequest,
  OrchestrationResult,
  ReadinessResponse,
  RuntimeExecution,
  RuntimeRequest,
  RuntimeStatus,
  Task,
  TaskCreate,
  ToolAuditEvent,
  ToolCall,
  ToolExecutionResult,
  ToolInfo,
  WorkflowDefinition,
  WorkflowRun,
} from "../types";

// ---------- System ----------
export function useHealth() {
  return useQuery({
    queryKey: ["health"],
    queryFn: () => api.get<HealthResponse>("/health", { skipAuth: true }),
    refetchInterval: 30_000,
    retry: 1,
  });
}

export function useReadiness() {
  return useQuery({
    queryKey: ["readiness"],
    queryFn: () => api.get<ReadinessResponse>("/ready", { skipAuth: true }),
    refetchInterval: 30_000,
    retry: 1,
  });
}

// ---------- Tasks ----------
export function useTask(taskId: string | undefined, options?: Partial<UseQueryOptions<Task>>) {
  return useQuery({
    queryKey: ["task", taskId],
    queryFn: () => api.get<Task>(`/api/v1/tasks/${taskId}`),
    enabled: Boolean(taskId),
    retry: false,
    ...options,
  });
}

export function useCreateTask() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: TaskCreate) => api.post<Task>("/api/v1/tasks", payload),
    onSuccess: (task) => {
      queryClient.setQueryData(["task", task.id], task);
    },
  });
}

// ---------- Orchestration ----------
export function useOrchestrate() {
  return useMutation({
    mutationFn: (payload: OrchestrationRequest) =>
      api.post<OrchestrationResult>("/api/v1/orchestrate", payload, { timeoutMs: 120_000 }),
  });
}

// ---------- Autonomous ----------
export function useAutonomousRun() {
  return useMutation({
    mutationFn: (payload: AutonomousRunRequest) =>
      api.post<AutonomousRunResult>("/api/v1/autonomous/run", payload, { timeoutMs: 150_000 }),
  });
}

// ---------- Memory ----------
export function useMemorySearch(query: MemoryQuery, options?: { enabled?: boolean }) {
  return useQuery({
    queryKey: ["memory", "search", query],
    queryFn: () => api.post<MemoryRecord[]>("/api/v1/memory/search", query),
    enabled: options?.enabled ?? true,
  });
}

export function useMemoryContext() {
  return useMutation({
    mutationFn: (query: MemoryQuery) => api.post<MemoryContext>("/api/v1/memory/context", query),
  });
}

export function useMemoryGet(memoryId: string | undefined) {
  return useQuery({
    queryKey: ["memory", memoryId],
    queryFn: () => api.get<MemoryRecord>(`/api/v1/memory/${memoryId}`),
    enabled: Boolean(memoryId),
  });
}

export function useWriteMemory() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: MemoryWrite) => api.post<MemoryRecord>("/api/v1/memory", payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["memory", "search"] });
    },
  });
}

export function useDeleteMemory() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (memoryId: string) => api.delete<void>(`/api/v1/memory/${memoryId}`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["memory", "search"] });
    },
  });
}

// ---------- Tools ----------
export function useTools() {
  return useQuery({
    queryKey: ["tools"],
    queryFn: () => api.get<ToolInfo[]>("/api/v1/tools"),
  });
}

export function useExecuteTool() {
  return useMutation({
    mutationFn: ({ call, approvalId }: { call: ToolCall; approvalId?: string }) =>
      api.post<ToolExecutionResult>("/api/v1/tools/execute", {
        call,
        approval_id: approvalId ?? null,
      }),
  });
}

export function useIssueApproval() {
  return useMutation({
    mutationFn: (payload: { tool: string; approved_by: string; reason?: string }) =>
      api.post<ApprovalGrant>("/api/v1/tools/approvals", payload),
  });
}

export function useToolAudit() {
  return useQuery({
    queryKey: ["tools", "audit"],
    queryFn: () => api.get<ToolAuditEvent[]>("/api/v1/tools/audit"),
    refetchInterval: 20_000,
  });
}

// ---------- Workflows ----------
export function useRunWorkflow() {
  return useMutation({
    mutationFn: (payload: { definition: WorkflowDefinition; context?: Record<string, unknown> }) =>
      api.post<WorkflowRun>("/api/v1/workflows/run", payload, { timeoutMs: 60_000 }),
  });
}

export function useResumeWorkflow() {
  return useMutation({
    mutationFn: ({ runId, approvals }: { runId: string; approvals: Record<string, string> }) =>
      api.post<WorkflowRun>(`/api/v1/workflows/runs/${runId}/resume`, { approvals }),
  });
}

export function useWorkflowRun(runId: string | undefined) {
  return useQuery({
    queryKey: ["workflow-run", runId],
    queryFn: () => api.get<WorkflowRun>(`/api/v1/workflows/runs/${runId}`),
    enabled: Boolean(runId),
    retry: false,
  });
}

// ---------- Runtime ----------
export function useExecuteRuntime() {
  return useMutation({
    mutationFn: (payload: RuntimeRequest) =>
      api.post<RuntimeExecution>("/api/v1/runtime/execute", payload, { timeoutMs: 60_000 }),
  });
}

export function useRuntimeExecution(executionId: string | undefined) {
  return useQuery({
    queryKey: ["runtime-execution", executionId],
    queryFn: () => api.get<RuntimeExecution>(`/api/v1/runtime/executions/${executionId}`),
    enabled: Boolean(executionId),
    retry: false,
  });
}

export function useRuntimeStatus(provider: string, workflow: string, options?: { enabled?: boolean }) {
  return useQuery({
    queryKey: ["runtime-status", provider, workflow],
    queryFn: () =>
      api.get<RuntimeStatus>(`/api/v1/runtime/status?provider=${encodeURIComponent(provider)}&workflow=${encodeURIComponent(workflow)}`),
    enabled: (options?.enabled ?? true) && Boolean(provider) && Boolean(workflow),
    refetchInterval: 15_000,
  });
}

// ---------- Integrations: unified connector catalog ----------
// Catalog reads are public on the backend (no operator API key required) so
// the Integration Hub renders for any visitor — only mutating actions below
// (test/execute/MCP create/test/delete) require auth and will 401 without it.
export function useConnectorCatalog() {
  return useQuery({
    queryKey: ["connector-catalog"],
    queryFn: () => api.get<ConnectorEntry[]>("/api/v1/integrations", { skipAuth: true }),
    refetchInterval: 30_000,
  });
}

export function useTestIntegration() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (provider: string) =>
      api.post<IntegrationStatus>(`/api/v1/integrations/${provider}/test`, undefined, { timeoutMs: 15_000 }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["connector-catalog"] });
    },
  });
}

export function useExecuteIntegration() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: { provider: string; request: IntegrationRequest }) =>
      api.post<IntegrationResult>("/api/v1/integrations/execute", payload, { timeoutMs: 60_000 }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["connector-catalog"] });
    },
  });
}

// ---------- Integrations: MCP servers ----------
export function useMCPServers() {
  return useQuery({
    queryKey: ["mcp-servers"],
    queryFn: () => api.get<MCPServer[]>("/api/v1/integrations/mcp/servers", { skipAuth: true }),
    refetchInterval: 30_000,
  });
}

export function useCreateMCPServer() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: MCPServerCreate) => api.post<MCPServer>("/api/v1/integrations/mcp/servers", payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["mcp-servers"] });
    },
  });
}

export function useTestMCPServer() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (serverId: string) =>
      api.post<MCPServer>(`/api/v1/integrations/mcp/servers/${serverId}/test`, undefined, { timeoutMs: 20_000 }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["mcp-servers"] });
    },
  });
}

// ---------------------------------------------------------------------------
// Integrations: OAuth2 authorize/callback flow
// ---------------------------------------------------------------------------
export function useOAuthAuthorize() {
  return useMutation({
    mutationFn: (provider: string) =>
      api.get<{ authorize_url: string }>(`/api/v1/integrations/oauth/${provider}/authorize`),
  });
}

export function useOAuthDisconnect() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (provider: string) => api.delete<void>(`/api/v1/integrations/oauth/${provider}`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["connector-catalog"] });
    },
  });
}

export function useDeleteMCPServer() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (serverId: string) => api.delete<void>(`/api/v1/integrations/mcp/servers/${serverId}`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["mcp-servers"] });
    },
  });
}
