import { useRef } from "react";
import { motion, useReducedMotion } from "framer-motion";
import { useI18n, enabledLocales } from "@/lib/i18n";
import { cn } from "@/lib/utils";

/**
 * Segmented language control, rendered entirely from the locale registry.
 *
 * It has no idea which languages exist: it maps `enabledLocales()`, so adding
 * a locale to the registry makes it appear here with no change to this file.
 * There is deliberately no "toggle to the other language" logic — that shape
 * only works for exactly two locales and becomes debt the moment a third is
 * added.
 *
 * Motion: the active capsule is a shared `layoutId`, so Framer animates it
 * between segments rather than us positioning it by hand — which is what keeps
 * rapid switching from stranding the indicator mid-track. A glass sweep runs
 * across the control on change. Both are transform/opacity only.
 */
export function LanguageSwitcher({ className }: { className?: string }) {
  const { locale, setLocale, t, definition } = useI18n();
  const reduceMotion = useReducedMotion();
  const locales = enabledLocales();
  const buttonsRef = useRef<(HTMLButtonElement | null)[]>([]);

  // Roving arrow-key navigation, the expected keyboard model for a radiogroup.
  const onKeyDown = (event: React.KeyboardEvent, index: number) => {
    const last = locales.length - 1;
    let next: number | null = null;
    if (event.key === "ArrowRight" || event.key === "ArrowDown") next = index === last ? 0 : index + 1;
    if (event.key === "ArrowLeft" || event.key === "ArrowUp") next = index === 0 ? last : index - 1;
    if (event.key === "Home") next = 0;
    if (event.key === "End") next = last;
    if (next === null) return;
    event.preventDefault();
    setLocale(locales[next].code);
    buttonsRef.current[next]?.focus();
  };

  return (
    <div
      role="radiogroup"
      aria-label={t("language.label")}
      className={cn(
        // Same glass vocabulary as the other topbar controls: translucent
        // surface, hairline border, no glow.
        "relative inline-flex shrink-0 items-center gap-0.5 overflow-hidden rounded-full",
        "border border-hairline bg-white/[0.04] p-0.5 backdrop-blur-md",
        "dark:bg-white/[0.04]",
        className
      )}
    >
      {/* Glass sweep: a highlight that travels across the control when the
          language changes. Keyed on locale so it replays on each switch. */}
      {!reduceMotion && (
        <motion.span
          key={`sweep-${locale}`}
          aria-hidden
          initial={{ x: "-120%", opacity: 0.55 }}
          animate={{ x: "120%", opacity: 0 }}
          transition={{ duration: 0.55, ease: [0.22, 1, 0.36, 1] }}
          className="pointer-events-none absolute inset-y-0 w-1/2 bg-gradient-to-r from-transparent via-white/25 to-transparent"
        />
      )}

      {locales.map((item, index) => {
        const active = item.code === locale;
        return (
          <button
            key={item.code}
            ref={(el) => {
              buttonsRef.current[index] = el;
            }}
            type="button"
            role="radio"
            aria-checked={active}
            // The accessible name is the language's own name, so a screen
            // reader announces "हिंदी", not a code.
            aria-label={t("language.switchTo", { language: item.nativeLabel })}
            lang={item.code}
            tabIndex={active ? 0 : -1}
            onClick={() => setLocale(item.code)}
            onKeyDown={(event) => onKeyDown(event, index)}
            className={cn(
              "focus-ring relative z-10 rounded-full px-2.5 text-[11px] font-medium leading-none",
              // 44px touch target on coarse pointers without inflating the
              // control on desktop, where it sits beside the icon buttons.
              "flex h-7 items-center justify-center whitespace-nowrap transition-colors duration-200 max-sm:h-11 max-sm:px-3.5",
              active ? "text-content-primary" : "text-content-muted hover:text-content-secondary"
            )}
          >
            {active && (
              <motion.span
                // Shared layoutId = Framer owns the indicator's position, so
                // it glides between segments and cannot end up stranded after
                // rapid switching.
                layoutId="language-indicator"
                className="absolute inset-0 rounded-full border border-accent-gold/25 bg-accent-gold/[0.14]"
                transition={
                  reduceMotion
                    ? { duration: 0 }
                    : { type: "spring", stiffness: 420, damping: 34, mass: 0.7 }
                }
              />
            )}
            <span className="relative">{item.shortLabel}</span>
          </button>
        );
      })}
      <span className="sr-only" aria-live="polite">
        {t("language.current", { language: definition.nativeLabel })}
      </span>
    </div>
  );
}
