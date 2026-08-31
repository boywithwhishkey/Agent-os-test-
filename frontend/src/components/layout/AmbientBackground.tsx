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
 * One liquid "infinity" blob.
 *
 * Each is a morphing rounded shape (animate-blob drives border-radius, which
 * is what makes it read as a soft body rather than a circle) filled with a
 * two-stop gradient: a lit magenta/violet edge falling away into near-black,
 * so the shape looks like a form catching light rather than a flat colour
 * patch. A slow counter-rotation moves the highlight around the body.
 *
 * `blur` is deliberately modest — over-blurring turns these back into the
 * generic glow blobs this design replaced. The softness comes from the
 * gradient falloff, not from smearing the whole shape.
 */
function Blob({
  className,
  gradient,
  blur,
  spin = "animate-blob",
}: {
  className: string;
  gradient: string;
  blur: string;
  spin?: string;
}) {
  return (
    <div className={`absolute ${className}`}>
      <div className={`h-full w-full ${spin}`} style={{ filter: `blur(${blur})` }}>
        <div className="h-full w-full animate-blob-turn" style={{ background: gradient }} />
      </div>
    </div>
  );
}

/**
 * Layer 2+ of THYNACT's ambient background: drifting liquid blobs in a
 * gold/magenta duotone over the near-black base, a faint technical grid, and sparse floating
 * points. Fixed behind the whole app shell so every page shares one
 * continuous canvas instead of feeling like stacked, disconnected sections.
 * Layer 1 (the deep base colour) is `body`'s own background-color in
 * index.css.
 *
 * Scroll response: each depth band is driven by the same spring-smoothed
 * scroll value at a different rate, so the field parallaxes as you scroll and
 * settles smoothly rather than tracking the wheel 1:1. Everything animates
 * transform/opacity/filter only — no layout properties — so scrolling stays
 * cheap. All of it is disabled under prefers-reduced-motion.
 */
export function AmbientBackground() {
  const reduceMotion = useReducedMotion();
  const { scrollY } = useScroll();
  // Softer spring than a raw scroll binding: the background keeps moving for a
  // beat after the wheel stops, which is what makes it feel "liquid" instead
  // of glued to the scrollbar.
  const smoothScroll = useSpring(scrollY, { stiffness: 48, damping: 22, mass: 0.6 });

  // Depth bands. Larger multiplier = nearer the viewer = moves more.
  const gridY = useTransform(smoothScroll, (v) => (reduceMotion ? 0 : v * 0.03));
  const farY = useTransform(smoothScroll, (v) => (reduceMotion ? 0 : v * 0.06));
  const midY = useTransform(smoothScroll, (v) => (reduceMotion ? 0 : v * 0.14));
  const nearY = useTransform(smoothScroll, (v) => (reduceMotion ? 0 : v * 0.24));
  // A little lateral drift as well, so the field does not feel like it is only
  // sliding on one axis.
  const midX = useTransform(smoothScroll, (v) => (reduceMotion ? 0 : v * -0.03));
  const nearX = useTransform(smoothScroll, (v) => (reduceMotion ? 0 : v * 0.04));

  const points = useMemo(() => DATA_POINTS, []);

  return (
    <div
      /* The blobs are tuned for a near-black field. At full strength on a light
         background they wash straight over body text — sidebar labels and card
         headings were getting lost in the purple. Light mode gets a quieter
         version of the same field rather than a different design.

         Raised from 0.22 once the field became a duotone: at 0.22 the muted
         gold and the magenta both faded to the same near-neutral grey, so the
         two hues stopped being distinguishable and the page read colourless.
         Legibility still holds because the cards are glass over this, not
         transparent. */
      className="pointer-events-none fixed inset-0 z-0 overflow-hidden opacity-[0.34] dark:opacity-100"
      aria-hidden
    >
      <motion.div className="absolute inset-[-64px] bg-technical-grid opacity-40" style={{ y: gridY }} />

      {/* Far band — the largest, dimmest masses. */}
      <motion.div className="absolute inset-0" style={{ y: farY }}>
        <Blob
          className="left-[-22vh] top-[-18vh] h-[66vh] w-[54vh]"
          blur="26px"
          spin="animate-blob-slow"
          gradient="linear-gradient(155deg, color-mix(in srgb, var(--color-ambient-gold) 66%, transparent) 0%, color-mix(in srgb, var(--color-ambient-magenta) 20%, transparent) 40%, color-mix(in srgb, var(--color-ambient-plum) 62%, transparent) 62%, transparent 80%)"
        />
        <Blob
          className="bottom-[-26vh] right-[-16vh] h-[62vh] w-[58vh]"
          blur="30px"
          gradient="linear-gradient(200deg, color-mix(in srgb, var(--color-ambient-magenta) 34%, transparent) 0%, color-mix(in srgb, var(--color-ambient-gold) 50%, transparent) 42%, color-mix(in srgb, var(--color-ambient-slate) 44%, transparent) 66%, transparent 84%)"
        />
      </motion.div>

      {/* Mid band — the hero shapes, the ones you actually read as bodies. */}
      <motion.div className="absolute inset-0" style={{ y: midY, x: midX }}>
        <Blob
          className="right-[-10vh] top-[-14vh] h-[48vh] w-[46vh]"
          blur="18px"
          gradient="linear-gradient(165deg, color-mix(in srgb, var(--color-ambient-gold) 84%, transparent) 0%, color-mix(in srgb, var(--color-ambient-magenta) 24%, transparent) 38%, color-mix(in srgb, var(--color-ambient-plum) 56%, transparent) 58%, transparent 78%)"
        />
        <Blob
          className="right-[2vh] top-[16vh] h-[54vh] w-[50vh]"
          blur="20px"
          spin="animate-blob-slow"
          gradient="linear-gradient(190deg, color-mix(in srgb, var(--color-ambient-magenta) 46%, transparent) 0%, color-mix(in srgb, var(--color-ambient-plum) 58%, transparent) 46%, color-mix(in srgb, var(--color-ambient-navy) 50%, transparent) 66%, transparent 84%)"
        />
      </motion.div>

      {/* Near band — smaller, brighter, moves most on scroll. */}
      <motion.div className="absolute inset-0" style={{ y: nearY, x: nearX }}>
        <Blob
          className="bottom-[4vh] left-[-20vh] h-[42vh] w-[38vh]"
          blur="20px"
          gradient="linear-gradient(140deg, color-mix(in srgb, var(--color-ambient-gold) 54%, transparent) 0%, color-mix(in srgb, var(--color-ambient-magenta) 18%, transparent) 46%, color-mix(in srgb, var(--color-ambient-plum) 44%, transparent) 66%, transparent 84%)"
        />
        <Blob
          className="left-[36vh] top-[52vh] h-[34vh] w-[32vh]"
          blur="22px"
          spin="animate-blob-slow"
          gradient="linear-gradient(210deg, color-mix(in srgb, var(--color-ambient-magenta) 40%, transparent) 0%, color-mix(in srgb, var(--color-ambient-gold) 42%, transparent) 44%, color-mix(in srgb, var(--color-ambient-plum) 50%, transparent) 68%, transparent 84%)"
        />
      </motion.div>

      {!reduceMotion && (
        <div className="absolute inset-0">
          {points.map((p, i) => (
            <span
              key={i}
              className={`absolute h-1 w-1 rounded-full animate-float ${
                i % 2 === 0 ? "bg-ambient-gold/40" : "bg-ambient-magenta/40"
              }`}
              style={{ left: `${p.x}%`, top: `${p.y}%`, animationDelay: `${p.delay}s` }}
            />
          ))}
        </div>
      )}
    </div>
  );
}
