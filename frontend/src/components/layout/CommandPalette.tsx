import { useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import { createPortal } from "react-dom";
import { AnimatePresence, motion } from "framer-motion";
import { Search, CornerDownLeft } from "lucide-react";
import { allNavItems } from "@/lib/nav";
import { Input } from "@/components/ui/Input";
import { BrandMark } from "@/components/ui/BrandMark";

export function CommandPalette({ open, onClose }: { open: boolean; onClose: () => void }) {
  const [query, setQuery] = useState("");
  const [activeIndex, setActiveIndex] = useState(0);
  const navigate = useNavigate();

  const results = useMemo(() => {
    const q = query.trim().toLowerCase();
    if (!q) return allNavItems;
    return allNavItems.filter((item) => item.label.toLowerCase().includes(q));
  }, [query]);

  useEffect(() => {
    if (!open) {
      setQuery("");
      setActiveIndex(0);
    }
  }, [open]);

  useEffect(() => {
    setActiveIndex(0);
  }, [query]);

  const go = (to: string) => {
    navigate(to);
    onClose();
  };

  useEffect(() => {
    if (!open) return;
    const onKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
      if (e.key === "ArrowDown") {
        e.preventDefault();
        setActiveIndex((i) => Math.min(i + 1, results.length - 1));
      }
      if (e.key === "ArrowUp") {
        e.preventDefault();
        setActiveIndex((i) => Math.max(i - 1, 0));
      }
      if (e.key === "Enter" && results[activeIndex]) {
        go(results[activeIndex].to);
      }
    };
    document.addEventListener("keydown", onKeyDown);
    return () => document.removeEventListener("keydown", onKeyDown);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [open, results, activeIndex]);

  return createPortal(
    <AnimatePresence>
      {open && (
        <div className="fixed inset-0 z-[60] flex items-start justify-center px-4 pt-24">
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="absolute inset-0 bg-black/50 backdrop-blur-sm"
            onClick={onClose}
            aria-hidden
          />
          <motion.div
            initial={{ opacity: 0, y: -8, scale: 0.98 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: -8, scale: 0.98 }}
            transition={{ duration: 0.12 }}
            role="dialog"
            aria-modal="true"
            aria-label="Command palette"
            className="glass-focus relative z-10 w-full max-w-lg overflow-hidden rounded-xl border border-hairline"
          >
            <div className="relative border-b border-hairline p-3">
              <Search className="pointer-events-none absolute left-6 top-1/2 h-4 w-4 -translate-y-1/2 text-content-muted" />
              <Input
                autoFocus
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="Jump to a screen…"
                className="border-none pl-9 focus-visible:ring-0"
              />
            </div>
            <ul className="max-h-80 overflow-y-auto p-1.5">
              {results.length === 0 && (
                <li className="px-3 py-6 text-center text-sm text-content-muted">No matches</li>
              )}
              {results.map((item, i) => (
                <li key={item.to}>
                  <button
                    onClick={() => go(item.to)}
                    onMouseEnter={() => setActiveIndex(i)}
                    className={`flex w-full items-center justify-between gap-2 rounded-lg px-3 py-2 text-left text-sm ${
                      i === activeIndex
                        ? "bg-accent-gold/10 text-accent-gold"
                        : "text-content-secondary hover:bg-surface-hover"
                    }`}
                  >
                    <span className="flex items-center gap-2.5">
                      <item.icon className="h-4 w-4" />
                      {item.label}
                    </span>
                    {i === activeIndex && <CornerDownLeft className="h-3.5 w-3.5" />}
                  </button>
                </li>
              ))}
            </ul>
            <div className="flex items-center justify-between border-t border-hairline px-3 py-2">
              <BrandMark variant="mark" size="sm" />
              <kbd className="rounded border border-hairline bg-surface-hover px-1.5 py-0.5 font-mono text-[10px] text-content-muted">
                Esc to close
              </kbd>
            </div>
          </motion.div>
        </div>
      )}
    </AnimatePresence>,
    document.body
  );
}
