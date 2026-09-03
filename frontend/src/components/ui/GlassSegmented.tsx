import { useRef, type ReactNode } from "react";
import { motion, useReducedMotion } from "framer-motion";
import { cn } from "@/lib/utils";

export interface SegmentOption {
  value: string;
  /** Visible content — short text or an icon. */
  content: ReactNode;
  /** Accessible name; required because an icon-only segment has none. */
  label: string;
  /** Optional per-segment lang, so a screen reader pronounces it correctly. */
  lang?: string;
}

/**
 * The glass segmented control used by BOTH the language and theme switchers.
 *
 * Shared on purpose: two lookalike components drift apart the first time one is
 * tweaked. One primitive means the two controls in the header are identical by
 * construction, not by discipline.
 *
 * Motion is a single shared-`layoutId` capsule, so Framer owns the indicator's
 * position and animates it between segments. That is what makes rapid tapping
 * safe — there is no timer or manual offset to get out of sync, and an
 * interrupted animation resolves to the correct place rather than stranding
 * the indicator mid-track.
 *
 * Only `transform` and `opacity` animate. `layoutId` moves the capsule with a
 * transform rather than re-laying out, which is what keeps it smooth on
 * mobile.
 */
export function GlassSegmented({
  options,
  value,
  onChange,
  ariaLabel,
  layoutId,
  className,
}: {
  options: SegmentOption[];
  value: string;
  onChange: (value: string) => void;
  ariaLabel: string;
  /** Must be unique per control, or two controls share one capsule. */
  layoutId: string;
  className?: string;
}) {
  const reduceMotion = useReducedMotion();
  const buttons = useRef<(HTMLButtonElement | null)[]>([]);

  // Roving arrow-key navigation — the expected model for a radiogroup.
  const onKeyDown = (event: React.KeyboardEvent, index: number) => {
    const last = options.length - 1;
    let next: number | null = null;
    if (event.key === "ArrowRight" || event.key === "ArrowDown") next = index === last ? 0 : index + 1;
    if (event.key === "ArrowLeft" || event.key === "ArrowUp") next = index === 0 ? last : index - 1;
    if (event.key === "Home") next = 0;
    if (event.key === "End") next = last;
    if (next === null) return;
    event.preventDefault();
    onChange(options[next].value);
    buttons.current[next]?.focus();
  };

  return (
    <div
      role="radiogroup"
      aria-label={ariaLabel}
      className={cn(
        "relative inline-flex shrink-0 items-center gap-0.5 rounded-full",
        // One blur layer for the whole control rather than one per segment:
        // stacked backdrop-filters are the expensive part on mobile GPUs.
        "border border-hairline bg-white/[0.05] p-0.5 backdrop-blur-md",
        className
      )}
    >
      {options.map((option, index) => {
        const active = option.value === value;
        return (
          <button
            key={option.value}
            ref={(el) => {
              buttons.current[index] = el;
            }}
            type="button"
            role="radio"
            aria-checked={active}
            aria-label={option.label}
            lang={option.lang}
            tabIndex={active ? 0 : -1}
            onClick={() => onChange(option.value)}
            onKeyDown={(event) => onKeyDown(event, index)}
            className={cn(
              "focus-ring relative z-10 flex items-center justify-center rounded-full",
              "text-[11px] font-medium leading-none whitespace-nowrap",
              // A 44px target on coarse pointers without inflating the control
              // on desktop, where it sits beside the other header controls.
              "h-7 px-2.5 max-sm:h-11 max-sm:min-w-11 max-sm:px-3",
              // Press feedback, neutralised under reduced motion.
              "transition-colors duration-200 active:scale-[0.94] motion-reduce:active:scale-100",
              active ? "text-content-primary" : "text-content-muted hover:text-content-secondary"
            )}
          >
            {active && (
              <motion.span
                layoutId={layoutId}
                className={cn(
                  "absolute inset-0 rounded-full",
                  // The "lens": a lit top edge over a soft gold body, so it
                  // reads as refractive glass rather than a flat chip.
                  "border border-accent-gold/25 bg-accent-gold/[0.14]",
                  "shadow-[inset_0_1px_0_0_rgba(255,255,255,0.16)]"
                )}
                transition={
                  reduceMotion
                    ? { duration: 0 }
                    : { type: "spring", stiffness: 420, damping: 34, mass: 0.7 }
                }
              />
            )}
            <span className="relative">{option.content}</span>
          </button>
        );
      })}
    </div>
  );
}
