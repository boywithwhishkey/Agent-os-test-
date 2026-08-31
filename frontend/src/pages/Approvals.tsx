import { useState } from "react";
import { ShieldCheck, Info, Copy } from "lucide-react";
import { PageHeader } from "@/components/ui/PageHeader";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Input, Label, Select } from "@/components/ui/Input";
import { Badge } from "@/components/ui/Badge";
import { EmptyState } from "@/components/ui/States";
import { useTools, useIssueApproval } from "@/lib/api/queries";
import { useSessionHistory, recordHistory } from "@/lib/session-history";
import { useToast } from "@/components/ui/Toast";
import { formatDateTime } from "@/lib/utils";

export default function Approvals() {
  const tools = useTools();
  const issueApproval = useIssueApproval();
  const history = useSessionHistory("approval");
  const { push } = useToast();

  const [tool, setTool] = useState("");
  const [approvedBy, setApprovedBy] = useState("");
  const [reason, setReason] = useState("");

  const writeOrHighRiskTools = tools.data?.filter((t) => t.risk !== "read") ?? [];

  const issue = () => {
    if (!tool || !approvedBy) {
      push({ tone: "error", title: "Tool and approver are required" });
      return;
    }
    issueApproval.mutate(
      { tool, approved_by: approvedBy, reason: reason || undefined },
      {
        onSuccess: (grant) => {
          recordHistory("approval", {
            id: grant.approval_id,
            label: `${grant.tool} · approved by ${grant.approved_by}`,
            createdAt: new Date().toISOString(),
          });
          push({ tone: "success", title: "Approval issued", description: grant.approval_id });
          setReason("");
        },
        onError: (error) => push({ tone: "error", title: "Could not issue approval", description: (error as Error).message }),
      }
    );
  };

  return (
    <div className="space-y-6">
      <PageHeader
        title="Approval Center"
        description="THYNACT uses single-use, pre-authorized approval grants rather than a pending-request queue."
      />

      <Card className="border-accent-gold-soft/25 bg-accent-gold-soft/5">
        <CardContent className="flex items-start gap-3 pt-5">
          <Info className="mt-0.5 h-4 w-4 shrink-0 text-accent-gold-soft" />
          <p className="text-sm text-content-secondary">
            There is no "pending approval" queue in this backend — a grant is issued proactively for a
            specific tool, then consumed exactly once the next time that tool is executed with
            write or high-risk access. Grants shown below are this session's real issued grants;
            once used, the same ID cannot be reused.
          </p>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <ShieldCheck className="h-4 w-4 text-accent-gold" /> Issue a trusted approval
          </CardTitle>
        </CardHeader>
        <CardContent className="grid gap-3 sm:grid-cols-3">
          <div>
            <Label htmlFor="tool">Tool</Label>
            <Select id="tool" value={tool} onChange={(e) => setTool(e.target.value)}>
              <option value="">Select a tool…</option>
              {writeOrHighRiskTools.map((t) => (
                <option key={t.name} value={t.name}>
                  {t.name} ({t.risk.replace("_", " ")})
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
          <div className="sm:col-span-3">
            <Button onClick={issue} loading={issueApproval.isPending}>
              Issue approval
            </Button>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>This session's grants</CardTitle>
        </CardHeader>
        <CardContent>
          {history.length === 0 ? (
            <EmptyState
              icon={<ShieldCheck className="h-5 w-5" />}
              title="No approvals issued yet"
              description="Grants you issue above will be listed here for quick reuse in the Tools page."
            />
          ) : (
            <ul className="divide-y divide-surface">
              {history.map((entry) => (
                <li key={entry.id} className="flex items-center justify-between gap-3 py-2.5">
                  <div className="min-w-0">
                    <p className="truncate text-sm font-medium text-content-primary">{entry.label}</p>
                    <p className="font-mono text-xs text-content-muted">{entry.id}</p>
                    <p className="text-xs text-content-muted">{formatDateTime(entry.createdAt)}</p>
                  </div>
                  <div className="flex items-center gap-2 shrink-0">
                    <Badge tone="amber">Single-use</Badge>
                    <Button variant="ghost" size="sm" onClick={() => navigator.clipboard.writeText(entry.id)}>
                      <Copy className="h-3.5 w-3.5" />
                    </Button>
                  </div>
                </li>
              ))}
            </ul>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
