import { useEffect, useRef, useState } from "react";
import { Menu, Search } from "lucide-react";
import { LanguageSwitcher } from "./LanguageSwitcher";
import { ThemeSwitcher } from "./ThemeSwitcher";
import { AccountPopover } from "./AccountPopover";
import { getEnvironmentLabel } from "@/lib/environment";
import { useT } from "@/lib/i18n";
import { cn } from "@/lib/utils";

export function Topbar({
  onOpenMobileNav,
  onOpenCommandPalette,
}: {
  onOpenMobileNav: () => void;
  onOpenCommandPalette: () => void;
}) {
  const t = useT();

  // The header only needs a backdrop once content is behind it. A 1px sentinel
  // above it reports that via IntersectionObserver, so there is no scroll
  // listener and no per-frame work — the observer fires twice per page, at the
  // moments the state actually changes.
  const sentinel = useRef<HTMLDivElement>(null);
  const [scrolled, setScrolled] = useState(false);
  useEffect(() => {
    const node = sentinel.current;
    if (!node || typeof IntersectionObserver === "undefined") return;
    const observer = new IntersectionObserver(
      ([entry]) => setScrolled(!entry.isIntersecting),
      { rootMargin: "0px" }
    );
    observer.observe(node);
    return () => observer.disconnect();
  }, []);

  const environmentLabel =
    typeof window === "undefined" ? null : getEnvironmentLabel(window.location.hostname);

  // Deliberately chrome-less: no glass panel, no border, no fade strip. The
  // ambient background runs straight through the top of the page, and each
  // control carries its own (minimal) affordance instead of sitting in a box.
  return (
    <>
      {/* Sentinel: sits in normal flow above the sticky header. */}
      <div ref={sentinel} aria-hidden className="h-px w-full" />
      <header
        className={cn(
          "sticky top-0 z-30 flex h-14 items-center gap-1.5 px-3 sm:gap-3 sm:px-4",
          "transition-colors duration-200",
          // Chrome-less over the hero, glass once content is behind it. Before
          // the sticky positioning was fixed the header never actually stayed
          // put, so this collision could not happen and the bar could stay
          // fully transparent.
          scrolled
            ? "border-b border-hairline bg-surface-canvas/88 backdrop-blur-xl"
            : "border-b border-transparent bg-transparent"
        )}
      >
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

        {/* Beside the theme control: both are "how the product presents
            itself to me" preferences, so they belong together. */}
        {/* Language and theme are the two "how this product presents itself
            to me" preferences, so they sit together as one control family.
            Settings and the API status moved into the account popover: the
            header was carrying six targets on a 320px screen, and these two
            are the ones people actually reach for. */}
        <LanguageSwitcher />
        <ThemeSwitcher />
      </div>
      </header>
    </>
  );
}
