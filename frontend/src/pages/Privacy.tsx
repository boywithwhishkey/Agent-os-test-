import { Link } from "react-router-dom";
import { ShieldCheck, Database, Cookie, KeyRound, Share2, Clock, UserCheck, Mail, AlertTriangle } from "lucide-react";
import { Card, CardContent } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { PageHeader } from "@/components/ui/PageHeader";
import { ScrollReveal } from "@/components/ui/ScrollReveal";

/**
 * Privacy notice and operating policy.
 *
 * Written from what this codebase verifiably does — the tables in
 * `migrations/`, the browser storage keys in `lib/`, and the absence of any
 * analytics or advertising SDK — rather than from a generic template. Where a
 * commitment depends on how an operator deploys THYNACT, that is stated as a
 * condition rather than a promise.
 *
 * It is deliberately NOT presented as legal advice: the notice tells the
 * reader plainly that it needs review by a qualified adviser before it is
 * relied on for a jurisdiction, because a confidently-worded but unreviewed
 * policy is a liability, not a feature.
 */

const LAST_UPDATED = "31 August 2026";

function Section({
  icon: Icon,
  title,
  children,
}: {
  icon: React.ElementType;
  title: string;
  children: React.ReactNode;
}) {
  return (
    <ScrollReveal>
      <Card>
        <CardContent className="space-y-3">
          <div className="flex items-center gap-2.5">
            <span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg border border-hairline text-accent-gold">
              <Icon className="h-4 w-4" />
            </span>
            <h2 className="text-sm font-semibold text-content-primary">{title}</h2>
          </div>
          <div className="space-y-3 text-sm leading-relaxed text-content-secondary">{children}</div>
        </CardContent>
      </Card>
    </ScrollReveal>
  );
}

function DataRow({ what, where, why, keep }: { what: string; where: string; why: string; keep: string }) {
  return (
    <tr className="border-b border-hairline last:border-0">
      <td className="py-2.5 pr-3 align-top font-medium text-content-primary">{what}</td>
      <td className="py-2.5 pr-3 align-top text-content-secondary">{where}</td>
      <td className="py-2.5 pr-3 align-top text-content-secondary">{why}</td>
      <td className="py-2.5 align-top text-content-muted">{keep}</td>
    </tr>
  );
}

export default function Privacy() {
  return (
    <div className="space-y-4 pb-8">
      <PageHeader
        title="Privacy & Policy"
        description="What THYNACT stores, where it goes, and the rules the system holds itself to."
      />

      <ScrollReveal>
        <Card>
          <CardContent className="flex flex-wrap items-center gap-x-3 gap-y-2 text-sm">
            <Badge tone="neutral">Last updated {LAST_UPDATED}</Badge>
            <span className="text-content-muted">
              Applies to the THYNACT Control Center and its API.
            </span>
          </CardContent>
        </Card>
      </ScrollReveal>

      <Section icon={AlertTriangle} title="Read this first">
        <p>
          This notice describes how this software behaves, verified against its own source: the
          database tables it creates, the browser storage keys it writes, and the third-party
          scripts it loads (there are none). It is written to be accurate, not reassuring.
        </p>
        <p>
          It is <strong className="text-content-primary">not legal advice</strong> and has not been
          reviewed by a lawyer. Before relying on it as your public privacy policy — particularly
          under the GDPR, the UK GDPR, the DPDP Act or CCPA/CPRA — have a qualified adviser review
          it against how you actually deploy and operate the platform.
        </p>
      </Section>

      <Section icon={Database} title="What is stored, and where">
        <p>
          THYNACT stores operational data needed to run and audit agent work. When an operator
          configures durable storage, the following live in that operator's own PostgreSQL
          database — not in any service run by us:
        </p>
        {/* The table has four columns of real content and cannot usefully
            compress to 390px, so it scrolls inside its own container. Without
            a hint the cut-off right edge reads as broken rather than
            scrollable, so say so on the widths where it actually happens. */}
        <p className="text-xs text-content-muted sm:hidden">Scroll the table sideways to see why and retention.</p>
        <div className="-mx-1 overflow-x-auto">
          <table className="w-full min-w-[640px] text-sm">
            <thead>
              <tr className="border-b border-hairline text-left text-xs uppercase tracking-wider text-content-muted">
                <th className="py-2 pr-3 font-medium">Data</th>
                <th className="py-2 pr-3 font-medium">Where</th>
                <th className="py-2 pr-3 font-medium">Why</th>
                <th className="py-2 font-medium">Retention</th>
              </tr>
            </thead>
            <tbody>
              <DataRow
                what="Tasks & objectives"
                where="tasks"
                why="The work you asked the system to do"
                keep="Until deleted by the operator"
              />
              <DataRow
                what="Workflow definitions & runs"
                where="workflow_definitions, workflow_runs"
                why="Reproducing and resuming multi-step work"
                keep="Until deleted by the operator"
              />
              <DataRow
                what="Runtime executions"
                where="runtime_executions"
                why="Retry, idempotency and circuit-breaker state"
                keep="Until deleted by the operator"
              />
              <DataRow
                what="Agent memory"
                where="agent_memories"
                why="Semantic + lexical recall, including embeddings"
                keep="Until deleted from the Memory page"
              />
              <DataRow
                what="Approvals"
                where="tool_approvals"
                why="Proving a risky action was authorised"
                keep="Single-use; the record persists"
              />
              <DataRow
                what="Audit events"
                where="tool_audit_events"
                why="Which tool ran, its outcome, and the request that caused it"
                keep="Append-only; retained for accountability"
              />
            </tbody>
          </table>
        </div>
        <p>
          If durable storage is <em>not</em> configured, all of the above lives only in the API
          process's memory and is lost on every restart. The System Health page states which mode
          a deployment is actually in — it is never implied to be durable when it is not.
        </p>
      </Section>

      <Section icon={Cookie} title="Cookies and tracking">
        <p>
          <strong className="text-content-primary">
            This application sets no cookies and loads no analytics, advertising or session-replay
            scripts.
          </strong>{" "}
          There is no Google Analytics, no tag manager, no pixel, no third-party telemetry. Nothing
          about your use of the interface is sent to anyone but the API you point it at.
        </p>
        <p>The interface keeps four values in your own browser, and nowhere else:</p>
        <ul className="ml-4 list-disc space-y-1.5">
          <li>
            <span className="font-mono text-xs text-content-primary">agent-os:api-key</span> — your
            operator key, in <strong className="text-content-primary">sessionStorage</strong> only,
            so it is discarded when the tab closes. It is never written to disk, never logged, and
            never bundled into the JavaScript.
          </li>
          <li>
            <span className="font-mono text-xs text-content-primary">agent-os:api-base-url</span> —
            which API this interface talks to.
          </li>
          <li>
            <span className="font-mono text-xs text-content-primary">agent-os:session-history</span>{" "}
            — IDs of items you created this session, so they are not lost. Cleared with the tab.
          </li>
          <li>
            <span className="font-mono text-xs text-content-primary">agent-os:theme</span> — your
            light/dark preference.
          </li>
        </ul>
        <p>
          Clearing site data, or using “Clear session” in the account menu, removes all four
          immediately.
        </p>
      </Section>

      <Section icon={KeyRound} title="Credentials and secrets">
        <p>
          Provider credentials are held as references, not printed. The platform is built so that
          API keys, tokens, refresh tokens, client secrets and database passwords are never written
          to model output, terminal logs, audit payloads or source control — only their{" "}
          <em>names</em> appear.
        </p>
        <p>
          OAuth access tokens obtained through the connector flow are held in the API process's
          memory and are not persisted to the database. They are therefore dropped on restart and
          reconnection is required. This is a deliberate current limitation:{" "}
          <strong className="text-content-primary">
            persisting them would require encryption at rest and a key-management decision that has
            not yet been made
          </strong>
          , and storing them in cleartext would be worse than losing them.
        </p>
      </Section>

      <Section icon={Share2} title="Who your data is shared with">
        <p>
          THYNACT does not sell data and has no advertising relationships. Data leaves a deployment
          only where you direct it:
        </p>
        <ul className="ml-4 list-disc space-y-1.5">
          <li>
            <strong className="text-content-primary">Model providers</strong> — when you configure
            one, the content of a request is sent to that provider to generate a response. With the
            default mock provider, no external model call is made at all.
          </li>
          <li>
            <strong className="text-content-primary">Connectors you connect</strong> — a provider
            receives only what the specific capability requires, when you invoke it.
          </li>
          <li>
            <strong className="text-content-primary">Infrastructure you choose</strong> — the
            hosting, database and cache you provision hold the data described above.
          </li>
        </ul>
        <p>
          Nothing is transmitted to a provider you have not configured. Staging and production are
          kept isolated in code — separate databases, separate credentials, separate queue
          namespaces — so test activity cannot reach production accounts.
        </p>
      </Section>

      <Section icon={ShieldCheck} title="How consequential actions are controlled">
        <p>
          Capability does not imply permission. Actions that send, publish, delete, purchase,
          refund, spend, change budgets, deploy, merge or alter security settings pass through
          policy and, where required, an explicit approval that the model cannot issue to itself.
        </p>
        <p>
          Approval grants are single-use. Every tool execution is recorded with its outcome and the
          correlation ID of the originating request, so any action can be traced back to what
          caused it. Content returned by external systems is treated as data and never as
          instructions.
        </p>
      </Section>

      <Section icon={UserCheck} title="Your choices">
        <ul className="ml-4 list-disc space-y-1.5">
          <li>Delete individual memories from the Memory page at any time.</li>
          <li>Disconnect any connector, which discards its stored authorisation.</li>
          <li>Clear your local session from the account menu, removing the key and history.</li>
          <li>
            Because an operator controls the database, requests to access, correct, export or
            erase personal data are fulfilled by that operator directly against their own storage.
          </li>
        </ul>
      </Section>

      <Section icon={Clock} title="Retention">
        <p>
          The platform does not currently apply automatic expiry to tasks, workflows, memory or
          audit events — they persist until deleted. Audit events are intended to be append-only,
          because a record that can be quietly rewritten is not an audit trail.
        </p>
        <p>
          Operators running THYNACT under a regime with statutory retention limits should set and
          enforce a retention schedule against their own database; the platform does not assume one
          on their behalf.
        </p>
      </Section>

      <Section icon={Mail} title="Contact">
        <p>
          Questions about this notice, or a request concerning personal data, should go to the
          operator of the deployment you are using. For the platform itself, see the{" "}
          <Link
            to="/overview"
            className="font-medium text-accent-gold underline-offset-2 hover:underline"
          >
            product overview
          </Link>{" "}
          or the{" "}
          <Link
            to="/system-health"
            className="font-medium text-accent-gold underline-offset-2 hover:underline"
          >
            system health
          </Link>{" "}
          page, which reports exactly how this deployment is configured.
        </p>
      </Section>
    </div>
  );
}
