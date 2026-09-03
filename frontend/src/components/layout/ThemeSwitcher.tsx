import { AnimatePresence, motion, useReducedMotion } from "framer-motion";
import { Moon, Sun, Monitor } from "lucide-react";
import { useTheme } from "@/lib/theme";
import { useT } from "@/lib/i18n";
import { cn } from "@/lib/utils";

const ORDER = ["dark", "light", "system"] as const;
type ThemeValue = (typeof ORDER)[number];

const ICONS: Record<ThemeValue, typeof Moon> = {
  dark: Moon,
  light: Sun,
  system: Monitor,
};

/**
 * A single compact glass button that cycles dark → light → system.
 *
 * This replaced a three-segment control. Segments were honest about the three
 * options but cost roughly three times the width, and the header is the most
 * contested space in the product — on a phone that bulk pushed against the
 * language control and ate the title row. Theme is a low-frequency, easily
 * reversible preference: one tap to advance, and the icon says where you are.
 * Language stays segmented because picking a language is a deliberate choice
 * you make once, not something you cycle through.
 *
 * The icon crossfades with a small rotation rather than swapping instantly,
 * so the control still reads as animated glass at a fraction of the footprint.
 */
export function ThemeSwitcher({ className }: { className?: string }) {
  const { theme, setTheme } = useTheme();
  const reduceMotion = useReducedMotion();
  const t = useT();

  const current = (ORDER.includes(theme as ThemeValue) ? theme : "dark") as ThemeValue;
  const next = ORDER[(ORDER.indexOf(current) + 1) % ORDER.length];
  const Icon = ICONS[current];

  return (
    <button
      type="button"
      onClick={() => setTheme(next)}
      // Announces what it IS and what it will DO — an icon-only control that
      // only said "theme" would leave a screen-reader user guessing.
      aria-label={`${t("theme.label")}: ${t(`theme.${current}`)}. ${t("theme.change")}`}
      title={t(`theme.${current}`)}
      className={cn(
        "focus-ring relative inline-flex shrink-0 items-center justify-center overflow-hidden rounded-full",
        // Same glass vocabulary as the language capsule, so the two still read
        // as one control family despite the different shape.
        "border border-hairline bg-white/[0.05] backdrop-blur-md",
        "h-8 w-8 max-sm:h-11 max-sm:w-11",
        "text-content-secondary transition-colors duration-200 hover:text-content-primary",
        "active:scale-[0.94] motion-reduce:active:scale-100",
        className
      )}
    >
      <AnimatePresence mode="wait" initial={false}>
        <motion.span
          key={current}
          initial={reduceMotion ? false : { opacity: 0, rotate: -35, scale: 0.7 }}
          animate={{ opacity: 1, rotate: 0, scale: 1 }}
          exit={reduceMotion ? { opacity: 0 } : { opacity: 0, rotate: 35, scale: 0.7 }}
          transition={{ duration: reduceMotion ? 0 : 0.22, ease: [0.22, 1, 0.36, 1] }}
          className="absolute inset-0 flex items-center justify-center"
        >
          <Icon className="h-4 w-4" />
        </motion.span>
      </AnimatePresence>
      <span className="sr-only" aria-live="polite">
        {t(`theme.${current}`)}
      </span>
    </button>
  );
}
