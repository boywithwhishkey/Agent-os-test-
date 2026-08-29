import { useEffect, useRef, useState } from "react";
import { Link } from "react-router-dom";
import { AnimatePresence, motion } from "framer-motion";
import { CircleUserRound, KeyRound, LogOut, Plug, Settings as SettingsIcon, ShieldCheck } from "lucide-react";
import { Tooltip } from "@/components/ui/Tooltip";
import { useToast } from "@/components/ui/Toast";
import { getApiBaseUrl, isApiConfigured, resetApiConfig } from "@/lib/api/config";
import { modalMotion } from "@/lib/motion";
import { cn } from "@/lib/utils";

/**
 * Small circular operator/profile control beside the hamburger. THYNACT has
 * no user-account system — this surfaces the one real notion of identity the
 * app has: the operator's local API key session (see lib/api/config.ts) —
 * never invented account fields that don't exist on the backend.
 */
export function AccountPopover() {
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);
  const { push } = useToast();
  const configured = isApiConfigured();

  useEffect(() => {
    if (!open) return;
    // pointerdown (not click) so this can't race the toggle button's own
    // click handler, and so it fires consistently on touch as well as mouse.
    const onPointerDown = (e: PointerEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false);
    };
    const onKeyDown = (e: KeyboardEvent) => e.key === "Escape" && setOpen(false);
    document.addEventListener("pointerdown", onPointerDown);
    document.addEventListener("keydown", onKeyDown);
    return () => {
      document.removeEventListener("pointerdown", onPointerDown);
      document.removeEventListener("keydown", onKeyDown);
    };
  }, [open]);

  const clearSession = () => {
    resetApiConfig();
    setOpen(false);
    push({ tone: "info", title: "Operator session cleared", description: "API key removed from this tab." });
  };

  return (
    <div className="relative" ref={ref}>
      <Tooltip content={configured ? "Operator session" : "No operator session"}>
        <button
          type="button"
          onClick={() => setOpen((o) => !o)}
          aria-label="Account and operator session"
          aria-haspopup="menu"
          aria-expanded={open}
          className={cn(
            "focus-ring relative flex h-8 w-8 shrink-0 items-center justify-center rounded-full glass-soft border border-hairline text-content-secondary transition-colors hover:text-accent-violet"
          )}
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

      <AnimatePresence>
        {open && (
          <motion.div
            role="menu"
            aria-label="Operator session"
            initial={modalMotion.initial}
            animate={modalMotion.animate}
            exit={modalMotion.exit}
            transition={modalMotion.transition}
            className="glass-focus absolute left-0 top-full z-50 mt-2 w-64 max-w-[calc(100vw-2rem)] overflow-hidden rounded-2xl border border-hairline"
          >
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
                className="focus-ring flex items-center gap-2.5 rounded-lg px-2.5 py-2 text-sm text-content-secondary transition-colors hover:bg-surface-hover hover:text-content-primary"
              >
                <SettingsIcon className="h-4 w-4" /> Settings
              </Link>
              <Link
                to="/integrations"
                onClick={() => setOpen(false)}
                className="focus-ring flex items-center gap-2.5 rounded-lg px-2.5 py-2 text-sm text-content-secondary transition-colors hover:bg-surface-hover hover:text-content-primary"
              >
                <Plug className="h-4 w-4" /> Connections
              </Link>
              {configured && (
                <button
                  onClick={clearSession}
                  className="focus-ring flex items-center gap-2.5 rounded-lg px-2.5 py-2 text-left text-sm text-accent-red transition-colors hover:bg-accent-red/10"
                >
                  <LogOut className="h-4 w-4" /> Clear session
                </button>
              )}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
