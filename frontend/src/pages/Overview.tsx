import { Link } from "react-router-dom";
import { useT } from "@/lib/i18n";
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

// Keys, not copy. `to` is a route identifier and is never translated.
const PILLARS = [
  { icon: Brain, key: "reason", to: "/orchestrate" },
  { icon: Users, key: "threeRole", to: "/autonomous" },
  { icon: Workflow, key: "workflow", to: "/workflows" },
  { icon: Wrench, key: "tools", to: "/tools" },
  { icon: Database, key: "memory", to: "/memory" },
  { icon: Activity, key: "runtime", to: "/runtime" },
] as const;

const GOVERNANCE = [
  { icon: ShieldCheck, key: "authority" },
  { icon: ScrollText, key: "audited" },
  { icon: Lock, key: "untrusted" },
  { icon: Gauge, key: "honest" },
] as const;

export default function Overview() {
  const t = useT();
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
              {t("pages.overview.heroTitle")}
            </h1>
          </StaggerItem>
          <StaggerItem>
            <p className="max-w-2xl text-base leading-relaxed text-content-secondary">
              {BRAND_TAGLINE} {t("pages.overview.heroBody")}
            </p>
          </StaggerItem>
          <StaggerItem>
            <div className="flex flex-wrap items-center gap-2.5">
              <Link to="/orchestrate">
                <Button size="lg">
                  {t("pages.overview.startOrchestration")} <ArrowRight className="h-4 w-4" />
                </Button>
              </Link>
              <Link to="/integrations">
                <Button variant="outline" size="lg">
                  {t("pages.overview.browseConnectors")}
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
            <h2 className="text-lg font-semibold text-content-primary">{t("pages.overview.whatItDoes")}</h2>
            <span className="hidden shrink-0 text-xs uppercase tracking-wider text-content-muted sm:inline">
              {t("pages.overview.everyItemLinks")}
            </span>
          </div>
          <StaggerGroup className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3">
            {PILLARS.map((p) => (
              <StaggerItem key={p.key} className="h-full">
                <Card className="group h-full transition-transform duration-200 hover:-translate-y-0.5">
                  <CardContent className="flex h-full flex-col gap-3">
                    <span className="flex h-10 w-10 items-center justify-center rounded-xl border border-hairline bg-accent-gold/[0.08] text-accent-gold transition-colors group-hover:border-accent-gold/30">
                      <p.icon className="h-5 w-5" />
                    </span>
                    <h3 className="text-sm font-semibold text-content-primary">{t(`pages.overview.pillars.${p.key}.title` as Parameters<typeof t>[0])}</h3>
                    <p className="flex-1 text-sm leading-relaxed text-content-secondary">{t(`pages.overview.pillars.${p.key}.body` as Parameters<typeof t>[0])}</p>
                    <Link
                      to={p.to}
                      className="focus-ring inline-flex items-center gap-1.5 rounded text-sm font-medium text-accent-gold transition-opacity hover:opacity-80"
                    >
                      {t(`pages.overview.pillars.${p.key}.action` as Parameters<typeof t>[0])} <ArrowRight className="h-3.5 w-3.5" />
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
            <h2 className="text-lg font-semibold text-content-primary">{t("pages.overview.howItStaysTrustworthy")}</h2>
            <p className="max-w-2xl text-sm text-content-secondary">
              {t("pages.overview.trustworthyBody")}
            </p>
          </div>
          <div className="grid grid-cols-1 gap-3 md:grid-cols-2">
            {GOVERNANCE.map((g) => (
              <Card key={g.key}>
                <CardContent className="flex gap-3.5">
                  <span className="mt-0.5 flex h-9 w-9 shrink-0 items-center justify-center rounded-lg border border-hairline text-accent-gold">
                    <g.icon className="h-4 w-4" />
                  </span>
                  <div className="min-w-0 space-y-1">
                    <h3 className="text-sm font-semibold text-content-primary">{t(`pages.overview.governance.${g.key}.title` as Parameters<typeof t>[0])}</h3>
                    <p className="text-sm leading-relaxed text-content-secondary">{t(`pages.overview.governance.${g.key}.body` as Parameters<typeof t>[0])}</p>
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
                <h2 className="text-sm font-semibold text-content-primary">{t("pages.overview.connectors")}</h2>
                <Badge tone="neutral">{t("pages.overview.mcpFirst")}</Badge>
              </div>
              <p className="max-w-xl text-sm leading-relaxed text-content-secondary">
                {t("pages.overview.connectorsBody")}
              </p>
            </div>
            <Link to="/integrations" className="shrink-0">
              <Button variant="outline">
                {t("pages.overview.viewIntegrations")} <ArrowRight className="h-4 w-4" />
              </Button>
            </Link>
          </CardContent>
        </Card>
      </ScrollReveal>
    </div>
  );
}
