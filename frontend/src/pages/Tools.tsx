import { useMemo, useState } from "react";
import { Wrench, PlayCircle, ShieldCheck, Copy } from "lucide-react";
import { PageHeader } from "@/components/ui/PageHeader";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Input, Label, Select, Textarea, FieldError } from "@/components/ui/Input";
import { Badge } from "@/components/ui/Badge";
import { EmptyState, ErrorState, LoadingState } from "@/components/ui/States";
import { SkeletonRows } from "@/components/ui/Skeleton";
import { JSONViewer } from "@/components/ui/JSONViewer";
import { useTools, useExecuteTool, useIssueApproval } from "@/lib/api/queries";
import { useToast } from "@/components/ui/Toast";
import type { ToolRisk } from "@/lib/types";

const riskTone: Record<ToolRisk, "green" | "amber" | "red"> = {
  read: "green",
  write: "amber",
  high_risk: "red",
};

export default function Tools() {
  const tools = useTools();
  const executeTool = useExecuteTool();
  const issueApproval = useIssueApproval();
  const { push } = useToast();

  const [selectedTool, setSelectedTool] = useState("");
  const [argsText, setArgsText] = useState("{}");
  const [argsError, setArgsError] = useState<string | undefined>();
  const [approvalId, setApprovalId] = useState("");
  const [approvedBy, setApprovedBy] = useState("");
  const [reason, setReason] = useState("");

  const selected = useMemo(() => tools.data?.find((t) => t.name === selectedTool), [tools.data, selectedTool]);

  const runTool = () => {
    let parsedArgs: Record<string, unknown> = {};
    try {
      parsedArgs = argsText.trim() ? JSON.parse(argsText) : {};
      setArgsError(undefined);
    } catch {
      setArgsError("Arguments must be valid JSON");
      return;
    }
    executeTool.mutate({ call: { tool: selectedTool, arguments: parsedArgs }, approvalId: approvalId || undefined });
  };

  const issue = () => {
    if (!selectedTool || !approvedBy) {
      push({ tone: "error", title: "Tool and approver are required" });
      return;
    }
    issueApproval.mutate(
      { tool: selectedTool, approved_by: approvedBy, reason: reason || undefined },
      {
        onSuccess: (grant) => {
          setApprovalId(grant.approval_id);
          push({ tone: "success", title: "Approval issued", description: "One-time use — applied below." });
        },
        onError: (error) => push({ tone: "error", title: "Could not issue approval", description: (error as Error).message }),
      }
    );
  };

  return (
    <div className="space-y-6">
      <PageHeader
        title="Tools"
        description="Browse the tool registry, issue trusted (single-use) approvals for write/high-risk tools, and execute them safely."
      />

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Wrench className="h-4 w-4 text-accent-gold" /> Tool registry
          </CardTitle>
        </CardHeader>
        <CardContent>
          {tools.isLoading ? (
            <SkeletonRows rows={4} />
          ) : tools.isError ? (
            <ErrorState error={tools.error} onRetry={() => tools.refetch()} />
          ) : !tools.data?.length ? (
            <EmptyState title="No tools registered" />
          ) : (
            <ul className="divide-y divide-surface">
              {tools.data.map((tool) => (
                <li key={tool.name} className="flex items-center justify-between gap-3 py-2.5">
                  <div className="min-w-0">
                    <p className="truncate text-sm font-medium text-content-primary">{tool.name}</p>
                    <p className="truncate text-xs text-content-muted">{tool.description}</p>
                  </div>
                  <Badge tone={riskTone[tool.risk]} className="capitalize shrink-0">
                    {tool.risk.replace("_", " ")}
                  </Badge>
                </li>
              ))}
            </ul>
          )}
        </CardContent>
      </Card>

      <div className="grid gap-4 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <ShieldCheck className="h-4 w-4 text-accent-gold" /> Issue approval
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <div>
              <Label htmlFor="approval-tool">Tool</Label>
              <Select id="approval-tool" value={selectedTool} onChange={(e) => setSelectedTool(e.target.value)}>
                <option value="">Select a tool…</option>
                {tools.data?.map((t) => (
                  <option key={t.name} value={t.name}>
                    {t.name}
                  </option>
                ))}
              </Select>
            </div>
            <div>
              <Label htmlFor="approved-by">Approved by</Label>
              <Input id="approved-by" value={approvedBy} onChange={(e) => setApprovedBy(e.target.value)} placeholder="you@example.com" />
            </div>
            <div>
              <Label htmlFor="reason">Reason (optional)</Label>
              <Input id="reason" value={reason} onChange={(e) => setReason(e.target.value)} />
            </div>
            <Button onClick={issue} loading={issueApproval.isPending} variant="secondary">
              Issue single-use approval
            </Button>
            {approvalId && (
              <div className="flex items-center justify-between gap-2 rounded-lg border border-accent-green/25 bg-accent-green/5 px-3 py-2">
                <span className="truncate font-mono text-xs text-content-secondary">{approvalId}</span>
                <Button variant="ghost" size="sm" onClick={() => navigator.clipboard.writeText(approvalId)}>
                  <Copy className="h-3.5 w-3.5" />
                </Button>
              </div>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <PlayCircle className="h-4 w-4 text-accent-gold" /> Execute tool
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <div>
              <Label htmlFor="exec-tool">Tool</Label>
              <Select id="exec-tool" value={selectedTool} onChange={(e) => setSelectedTool(e.target.value)}>
                <option value="">Select a tool…</option>
                {tools.data?.map((t) => (
                  <option key={t.name} value={t.name}>
                    {t.name}
                  </option>
                ))}
              </Select>
            </div>
            {selected && selected.risk !== "read" && (
              <div>
                <Label htmlFor="approval-id">Approval ID</Label>
                <Input id="approval-id" value={approvalId} onChange={(e) => setApprovalId(e.target.value)} placeholder="Required for write/high-risk tools" />
              </div>
            )}
            <div>
              <Label htmlFor="args">Arguments (JSON)</Label>
              <Textarea id="args" value={argsText} onChange={(e) => setArgsText(e.target.value)} rows={4} className="font-mono text-xs" />
              <FieldError>{argsError}</FieldError>
            </div>
            <Button onClick={runTool} loading={executeTool.isPending} disabled={!selectedTool}>
              Execute
            </Button>

            {executeTool.isPending && <LoadingState label="Executing…" />}
            {executeTool.isError && <ErrorState error={executeTool.error} onRetry={runTool} />}
            {executeTool.data && (
              <div className="space-y-2">
                <div className="flex items-center gap-2">
                  <Badge tone={executeTool.data.success ? "green" : "red"}>
                    {executeTool.data.success ? "Success" : "Failed"}
                  </Badge>
                  {executeTool.data.approval_required && <Badge tone="amber">Approval required</Badge>}
                </div>
                <JSONViewer data={executeTool.data} collapsedByDefault={false} />
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
