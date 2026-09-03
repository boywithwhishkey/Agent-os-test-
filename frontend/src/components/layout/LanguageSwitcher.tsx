import { motion, useReducedMotion } from "framer-motion";
import { useI18n, enabledLocales } from "@/lib/i18n";
import { GlassSegmented } from "@/components/ui/GlassSegmented";
import { cn } from "@/lib/utils";

/**
 * Language control, rendered entirely from the locale registry.
 *
 * It has no idea which languages exist — it maps `enabledLocales()`, so adding
 * a locale to the registry makes it appear here with no change to this file.
 * There is deliberately no "toggle to the other language" shortcut: that shape
 * only works for exactly two locales.
 *
 * The glass sweep is the one thing layered on top of the shared control: a
 * highlight that travels across on change, keyed on locale so it replays.
 */
export function LanguageSwitcher({ className }: { className?: string }) {
  const { locale, setLocale, t, definition } = useI18n();
  const reduceMotion = useReducedMotion();
  const locales = enabledLocales();

  return (
    <div className={cn("relative inline-flex overflow-hidden rounded-full", className)}>
      {!reduceMotion && (
        <motion.span
          key={`sweep-${locale}`}
          aria-hidden
          initial={{ x: "-120%", opacity: 0.5 }}
          animate={{ x: "120%", opacity: 0 }}
          transition={{ duration: 0.5, ease: [0.22, 1, 0.36, 1] }}
          className="pointer-events-none absolute inset-y-0 z-20 w-1/2 bg-gradient-to-r from-transparent via-white/25 to-transparent"
        />
      )}

      <GlassSegmented
        layoutId="language-indicator"
        ariaLabel={t("language.label")}
        value={locale}
        onChange={setLocale}
        options={locales.map((item) => ({
          value: item.code,
          content: item.shortLabel,
          // The language's own name, so a screen reader announces "हिंदी".
          label: t("language.switchTo", { language: item.nativeLabel }),
          lang: item.code,
        }))}
      />

      <span className="sr-only" aria-live="polite">
        {t("language.current", { language: definition.nativeLabel })}
      </span>
    </div>
  );
}
