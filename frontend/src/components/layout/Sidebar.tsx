import { NavLink, useLocation } from "react-router-dom";
import { ChevronsLeft } from "lucide-react";
import { motion } from "framer-motion";
import { navGroups } from "@/lib/nav";
import { BrandMark } from "@/components/ui/BrandMark";
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
          "glass-soft fixed inset-y-0 left-0 z-50 flex flex-col border-r border-hairline transition-[width] duration-200 lg:sticky lg:top-0 lg:h-screen lg:translate-x-0",
          collapsed ? "lg:w-[68px]" : "lg:w-64",
          mobileOpen ? "w-64 translate-x-0" : "-translate-x-full lg:translate-x-0"
        )}
      >
        <div className="flex h-14 shrink-0 items-center justify-between border-b border-hairline px-4">
          <div className="overflow-hidden">
            <BrandMark variant={collapsed ? "mark" : "compact"} size="sm" />
          </div>
          <button
            onClick={onToggle}
            className="focus-ring hidden rounded-md p-1 text-content-muted hover:bg-surface-hover hover:text-content-primary lg:block"
            aria-label={collapsed ? "Expand sidebar" : "Collapse sidebar"}
          >
            <ChevronsLeft className={cn("h-4 w-4 transition-transform", collapsed && "rotate-180")} />
          </button>
        </div>

        <nav className="flex-1 space-y-5 overflow-y-auto px-3 py-4">
          {navGroups.map((group) => (
            <div key={group.label}>
              {!collapsed && (
                <p className="mb-1.5 px-2 text-[10px] font-semibold uppercase tracking-wider text-content-muted">
                  {group.label}
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
                        "focus-ring relative flex items-center gap-2.5 rounded-lg px-2.5 py-2 text-sm font-medium transition-colors",
                        isActive
                          ? "text-accent-violet"
                          : "text-content-secondary hover:bg-surface-hover hover:text-content-primary"
                      )}
                      title={collapsed ? item.label : undefined}
                    >
                      {isActive && (
                        <motion.span
                          layoutId="sidebar-active-pill"
                          className="absolute inset-0 rounded-lg bg-accent-violet/10"
                          transition={{ type: "spring", stiffness: 380, damping: 32 }}
                        />
                      )}
                      <item.icon className="relative z-10 h-4 w-4 shrink-0" />
                      {!collapsed && <span className="relative z-10 truncate">{item.label}</span>}
                    </NavLink>
                  );
                })}
              </div>
            </div>
          ))}
        </nav>
      </aside>
    </>
  );
}
