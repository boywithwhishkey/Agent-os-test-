import { useEffect, useLayoutEffect, useRef, useState } from "react";
import { createPortal } from "react-dom";
import { Link } from "react-router-dom";
import { AnimatePresence, motion } from "framer-motion";
import { CircleUserRound, KeyRound, LogOut, Plug, Settings as SettingsIcon, ShieldCheck } from "lucide-react";
import { Tooltip } from "@/components/ui/Tooltip";
import { useToast } from "@/components/ui/Toast";
import { getApiBaseUrl, isApiConfigured, resetApiConfig } from "@/lib/api/config";
import { modalMotion, sheetMotion } from "@/lib/motion";
import { cn } from "@/lib/utils";

const SHEET_BREAKPOINT = 640; // matches Tailwind's `sm` — below this, use a bottom sheet instead of a floating popover.
const PANEL_WIDTH = 288; // px, matches w-72 below
const VIEWPORT_MARGIN = 16; // px safe margin so the panel never touches the screen edge

/**
 * Small circular operator/profile control beside the sidebar hamburger.
 * THYNACT has no user-account system — this surfaces the one real notion
 * of identity the app has: the operator's local API-key session (see
 * lib/api/config.ts) — never invented account fields that don't exist on
 * the backend.
 *
 * Rendered through a portal to document.body (like Drawer/Dialog/
 * CommandPalette elsewhere in this codebase — this component was
 * previously the one inline exception, which is the most likely root
 * cause of any "opens behind/clipped" report: an inline-positioned
 * descendant is at the mercy of every ancestor's stacking context,
 * transform, and overflow, none of which a portal is subject to).
 * Position is computed from the trigger button's real
 * getBoundingClientRect() and clamped to stay fully on-screen — not
 * assumed from which edge of the toolbar it happens to sit near. Below
 * the `sm` breakpoint it renders as a full-width bottom sheet instead of
 * a floating popover, which is unclippable by construction.
 */
export function AccountPopover() {
  const [open, setOpen] = useState(false);
  const [isSheet, setIsSheet] = useState(
    () => typeof window !== "undefined" && window.innerWidth < SHEET_BREAKPOINT
  );
  const [coords, setCoords] = useState<{ top: number; left: number } | null>(null);
  const triggerRef = useRef<HTMLButtonElement>(null);
  const panelRef = useRef<HTMLDivElement>(null);
  const { push } = useToast();
  const configured = isApiConfigured();

  const reposition = () => {
    const sheet = window.innerWidth < SHEET_BREAKPOINT;
    setIsSheet(sheet);
    if (sheet || !triggerRef.current) {
      setCoords(null);
      return;
    }
    const rect = triggerRef.current.getBoundingClientRect();
    const left = Math.min(Math.max(rect.left, VIEWPORT_MARGIN), window.innerWidth - PANEL_WIDTH - VIEWPORT_MARGIN);
    const top = Math.min(rect.bottom + 8, window.innerHeight - VIEWPORT_MARGIN);
    setCoords({ top, left: Math.max(left, VIEWPORT_MARGIN) });
  };

  // Recompute position synchronously before paint so the panel never
  // flashes at a stale/zero position on open.
  useLayoutEffect(() => {
    if (open) reposition();
  }, [open]);

  useEffect(() => {
    if (!open) return;
    const onPointerDown = (e: PointerEvent) => {
      const target = e.target as Node;
      if (triggerRef.current?.contains(target)) return;
      if (panelRef.current?.contains(target)) return;
      setOpen(false);
    };
    const onKeyDown = (e: KeyboardEvent) => e.key === "Escape" && setOpen(false);
    const onViewportChange = () => reposition();
    document.addEventListener("pointerdown", onPointerDown);
    document.addEventListener("keydown", onKeyDown);
    window.addEventListener("resize", onViewportChange);
    window.addEventListener("orientationchange", onViewportChange);
    return () => {
      document.removeEventListener("pointerdown", onPointerDown);
      document.removeEventListener("keydown", onKeyDown);
      window.removeEventListener("resize", onViewportChange);
      window.removeEventListener("orientationchange", onViewportChange);
    };
  }, [open]);

  const clearSession = () => {
    resetApiConfig();
    setOpen(false);
    push({ tone: "info", title: "Operator session cleared", description: "API key removed from this tab." });
  };

  const menuContent = (
    <>
      <div className="flex items-center gap-2.5 border-b border-hairline px-4 py-3">
        <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-accent-violet/10 text-accent-violet">
          <CircleUserRound className="h-4.5 w-4.5" />
        </div>
        <div className="min-w-0">
          <p className="truncate text-sm font-medium text-content-primary">Operator</p>
          <p className="truncate text-xs text-content-muted">{getApiBaseUrl()}</p>
        </div>
      </div>

      <div className="px-4 py-3 text-xs">
        {configured ? (
          <span className="inline-flex items-center gap-1.5 text-accent-green">
            <ShieldCheck className="h-3.5 w-3.5" /> API key configured
          </span>
        ) : (
          <span className="inline-flex items-center gap-1.5 text-accent-amber">
            <KeyRound className="h-3.5 w-3.5" /> No API key set
          </span>
        )}
      </div>

      <div className="flex flex-col gap-0.5 px-2 pb-2">
        <Link
          to="/settings"
          onClick={() => setOpen(false)}
          className="focus-ring flex items-center gap-2.5 rounded-lg px-2.5 py-2.5 text-sm text-content-secondary transition-colors hover:bg-surface-hover hover:text-content-primary"
        >
          <SettingsIcon className="h-4 w-4" /> Settings
        </Link>
        <Link
          to="/integrations"
          onClick={() => setOpen(false)}
          className="focus-ring flex items-center gap-2.5 rounded-lg px-2.5 py-2.5 text-sm text-content-secondary transition-colors hover:bg-surface-hover hover:text-content-primary"
        >
          <Plug className="h-4 w-4" /> Connections
        </Link>
        {configured && (
          <button
            onClick={clearSession}
            className="focus-ring flex items-center gap-2.5 rounded-lg px-2.5 py-2.5 text-left text-sm text-accent-red transition-colors hover:bg-accent-red/10"
          >
            <LogOut className="h-4 w-4" /> Clear session
          </button>
        )}
      </div>
    </>
  );

  return (
    <div className="relative">
      <Tooltip content={configured ? "Operator session" : "No operator session"}>
        <button
          ref={triggerRef}
          type="button"
          onClick={() => setOpen((o) => !o)}
          aria-label="Account and operator session"
          aria-haspopup="menu"
          aria-expanded={open}
          className="focus-ring relative flex h-9 w-9 shrink-0 items-center justify-center rounded-full glass-soft border border-hairline text-content-secondary transition-colors hover:text-accent-violet"
        >
          <CircleUserRound className="h-4.5 w-4.5" />
          <span
            className={cn(
              "absolute -bottom-0.5 -right-0.5 h-2 w-2 rounded-full ring-2 ring-surface-raised",
              configured ? "bg-accent-green" : "bg-content-muted"
            )}
            aria-hidden
          />
        </button>
      </Tooltip>

      {createPortal(
        <AnimatePresence>
          {open && isSheet && (
            <div className="fixed inset-0 z-[70] flex items-end justify-center">
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                className="absolute inset-0 bg-black/50 backdrop-blur-sm"
                onClick={() => setOpen(false)}
                aria-hidden
              />
              <motion.div
                ref={panelRef}
                role="menu"
                aria-label="Operator session"
                initial={sheetMotion.initial}
                animate={sheetMotion.animate}
                exit={sheetMotion.exit}
                transition={sheetMotion.transition}
                className="glass-focus relative z-10 w-full max-w-md overflow-hidden rounded-t-2xl border border-hairline pb-[max(env(safe-area-inset-bottom),0.5rem)]"
              >
                <div className="mx-auto mt-2 h-1 w-10 rounded-full bg-content-muted/30" aria-hidden />
                {menuContent}
              </motion.div>
            </div>
          )}
          {open && !isSheet && coords && (
            <motion.div
              ref={panelRef}
              role="menu"
              aria-label="Operator session"
              initial={modalMotion.initial}
              animate={modalMotion.animate}
              exit={modalMotion.exit}
              transition={modalMotion.transition}
              style={{ position: "fixed", top: coords.top, left: coords.left, width: PANEL_WIDTH }}
              className="glass-focus z-[70] overflow-hidden rounded-2xl border border-hairline"
            >
              {menuContent}
            </motion.div>
          )}
        </AnimatePresence>,
        document.body
      )}
    </div>
  );
}
