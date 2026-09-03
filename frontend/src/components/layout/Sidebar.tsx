import { NavLink, useLocation } from "react-router-dom";
import { ChevronsLeft } from "lucide-react";
import { motion } from "framer-motion";
import { navGroups } from "@/lib/nav";
import { BrandMark } from "@/components/ui/BrandMark";
import { LanguageSwitcher } from "./LanguageSwitcher";
import { useT, type TranslationKey } from "@/lib/i18n";
import { cn } from "@/lib/utils";

export function Sidebar({
  collapsed,
  onToggle,
  mobileOpen,
  onCloseMobile,
}: {
  collapsed: boolean;
  onToggle: () => void;
  mobileOpen: boolean;
  onCloseMobile: () => void;
}) {
  const location = useLocation();
  const t = useT();

  return (
    <>
      {mobileOpen && (
        <div
          className="fixed inset-0 z-40 bg-black/50 backdrop-blur-sm lg:hidden"
          onClick={onCloseMobile}
          aria-hidden
        />
      )}
      <aside
        className={cn(
          "glass-soft fixed inset-y-0 left-0 z-50 flex flex-col border-r border-hairline transition-[width] duration-200 lg:sticky lg:top-0 lg:h-screen lg:h-dvh lg:translate-x-0",
          collapsed ? "lg:w-[68px]" : "lg:w-64",
          mobileOpen ? "w-64 translate-x-0" : "-translate-x-full lg:translate-x-0"
        )}
      >
        {/* Taller than the topbar on purpose: the lockup carries the tagline
            under the wordmark, with the mark spanning both lines. The topbar
            has no bottom border, so the two not sharing a height is not a
            visible misalignment. */}
        <div
          className={cn(
            "flex shrink-0 items-center justify-between border-b border-hairline px-4",
            collapsed ? "h-14" : "h-[76px]"
          )}
        >
          <div className="min-w-0 overflow-hidden">
            <BrandMark variant={collapsed ? "mark" : "full"} size="md" />
          </div>
          <button
            onClick={onToggle}
            className="focus-ring hidden rounded-md p-1 text-content-muted hover:bg-surface-hover hover:text-content-primary lg:block"
            aria-label={collapsed ? t("nav.expandSidebar") : t("nav.collapseSidebar")}
          >
            <ChevronsLeft className={cn("h-4 w-4 transition-transform", collapsed && "rotate-180")} />
          </button>
        </div>

        {/* Bottom padding clears the iOS home indicator so the last nav item
            stays tappable in the mobile drawer. */}
        <nav className="flex-1 space-y-5 overflow-y-auto px-3 pt-4 pb-[max(env(safe-area-inset-bottom),1rem)]">
          {navGroups.map((group) => (
            <div key={group.labelKey}>
              {!collapsed && (
                <p className="mb-1.5 px-2 text-[10px] font-semibold uppercase tracking-wider text-content-muted">
                  {t(group.labelKey as TranslationKey)}
                </p>
              )}
              <div className="space-y-0.5">
                {group.items.map((item) => {
                  const isActive = item.to === "/" ? location.pathname === "/" : location.pathname.startsWith(item.to);
                  return (
                    <NavLink
                      key={item.to}
                      to={item.to}
                      end={item.to === "/"}
                      onClick={onCloseMobile}
                      className={cn(
                        // Tap/press feedback on the primary navigation. transform-only, and
                        // neutralised under reduced motion (the global CSS override
                        // cannot touch transforms).
                        "focus-ring relative flex items-center gap-2.5 rounded-lg px-2.5 py-2 text-sm font-medium",
                        "transition-[color,background-color,transform] duration-150",
                        "active:scale-[0.97] motion-reduce:active:scale-100",
                        isActive
                          ? "text-accent-gold"
                          : "text-content-primary hover:bg-surface-hover hover:text-content-primary"
                      )}
                      title={collapsed ? t(item.labelKey as TranslationKey) : undefined}
                    >
                      {isActive && (
                        <motion.span
                          layoutId="sidebar-active-pill"
                          className="absolute inset-0 rounded-lg bg-accent-gold/10"
                          transition={{ type: "spring", stiffness: 380, damping: 32 }}
                        />
                      )}
                      <item.icon className="relative z-10 h-4 w-4 shrink-0" />
                      {!collapsed && <span className="relative z-10 truncate">{t(item.labelKey as TranslationKey)}</span>}
                    </NavLink>
                  );
                })}
              </div>
            </div>
          ))}
        </nav>

        {/* Language lives in the topbar from 640px up, where there is room for
            it beside the theme control. Below that the topbar is already full,
            so it moves here into the mobile drawer — one tap from the menu
            button, not buried in Settings. `sm:hidden` keeps exactly one
            instance visible at any width. */}
        {!collapsed && (
          <div className="shrink-0 border-t border-hairline px-3 py-3 sm:hidden">
            <LanguageSwitcher className="w-full justify-center" />
          </div>
        )}
      </aside>
    </>
  );
}
