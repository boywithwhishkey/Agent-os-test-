import type { ReactNode } from "react";
import { motion } from "framer-motion";
import { sectionReveal, staggerContainer, staggerItem, revealViewport } from "@/lib/motion";
import { cn } from "@/lib/utils";

/** Fades + rises a section into place once, as it enters the viewport. No scroll-jacking — purely `whileInView`. */
export function ScrollReveal({
  children,
  className,
  delay = 0,
}: {
  children: ReactNode;
  className?: string;
  delay?: number;
}) {
  return (
    <motion.div
      className={className}
      variants={sectionReveal}
      initial="hidden"
      whileInView="visible"
      viewport={revealViewport}
      transition={{ delay }}
    >
      {children}
    </motion.div>
  );
}

/** Staggers a group of children in as the group enters the viewport. Pass `StaggerItem` (or any motion child using `staggerItem`) inside. */
export function StaggerGroup({ children, className }: { children: ReactNode; className?: string }) {
  return (
    <motion.div className={className} variants={staggerContainer} initial="hidden" whileInView="visible" viewport={revealViewport}>
      {children}
    </motion.div>
  );
}

export function StaggerItem({ children, className }: { children: ReactNode; className?: string }) {
  return (
    <motion.div className={cn(className)} variants={staggerItem}>
      {children}
    </motion.div>
  );
}
