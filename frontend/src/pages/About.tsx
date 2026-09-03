import { Link } from "react-router-dom";
import {
  ArrowRight,
  Brain,
  Zap,
  ShieldCheck,
  Gauge,
  CheckCircle2,
  Lock,
  Layers,
  Repeat,
  ScrollText,
  Compass,
} from "lucide-react";
import { useT } from "@/lib/i18n";
import { Card, CardContent } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { BrandMark } from "@/components/ui/BrandMark";
import { ScrollReveal, StaggerGroup, StaggerItem } from "@/components/ui/ScrollReveal";
import { ReasoningFlow } from "@/components/about/ReasoningFlow";

/**
 * About THYNACT — the product's own account of itself: why it exists, how work
 * moves through it, and what it holds to.
 *
 * Two rules govern the copy here, and both are why the shipped/direction split
 * below exists at all. First: nothing on this page may present a capability as
 * available unless it is. Anything forward-looking sits under "Where it is
 * going" and is badged as direction. Second: every string is a translation key
 * — this page carries the brand voice, and a brand voice that only exists in
 * English is not one.
 */

// Keys, not copy. Icons are presentation and stay here.
const PRINCIPLES = [
  { icon: Gauge, key: "fast" },
  { icon: CheckCircle2, key: "real" },
  { icon: Lock, key: "authority" },
  { icon: Layers, key: "neutral" },
  { icon: Repeat, key: "continuity" },
  { icon: ScrollText, key: "governed" },
] as const;

const VISION = ["surfaces", "connectors", "automation", "multimodal"] as const;

const TRIAD = [
  { icon: Brain, titleKey: "thinkTitle", bodyKey: "thinkBody" },
  { icon: Zap, titleKey: "actTitle", bodyKey: "actBody" },
  { icon: ShieldCheck, titleKey: "controlTitle", bodyKey: "controlBody" },
] as const;

export default function About() {
  const t = useT();
  return (
    <div className="space-y-12 pb-10">
      {/* Hero */}
      <section className="relative pt-2">
        <div
          className="pointer-events-none absolute -top-24 right-0 h-64 w-64 rounded-full bg-accent-gold/[0.10] blur-[100px] animate-float"
          aria-hidden
        />
        <StaggerGroup className="flex flex-col gap-5">
          <StaggerItem>
            <BrandMark variant="full" size="lg" />
          </StaggerItem>
          <StaggerItem>
            <p className="max-w-3xl text-balance text-2xl font-medium leading-snug tracking-tight text-content-primary sm:text-3xl">
              {t("pages.about.heroStatement")}
            </p>
          </StaggerItem>
        </StaggerGroup>
      </section>

      {/* Why it exists */}
      <ScrollReveal>
        <section className="space-y-3">
          <h2 className="text-lg font-semibold text-content-primary">{t("pages.about.whyTitle")}</h2>
          <p className="max-w-3xl text-sm leading-relaxed text-content-secondary sm:text-base">
            {t("pages.about.whyBody")}
          </p>
        </section>
      </ScrollReveal>

      {/* Think / Act / Control */}
      <ScrollReveal>
        <StaggerGroup className="grid grid-cols-1 gap-3 md:grid-cols-3">
          {TRIAD.map((item) => (
            <StaggerItem key={item.titleKey} className="h-full">
              <Card className="h-full">
                <CardContent className="flex h-full flex-col gap-3">
                  <span className="flex h-10 w-10 items-center justify-center rounded-xl border border-hairline bg-accent-gold/[0.08] text-accent-gold">
                    <item.icon className="h-5 w-5" />
                  </span>
                  <h3 className="text-base font-semibold text-content-primary">
                    {t(`pages.about.${item.titleKey}` as Parameters<typeof t>[0])}
                  </h3>
                  <p className="text-sm leading-relaxed text-content-secondary">
                    {t(`pages.about.${item.bodyKey}` as Parameters<typeof t>[0])}
                  </p>
                </CardContent>
              </Card>
            </StaggerItem>
          ))}
        </StaggerGroup>
      </ScrollReveal>

      {/* The flow */}
      <ScrollReveal>
        <section className="space-y-4">
          <div className="space-y-1">
            <div className="flex flex-wrap items-center gap-2.5">
              <h2 className="text-lg font-semibold text-content-primary">{t("pages.about.flowTitle")}</h2>
              <Badge tone="gold">{t("pages.about.shipped")}</Badge>
            </div>
            <p className="max-w-2xl text-sm text-content-secondary">{t("pages.about.flowBody")}</p>
          </div>
          <Card>
            <CardContent className="py-6">
              <ReasoningFlow />
            </CardContent>
          </Card>
        </section>
      </ScrollReveal>

      {/* Principles */}
      <ScrollReveal>
        <section className="space-y-4">
          <h2 className="text-lg font-semibold text-content-primary">{t("pages.about.principlesTitle")}</h2>
          <StaggerGroup className="grid grid-cols-1 gap-3 md:grid-cols-2">
            {PRINCIPLES.map((p) => (
              <StaggerItem key={p.key} className="h-full">
                <Card className="h-full">
                  <CardContent className="flex h-full gap-3.5">
                    <span className="mt-0.5 flex h-9 w-9 shrink-0 items-center justify-center rounded-lg border border-hairline text-accent-gold">
                      <p.icon className="h-4 w-4" />
                    </span>
                    <div className="min-w-0 space-y-1">
                      <h3 className="text-sm font-semibold text-content-primary">
                        {t(`pages.about.principles.${p.key}.title` as Parameters<typeof t>[0])}
                      </h3>
                      <p className="text-sm leading-relaxed text-content-secondary">
                        {t(`pages.about.principles.${p.key}.body` as Parameters<typeof t>[0])}
                      </p>
                    </div>
                  </CardContent>
                </Card>
              </StaggerItem>
            ))}
          </StaggerGroup>
        </section>
      </ScrollReveal>

      {/* Direction — explicitly NOT shipped capability. */}
      <ScrollReveal>
        <section className="space-y-4">
          <div className="space-y-1">
            <div className="flex flex-wrap items-center gap-2.5">
              <h2 className="text-lg font-semibold text-content-primary">{t("pages.about.visionTitle")}</h2>
              <Badge tone="neutral">
                <Compass className="h-3 w-3" aria-hidden /> {t("pages.about.direction")}
              </Badge>
            </div>
            <p className="max-w-2xl text-sm text-content-secondary">{t("pages.about.visionBody")}</p>
          </div>
          <Card>
            <CardContent>
              <ul className="grid grid-cols-1 gap-x-6 gap-y-2.5 sm:grid-cols-2">
                {VISION.map((v) => (
                  <li key={v} className="flex items-start gap-2.5 text-sm text-content-secondary">
                    <span className="mt-[0.45rem] h-1.5 w-1.5 shrink-0 rounded-full bg-accent-gold/60" aria-hidden />
                    {t(`pages.about.vision.${v}` as Parameters<typeof t>[0])}
                  </li>
                ))}
              </ul>
            </CardContent>
          </Card>
        </section>
      </ScrollReveal>

      {/* CTA */}
      <ScrollReveal>
        <Card className="overflow-hidden">
          <CardContent className="relative flex flex-col gap-4 py-8 sm:items-center sm:text-center">
            <div
              className="pointer-events-none absolute -bottom-20 left-1/2 h-52 w-52 -translate-x-1/2 rounded-full bg-accent-gold/[0.08] blur-[90px]"
              aria-hidden
            />
            <h2 className="relative text-xl font-semibold tracking-tight text-content-primary">
              {t("pages.about.ctaTitle")}
            </h2>
            <p className="relative max-w-xl text-sm leading-relaxed text-content-secondary">
              {t("pages.about.ctaBody")}
            </p>
            <div className="relative flex flex-wrap gap-2.5 sm:justify-center">
              <Link to="/">
                <Button size="lg">
                  {t("pages.about.ctaPrimary")} <ArrowRight className="h-4 w-4" />
                </Button>
              </Link>
              <Link to="/integrations">
                <Button variant="outline" size="lg">
                  {t("pages.about.ctaSecondary")}
                </Button>
              </Link>
            </div>
          </CardContent>
        </Card>
      </ScrollReveal>
    </div>
  );
}
