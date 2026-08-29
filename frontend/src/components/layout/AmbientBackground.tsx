import { useMemo } from "react";
import { motion, useReducedMotion, useScroll, useSpring, useTransform } from "framer-motion";

// A handful of fixed (not random-per-render) data points — sparse by design,
// never hundreds of DOM nodes. Positions are deterministic percentages so
// server/client and every re-render agree.
const DATA_POINTS = [
  { x: 8, y: 14, delay: 0 },
  { x: 22, y: 62, delay: 0.6 },
  { x: 38, y: 28, delay: 1.2 },
  { x: 54, y: 78, delay: 0.3 },
  { x: 67, y: 18, delay: 1.6 },
  { x: 79, y: 52, delay: 0.9 },
  { x: 88, y: 84, delay: 1.9 },
  { x: 46, y: 46, delay: 2.2 },
  { x: 15, y: 90, delay: 1.4 },
  { x: 92, y: 10, delay: 0.5 },
];

/**
 * Layer 2–4 of THYNACT's ambient technical background: a faint grid, two
 * slow-drifting mesh-gradient glows, and sparse floating data points. Fixed
 * behind the whole app shell so every page shares one continuous canvas
 * instead of feeling like stacked, disconnected sections. Layer 1 (the deep
 * near-black/near-white base) is `body`'s own background-color in index.css.
 */
export function AmbientBackground() {
  const reduceMotion = useReducedMotion();
  const { scrollY } = useScroll();
  const smoothScroll = useSpring(scrollY, { stiffness: 60, damping: 20, mass: 0.5 });
  // Background layers move slower than the foreground content — classic parallax depth cue.
  const gridY = useTransform(smoothScroll, (v) => (reduceMotion ? 0 : v * 0.04));
  const meshY = useTransform(smoothScroll, (v) => (reduceMotion ? 0 : v * 0.08));

  const points = useMemo(() => DATA_POINTS, []);

  return (
    <div className="pointer-events-none fixed inset-0 z-0 overflow-hidden" aria-hidden>
      <motion.div className="absolute inset-[-64px] bg-technical-grid opacity-60" style={{ y: gridY }} />

      <motion.div className="absolute inset-0" style={{ y: meshY }}>
        <div className="absolute left-[-10%] top-[-15%] h-[55vh] w-[55vh] rounded-full bg-accent-gold/[0.08] blur-[120px] animate-drift" />
        <div className="absolute bottom-[-15%] right-[-10%] h-[60vh] w-[60vh] rounded-full bg-ambient-wine/[0.09] blur-[130px] animate-drift-slow" />
      </motion.div>

      {!reduceMotion && (
        <div className="absolute inset-0">
          {points.map((p, i) => (
            <span
              key={i}
              className="absolute h-1 w-1 rounded-full bg-accent-gold-light/30 animate-float"
              style={{ left: `${p.x}%`, top: `${p.y}%`, animationDelay: `${p.delay}s` }}
            />
          ))}
        </div>
      )}
    </div>
  );
}
