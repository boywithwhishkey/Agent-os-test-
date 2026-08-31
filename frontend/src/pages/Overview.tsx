import { Link } from "react-router-dom";
import {
  Brain,
  Workflow,
  Wrench,
  ShieldCheck,
  Database,
  Activity,
  Plug,
  ScrollText,
  Users,
  ArrowRight,
  Lock,
  Gauge,
} from "lucide-react";
import { Card, CardContent } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { BrandMark, BRAND_TAGLINE } from "@/components/ui/BrandMark";
import { ScrollReveal, StaggerGroup, StaggerItem } from "@/components/ui/ScrollReveal";

/**
 * The product overview: what THYNACT actually does, written from the shipped
 * surface rather than a roadmap. Every capability listed here maps to a real
 * route in this app and a real endpoint on the API — nothing aspirational is
 * presented as available, because a capabilities page that overstates is worse
 * than none at all.
 */

const PILLARS = [
  {
    icon: Brain,
    title: "Reason before it acts",
    body: "Every request is routed by complexity, confidence and risk. Simple asks stay on a fast deterministic path; only work that genuinely needs planning or multiple specialists pays for it.",
    to: "/orchestrate",
    action: "Orchestrate",
  },
  {
    icon: Users,
    title: "Three-role orchestration",
    body: "Researcher, builder and reviewer run as a coordinated plan with a real parallelism limit, so complex objectives are decomposed and checked rather than answered in one pass.",
    to: "/autonomous",
    action: "Autonomous runs",
  },
  {
    icon: Workflow,
    title: "Durable workflow engine",
    body: "A visual DAG builder with dependency validation, retries, timeouts, conditions and approval gates. Runs are persisted and can be resumed past a pause.",
    to: "/workflows",
    action: "Build a workflow",
  },
  {
    icon: Wrench,
    title: "Governed tool execution",
    body: "Tools carry a risk level. Read tools run freely; write and high-risk tools require a single-use approval grant that cannot be self-issued by the model.",
    to: "/tools",
    action: "Tool registry",
  },
  {
    icon: Database,
    title: "Semantic + lexical memory",
    body: "Hybrid retrieval over pgvector with real relevance scoring — semantic similarity, lexical match and an importance weight — not a keyword search wearing a new name.",
    to: "/memory",
    action: "Search memory",
  },
  {
    icon: Activity,
    title: "Runtime you can see",
    body: "Circuit breakers, sliding-window rate limits, bounded retries and idempotency keys, each with live state you can inspect instead of inferring from logs.",
    to: "/runtime",
    action: "Runtime status",
  },
];

const GOVERNANCE = [
  {
    icon: ShieldCheck,
    title: "Model intelligence is not authority",
    body: "Capability never implies permission. Send, publish, delete, purchase, refund, spend, deploy and admin changes pass through policy and, where required, explicit approval.",
  },
  {
    icon: ScrollText,
    title: "Every execution is audited",
    body: "Tool runs record the tool, risk, outcome, approval requirement and the correlation ID of the request that caused them — so any action traces back to its origin.",
  },
  {
    icon: Lock,
    title: "Untrusted content stays data",
    body: "Text returned by emails, web pages, documents, connectors or MCP tools is treated as data, never as instructions. An unknown MCP tool is denied by default.",
  },
  {
    icon: Gauge,
    title: "Honest capability states",
    body: "A connector is not \"working\" because an adapter or a card exists. Each one reports live-validated, credential-required or not-implemented — and nothing is inflated.",
  },
];

export default function Overview() {
  return (
    <div className="space-y-10 pb-8">
      {/* Hero — the one brand moment on this page. */}
      <section className="relative overflow-hidden pt-2">
        <div
          className="pointer-events-none absolute -top-24 right-0 h-64 w-64 rounded-full bg-accent-gold/[0.10] blur-[100px] animate-float"
          aria-hidden
        />
        <StaggerGroup className="flex flex-col gap-5">
          <StaggerItem>
            <BrandMark variant="compact" size="lg" />
          </StaggerItem>
          <StaggerItem>
            <h1 className="max-w-3xl text-3xl font-semibold leading-tight tracking-tight text-content-primary sm:text-4xl">
              An agent platform that thinks first, then acts under your control.
            </h1>
          </StaggerItem>
          <StaggerItem>
            <p className="max-w-2xl text-base leading-relaxed text-content-secondary">
              {BRAND_TAGLINE} THYNACT plans, delegates, verifies and executes — with every
              consequential action gated by policy, recorded in an audit trail, and traceable
              back to the request that caused it.
            </p>
          </StaggerItem>
          <StaggerItem>
            <div className="flex flex-wrap items-center gap-2.5">
              <Link to="/orchestrate">
                <Button size="lg">
                  Start an orchestration <ArrowRight className="h-4 w-4" />
                </Button>
              </Link>
              <Link to="/integrations">
                <Button variant="outline" size="lg">
                  Browse connectors
                </Button>
              </Link>
            </div>
          </StaggerItem>
        </StaggerGroup>
      </section>

      {/* Capabilities */}
      <ScrollReveal>
        <section className="space-y-4">
          <div className="flex items-baseline justify-between gap-3">
            <h2 className="text-lg font-semibold text-content-primary">What it does</h2>
            <span className="hidden shrink-0 text-xs uppercase tracking-wider text-content-muted sm:inline">
              Every item links to the live surface
            </span>
          </div>
          <StaggerGroup className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3">
            {PILLARS.map((p) => (
              <StaggerItem key={p.title} className="h-full">
                <Card className="group h-full transition-transform duration-200 hover:-translate-y-0.5">
                  <CardContent className="flex h-full flex-col gap-3">
                    <span className="flex h-10 w-10 items-center justify-center rounded-xl border border-hairline bg-accent-gold/[0.08] text-accent-gold transition-colors group-hover:border-accent-gold/30">
                      <p.icon className="h-5 w-5" />
                    </span>
                    <h3 className="text-sm font-semibold text-content-primary">{p.title}</h3>
                    <p className="flex-1 text-sm leading-relaxed text-content-secondary">{p.body}</p>
                    <Link
                      to={p.to}
                      className="focus-ring inline-flex items-center gap-1.5 rounded text-sm font-medium text-accent-gold transition-opacity hover:opacity-80"
                    >
                      {p.action} <ArrowRight className="h-3.5 w-3.5" />
                    </Link>
                  </CardContent>
                </Card>
              </StaggerItem>
            ))}
          </StaggerGroup>
        </section>
      </ScrollReveal>

      {/* Governance — the differentiator, and the reason to trust it. */}
      <ScrollReveal>
        <section className="space-y-4">
          <div className="space-y-1">
            <h2 className="text-lg font-semibold text-content-primary">How it stays trustworthy</h2>
            <p className="max-w-2xl text-sm text-content-secondary">
              Autonomy is only useful if it is bounded. These are enforced in code, not described
              in a policy document.
            </p>
          </div>
          <div className="grid grid-cols-1 gap-3 md:grid-cols-2">
            {GOVERNANCE.map((g) => (
              <Card key={g.title}>
                <CardContent className="flex gap-3.5">
                  <span className="mt-0.5 flex h-9 w-9 shrink-0 items-center justify-center rounded-lg border border-hairline text-accent-gold">
                    <g.icon className="h-4 w-4" />
                  </span>
                  <div className="min-w-0 space-y-1">
                    <h3 className="text-sm font-semibold text-content-primary">{g.title}</h3>
                    <p className="text-sm leading-relaxed text-content-secondary">{g.body}</p>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </section>
      </ScrollReveal>

      {/* Connectors — stated honestly, with the real numbers. */}
      <ScrollReveal>
        <Card>
          <CardContent className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
            <div className="min-w-0 space-y-1.5">
              <div className="flex flex-wrap items-center gap-2">
                <Plug className="h-4 w-4 text-accent-gold" />
                <h2 className="text-sm font-semibold text-content-primary">Connectors</h2>
                <Badge tone="neutral">MCP-first, not MCP-only</Badge>
              </div>
              <p className="max-w-xl text-sm leading-relaxed text-content-secondary">
                Providers are reached through a broker that prefers official MCP, then verified
                MCP, then a managed connector, then a native adapter. The Integrations page shows
                each one's real state — connected, credential required, or not implemented — rather
                than a count that flatters the product.
              </p>
            </div>
            <Link to="/integrations" className="shrink-0">
              <Button variant="outline">
                View integrations <ArrowRight className="h-4 w-4" />
              </Button>
            </Link>
          </CardContent>
        </Card>
      </ScrollReveal>
    </div>
  );
}
