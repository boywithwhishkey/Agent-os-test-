import { motion, useReducedMotion } from "framer-motion";
import { ShieldCheck } from "lucide-react";
import { useT } from "@/lib/i18n";
import { cn } from "@/lib/utils";

/**
 * The INTENT → THINK → PLAN → VERIFY → ACT → RESULT chain, with the governed
 * middle (PLAN / VERIFY / ACT) enclosed by CONTROL.
 *
 * Built from layout primitives rather than a fixed-viewBox SVG on purpose: the
 * chain has to reflow from one horizontal row (>=1280px) to a vertical stack
 * (mobile) without scaling its labels into illegibility, and a scaled SVG
 * cannot do that.
 *
 * Motion is a single travelling pulse per connector — it communicates
 * direction, which is the whole point of the diagram. Under
 * `prefers-reduced-motion` every animation is dropped and the connectors
 * render as static rules; the diagram still reads correctly, because direction
 * is also carried by reading order.
 */

const GOVERNED = new Set<string>(["plan", "verify", "act"]);

type Step = "intent" | "think" | "plan" | "verify" | "act" | "result";

function Node({ step, index }: { step: Step; index: number }) {
  const t = useT();
  const governed = GOVERNED.has(step);
  return (
    <motion.li
      initial={{ opacity: 0, y: 10 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true, margin: "-40px" }}
      transition={{ duration: 0.35, delay: index * 0.07, ease: [0.16, 1, 0.3, 1] }}
      className={cn(
        "flex min-w-0 items-center justify-center rounded-xl border px-3 py-2.5 text-center text-xs font-semibold tracking-wide xl:flex-1",
        governed
          ? "border-accent-gold/30 bg-accent-gold/[0.07] text-accent-gold"
          : "border-hairline bg-surface-raised text-content-primary"
      )}
    >
      {t(`pages.about.flow.${step}` as Parameters<typeof t>[0])}
    </motion.li>
  );
}

/**
 * A connector between two nodes. Renders a vertical rule in the stacked layout
 * and a horizontal one from `lg` up, so the same list works in both
 * directions without duplicating the chain markup.
 */
function Connector({ delay }: { delay: number }) {
  const reduced = useReducedMotion();
  return (
    <li aria-hidden className="flex shrink-0 items-center justify-center">
      <span className="relative block h-5 w-px overflow-hidden rounded-full bg-accent-gold/25 xl:hidden">
        {!reduced && (
          <motion.span
            className="absolute left-0 block h-2 w-px rounded-full bg-accent-gold"
            initial={{ top: "-40%" }}
            animate={{ top: ["-40%", "140%"] }}
            transition={{ duration: 1.6, repeat: Infinity, ease: "easeInOut", delay, repeatDelay: 1.4 }}
          />
        )}
      </span>
      <span className="relative hidden h-px w-5 overflow-hidden rounded-full bg-accent-gold/25 xl:block 2xl:w-8">
        {!reduced && (
          <motion.span
            className="absolute top-0 block h-px w-2 rounded-full bg-accent-gold"
            initial={{ left: "-40%" }}
            animate={{ left: ["-40%", "140%"] }}
            transition={{ duration: 1.6, repeat: Infinity, ease: "easeInOut", delay, repeatDelay: 1.4 }}
          />
        )}
      </span>
    </li>
  );
}

export function ReasoningFlow() {
  const t = useT();
  return (
    <ol className="mx-auto flex max-w-md flex-col items-stretch xl:max-w-none xl:flex-row xl:items-center">
      <Node step="intent" index={0} />
      <Connector delay={0} />
      <Node step="think" index={1} />
      <Connector delay={0.2} />

      {/* The governed middle. CONTROL is a labelled enclosure rather than an
          absolutely-positioned overlay, so it can never land on top of text at
          a width nobody tested. */}
      <li className="min-w-0 xl:flex-[3.4]">
        <div className="relative mt-3 rounded-2xl border border-dashed border-accent-gold/35 bg-accent-gold/[0.03] p-3 xl:mx-1.5 xl:mt-0">
          <span className="absolute -top-2.5 left-3 inline-flex items-center gap-1 rounded-full border border-accent-gold/30 bg-surface-canvas px-2 py-0.5 text-[10px] font-semibold uppercase tracking-widest text-accent-gold">
            <ShieldCheck className="h-3 w-3" aria-hidden />
            {t("pages.about.flow.control")}
          </span>
          <ol className="flex flex-col items-stretch xl:flex-row xl:items-center">
            <Node step="plan" index={2} />
            <Connector delay={0.4} />
            <Node step="verify" index={3} />
            <Connector delay={0.6} />
            <Node step="act" index={4} />
          </ol>
        </div>
      </li>

      <Connector delay={0.8} />
      <Node step="result" index={5} />
    </ol>
  );
}
