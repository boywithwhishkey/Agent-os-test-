import { useState } from "react";
import { Link } from "react-router-dom";
import { Menu, Search, Moon, Sun, Monitor, Settings as SettingsIcon } from "lucide-react";
import { ConnectionStatus } from "./ConnectionStatus";
import { LanguageSwitcher } from "./LanguageSwitcher";
import { AccountPopover } from "./AccountPopover";
import { useTheme } from "@/lib/theme";
import { getEnvironmentLabel } from "@/lib/environment";
import { Button } from "@/components/ui/Button";
import { useT } from "@/lib/i18n";

export function Topbar({
  onOpenMobileNav,
  onOpenCommandPalette,
}: {
  onOpenMobileNav: () => void;
  onOpenCommandPalette: () => void;
}) {
  const { theme, setTheme } = useTheme();
  const t = useT();
  const [themeMenuOpen, setThemeMenuOpen] = useState(false);

  const environmentLabel =
    typeof window === "undefined" ? null : getEnvironmentLabel(window.location.hostname);
  const themeIcon = theme === "dark" ? <Moon className="h-4 w-4" /> : theme === "light" ? <Sun className="h-4 w-4" /> : <Monitor className="h-4 w-4" />;

  // Deliberately chrome-less: no glass panel, no border, no fade strip. The
  // ambient background runs straight through the top of the page, and each
  // control carries its own (minimal) affordance instead of sitting in a box.
  return (
    <header className="sticky top-0 z-30 flex h-14 items-center gap-1.5 bg-transparent px-3 sm:gap-3 sm:px-4">
      <button
        onClick={onOpenMobileNav}
        className="focus-ring shrink-0 rounded-md p-2 text-content-secondary hover:bg-surface-hover lg:hidden"
        aria-label={t("nav.openNavigation")}
      >
        <Menu className="h-5 w-5" />
      </button>

      <AccountPopover />

      <button
        onClick={onOpenCommandPalette}
        aria-label={t("topbar.searchPlaceholder")}
        className="focus-ring group flex shrink-0 items-center justify-center gap-2 rounded-lg p-2 text-sm text-content-muted transition-colors duration-200 hover:bg-white/[0.05] hover:text-content-secondary sm:flex-1 sm:max-w-md sm:justify-start sm:px-3 sm:py-1.5"
      >
        <Search className="h-4 w-4 shrink-0 sm:h-3.5 sm:w-3.5" />
        <span className="hidden truncate text-left sm:inline">{t("topbar.searchPlaceholder")}</span>
        <kbd className="hidden font-mono text-[10px] text-content-muted/70 transition-opacity duration-200 group-hover:opacity-100 sm:inline">
          ⌘K
        </kbd>
      </button>

      <div className="ml-auto flex items-center gap-1 sm:gap-2">
        {/* Non-production deployments say so. staging.thynact.com was for a
            period served from the production build, making the two visually
            identical — an operator should never have to guess which one they
            are about to act on. Nothing renders in production. */}
        {environmentLabel && (
          <span
            title={t("topbar.nonProduction", { environment: environmentLabel })}
            className="hidden items-center gap-1.5 text-[11px] font-medium tracking-wide text-accent-amber sm:inline-flex"
          >
            <span className="h-1.5 w-1.5 rounded-full bg-accent-amber animate-pulse-slow" />
            {environmentLabel}
          </span>
        )}
        {/* Reachability and authorisation are reported together — see
            ConnectionStatus for why they must not be two competing chips. */}
        <ConnectionStatus />

        {/* Beside the theme control: both are "how the product presents
            itself to me" preferences, so they belong together. */}
        <LanguageSwitcher className="hidden sm:inline-flex" />

        <div className="relative">
          <Button variant="ghost" size="icon" onClick={() => setThemeMenuOpen((o) => !o)} aria-label={t("theme.change")}>
            {themeIcon}
          </Button>
          {themeMenuOpen && (
            <div
              className="glass-focus absolute right-0 top-full z-40 mt-1.5 w-36 rounded-lg border border-hairline p-1"
              onMouseLeave={() => setThemeMenuOpen(false)}
            >
              {(["dark", "light", "system"] as const).map((option) => (
                <button
                  key={option}
                  onClick={() => {
                    setTheme(option);
                    setThemeMenuOpen(false);
                  }}
                  className={`flex w-full items-center gap-2 rounded-md px-2 py-1.5 text-left text-sm capitalize hover:bg-surface-hover ${
                    theme === option ? "text-accent-gold" : "text-content-secondary"
                  }`}
                >
                  {option === "dark" && <Moon className="h-3.5 w-3.5" />}
                  {option === "light" && <Sun className="h-3.5 w-3.5" />}
                  {option === "system" && <Monitor className="h-3.5 w-3.5" />}
                  {option}
                </button>
              ))}
            </div>
          )}
        </div>

        <Link to="/settings">
          <Button variant="ghost" size="icon" aria-label="Settings">
            <SettingsIcon className="h-4 w-4" />
          </Button>
        </Link>
      </div>
    </header>
  );
}
