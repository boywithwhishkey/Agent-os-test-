import { useEffect, useRef, useState } from "react";
import { Outlet, useLocation } from "react-router-dom";
import { AnimatePresence, motion } from "framer-motion";
import { Sidebar } from "./Sidebar";
import { Topbar } from "./Topbar";
import { useI18n } from "@/lib/i18n";
import { CommandPalette } from "./CommandPalette";
import { AmbientBackground } from "./AmbientBackground";
import { pageEnter } from "@/lib/motion";

export function AppShell() {
  const { locale } = useI18n();
  const mainRef = useRef<HTMLElement>(null);
  const firstLocaleRun = useRef(true);

  // Replay the copy-settle animation when the language changes.
  //
  // Deliberately NOT `key={locale}` on the content: that remounts the subtree,
  // which would wipe anything the user had typed into a form mid-switch.
  // Toggling the class and forcing a reflow restarts the CSS animation while
  // every component keeps its state, and needs no timer.
  useEffect(() => {
    if (firstLocaleRun.current) {
      firstLocaleRun.current = false;
      return; // don't animate the initial paint
    }
    const el = mainRef.current;
    if (!el) return;
    el.classList.remove("locale-transition");
    void el.offsetWidth; // reflow: restarts the animation
    el.classList.add("locale-transition");
  }, [locale]);
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
    // overflow-x-CLIP, not hidden. `overflow-x: hidden` computes overflow-y to
    // `auto`, which makes this div a scroll container — and the sticky topbar
    // then sticks to THIS box rather than the viewport. Since the box is as
    // tall as its content, the header simply scrolled away on every page.
    // `clip` still clips horizontally but creates no scroll container.
    <div className="relative flex min-h-screen min-h-dvh overflow-x-clip">
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
          ref={mainRef}
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
