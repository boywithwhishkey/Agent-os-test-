import { Link } from "react-router-dom";
import { Search, Hammer, Eye, ArrowUpRight, Info } from "lucide-react";
import { PageHeader } from "@/components/ui/PageHeader";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";

const roles = [
  {
    role: "researcher",
    icon: Search,
    description: "Gathers context and grounds the objective before any output is produced.",
  },
  {
    role: "builder",
    icon: Hammer,
    description: "Produces the primary output — code, plans, or content — from the research.",
  },
  {
    role: "reviewer",
    icon: Eye,
    description: "Verifies the builder's output and reports pass/fail with concrete issues.",
  },
];

export default function Agents() {
  return (
    <div className="space-y-6">
      <PageHeader
        title="Agents"
        description="THYNACT runs three fixed roles per orchestration, and dynamically named specialists per autonomous run."
      />

      <Card className="border-accent-gold-soft/25 bg-accent-gold-soft/5">
        <CardContent className="flex items-start gap-3 pt-5">
          <Info className="mt-0.5 h-4 w-4 shrink-0 text-accent-gold-soft" />
          <p className="text-sm text-content-secondary">
            Agent execution is only visible in the context of a run. Start an{" "}
            <Link to="/orchestrate" className="font-medium text-accent-gold-soft hover:underline">
              orchestration
            </Link>{" "}
            or an{" "}
            <Link to="/autonomous" className="font-medium text-accent-gold-soft hover:underline">
              autonomous run
            </Link>{" "}
            to see live agent activity, output, and verification.
          </p>
        </CardContent>
      </Card>

      <div className="grid gap-4 sm:grid-cols-3">
        {roles.map(({ role, icon: Icon, description }) => (
          <Card key={role}>
            <CardHeader>
              <CardTitle className="flex items-center gap-2 capitalize">
                <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-accent-gold/10 text-accent-gold">
                  <Icon className="h-4 w-4" />
                </span>
                {role}
              </CardTitle>
              <Badge tone="violet">Orchestration</Badge>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-content-secondary">{description}</p>
            </CardContent>
          </Card>
        ))}
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Autonomous specialists</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-content-secondary">
            Autonomous runs generate 2–6 specialist agents dynamically per objective, each with a
            planner-assigned name, task, and system prompt. Their status, output, and retry attempts
            are visible on each run.
          </p>
          <Link
            to="/autonomous"
            className="mt-3 inline-flex items-center gap-1 text-sm font-medium text-accent-gold hover:underline"
          >
            Go to Autonomous Runs <ArrowUpRight className="h-3.5 w-3.5" />
          </Link>
        </CardContent>
      </Card>
    </div>
  );
}
