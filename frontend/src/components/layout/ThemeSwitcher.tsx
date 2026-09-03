import { Moon, Sun, Monitor } from "lucide-react";
import { useTheme } from "@/lib/theme";
import { useT } from "@/lib/i18n";
import { GlassSegmented } from "@/components/ui/GlassSegmented";

/**
 * Theme control, built on the same glass primitive as the language switcher so
 * the two read as one control family in the header.
 *
 * This replaces an icon button that opened a dropdown. The dropdown was two
 * taps and an overlay to change a three-way preference — on mobile that is
 * strictly worse than three visible targets, and the overlay was one more
 * blurred surface to composite.
 */
export function ThemeSwitcher({ className }: { className?: string }) {
  const { theme, setTheme } = useTheme();
  const t = useT();

  return (
    <GlassSegmented
      className={className}
      layoutId="theme-indicator"
      ariaLabel={t("theme.label")}
      value={theme}
      onChange={(value) => setTheme(value as "dark" | "light" | "system")}
      options={[
        { value: "dark", content: <Moon className="h-3.5 w-3.5" />, label: t("theme.dark") },
        { value: "light", content: <Sun className="h-3.5 w-3.5" />, label: t("theme.light") },
        { value: "system", content: <Monitor className="h-3.5 w-3.5" />, label: t("theme.system") },
      ]}
    />
  );
}
