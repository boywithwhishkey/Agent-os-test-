import { useEffect, useState } from "react";
import { Outlet, useLocation } from "react-router-dom";
import { AnimatePresence, motion } from "framer-motion";
import { Sidebar } from "./Sidebar";
import { Topbar } from "./Topbar";
import { CommandPalette } from "./CommandPalette";
import { AmbientBackground } from "./AmbientBackground";
import { pageEnter } from "@/lib/motion";

export function AppShell() {
  const [collapsed, setCollapsed] = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);
  const [paletteOpen, setPaletteOpen] = useState(false);
  const location = useLocation();

  useEffect(() => {
    const onKeyDown = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === "k") {
        e.preventDefault();
        setPaletteOpen((o) => !o);
      }
    };
    document.addEventListener("keydown", onKeyDown);
    return () => document.removeEventListener("keydown", onKeyDown);
  }, []);

  return (
    // No opaque background here — body's gradient (index.css) must show
    // through. An earlier version had bg-surface-canvas on this element,
    // which is fully opaque and was silently hiding the entire ambient
    // background system behind it; caught by actually rendering the app.
    // min-h-screen stays as the fallback and min-h-dvh wins where supported:
    // on iOS Safari 100vh counts the collapsing browser chrome, so a vh-only
    // shell is taller than the visible viewport and the page jiggles as the
    // toolbar hides. dvh tracks the viewport that is actually visible.
    <div className="relative flex min-h-screen min-h-dvh overflow-x-hidden">
      <AmbientBackground />
      <Sidebar
        collapsed={collapsed}
        onToggle={() => setCollapsed((c) => !c)}
        mobileOpen={mobileOpen}
        onCloseMobile={() => setMobileOpen(false)}
      />
      <div className="relative z-10 flex min-w-0 flex-1 flex-col">
        <Topbar onOpenMobileNav={() => setMobileOpen(true)} onOpenCommandPalette={() => setPaletteOpen(true)} />
        <main
          id="main-content"
          tabIndex={-1}
          className="mx-auto w-full max-w-[1400px] flex-1 px-4 py-6 outline-none sm:px-6 lg:px-8"
        >
          <AnimatePresence mode="wait">
            <motion.div
              key={location.pathname}
              variants={pageEnter}
              initial="hidden"
              animate="visible"
              exit="exit"
            >
              <Outlet />
            </motion.div>
          </AnimatePresence>
        </main>
      </div>
      <CommandPalette open={paletteOpen} onClose={() => setPaletteOpen(false)} />
    </div>
  );
}
