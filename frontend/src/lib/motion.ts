import type { Transition, Variants } from "framer-motion";

// THYNACT's single reusable motion language: precise, technical, fluid —
// never bouncy or cartoonish. Every spring here is critically-damped-ish
// (high damping relative to stiffness) so motion settles instead of wobbling.
const preciseSpring: Transition = { type: "spring", stiffness: 260, damping: 30, mass: 0.9 };
const softSpring: Transition = { type: "spring", stiffness: 200, damping: 26 };

export const motionTokens = { preciseSpring, softSpring };

export const pageEnter: Variants = {
  hidden: { opacity: 0, y: 10 },
  visible: { opacity: 1, y: 0, transition: { duration: 0.32, ease: [0.16, 1, 0.3, 1] } },
  exit: { opacity: 0, y: -6, transition: { duration: 0.18, ease: [0.4, 0, 1, 1] } },
};

export const sectionReveal: Variants = {
  hidden: { opacity: 0, y: 18 },
  visible: { opacity: 1, y: 0, transition: { duration: 0.5, ease: [0.16, 1, 0.3, 1] } },
};

export const staggerContainer: Variants = {
  hidden: {},
  visible: { transition: { staggerChildren: 0.06, delayChildren: 0.04 } },
};

export const staggerItem: Variants = {
  hidden: { opacity: 0, y: 14 },
  visible: { opacity: 1, y: 0, transition: { duration: 0.4, ease: [0.16, 1, 0.3, 1] } },
};

export const glassAppear: Variants = {
  hidden: { opacity: 0, scale: 0.98, filter: "blur(4px)" },
  visible: { opacity: 1, scale: 1, filter: "blur(0px)", transition: { duration: 0.35, ease: [0.16, 1, 0.3, 1] } },
};

export const drawerMotion = {
  initial: { x: "100%" },
  animate: { x: 0 },
  exit: { x: "100%" },
  transition: preciseSpring,
};

export const sheetMotion = {
  initial: { y: "100%" },
  animate: { y: 0 },
  exit: { y: "100%" },
  transition: preciseSpring,
};

export const modalMotion = {
  initial: { opacity: 0, scale: 0.97, y: 8 },
  animate: { opacity: 1, scale: 1, y: 0 },
  exit: { opacity: 0, scale: 0.98, y: 6 },
  transition: softSpring,
};

export const hoverFloat = {
  rest: { y: 0 },
  hover: { y: -3, transition: preciseSpring },
};

export const fadeThrough: Variants = {
  hidden: { opacity: 0 },
  visible: { opacity: 1, transition: { duration: 0.25, ease: "easeOut" } },
  exit: { opacity: 0, transition: { duration: 0.15, ease: "easeIn" } },
};

export const metricReveal: Variants = {
  hidden: { opacity: 0, y: 8 },
  visible: { opacity: 1, y: 0, transition: { duration: 0.4, ease: [0.16, 1, 0.3, 1] } },
};

/** Standard viewport config for scroll-triggered reveals — fires once, slightly before full entry. */
export const revealViewport = { once: true, margin: "-80px 0px -80px 0px" } as const;
