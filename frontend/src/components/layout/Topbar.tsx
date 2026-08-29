import { useState } from "react";
import { Link } from "react-router-dom";
import { Menu, Search, Moon, Sun, Monitor, KeyRound, Settings as SettingsIcon } from "lucide-react";
import { HealthIndicator } from "./HealthIndicator";
import { AccountPopover } from "./AccountPopover";
import { useTheme } from "@/lib/theme";
import { isApiConfigured } from "@/lib/api/config";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";

export function Topbar({
  onOpenMobileNav,
  onOpenCommandPalette,
}: {
  onOpenMobileNav: () => void;
  onOpenCommandPalette: () => void;
}) {
  const { theme, setTheme } = useTheme();
  const [themeMenuOpen, setThemeMenuOpen] = useState(false);
  const configured = isApiConfigured();

  const themeIcon = theme === "dark" ? <Moon className="h-4 w-4" /> : theme === "light" ? <Sun className="h-4 w-4" /> : <Monitor className="h-4 w-4" />;

  return (
    <header className="glass-ambient sticky top-0 z-30 flex h-14 items-center gap-1.5 px-3 after:pointer-events-none after:absolute after:inset-x-0 after:top-full after:h-4 after:bg-gradient-to-b after:from-surface-canvas/60 after:to-transparent sm:gap-3 sm:px-4">
      <button
        onClick={onOpenMobileNav}
        className="focus-ring shrink-0 rounded-md p-2 text-content-secondary hover:bg-surface-hover lg:hidden"
        aria-label="Open navigation"
      >
        <Menu className="h-5 w-5" />
      </button>

      <AccountPopover />

      <button
        onClick={onOpenCommandPalette}
        aria-label="Search or jump to…"
        className="focus-ring flex shrink-0 items-center justify-center gap-2 rounded-lg border border-hairline bg-surface-hover/60 p-2 text-sm text-content-muted hover:border-accent-violet/30 sm:flex-1 sm:max-w-md sm:justify-start sm:px-3 sm:py-1.5"
      >
        <Search className="h-4 w-4 shrink-0 sm:h-3.5 sm:w-3.5" />
        <span className="hidden flex-1 truncate text-left sm:inline">Search or jump to…</span>
        <kbd className="hidden rounded border border-hairline bg-surface-hover px-1.5 py-0.5 font-mono text-[10px] sm:inline">
          ⌘K
        </kbd>
      </button>

      <div className="ml-auto flex items-center gap-1 sm:gap-2">
        {!configured && (
          <Link to="/settings">
            <Badge tone="amber" className="hidden sm:inline-flex">
              <KeyRound className="h-3 w-3" />
              API key needed
            </Badge>
          </Link>
        )}
        <HealthIndicator />

        <div className="relative">
          <Button variant="ghost" size="icon" onClick={() => setThemeMenuOpen((o) => !o)} aria-label="Change theme">
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
                    theme === option ? "text-accent-violet" : "text-content-secondary"
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
