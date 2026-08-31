import type { HTMLAttributes } from "react";
import { motion, useReducedMotion } from "framer-motion";
import { cn } from "@/lib/utils";
import { glassAppear, revealViewport } from "@/lib/motion";

// A translucent floating pane, not a bordered box — depth comes from
// backdrop blur + a soft shadow, separation from a hairline tonal edge
// rather than a bright outline. See index.css's glass-panel utility.
export function Card({ className, ...props }: HTMLAttributes<HTMLDivElement>) {
  const reduceMotion = useReducedMotion();

  // Card is the default content surface on 14+ pages, so animating it here is
  // what makes entrances feel consistent app-wide instead of a per-page
  // sprinkle. Uses the shared `glassAppear` token (a pane resolving out of
  // blur) rather than a bespoke variant — see CLAUDE.md on not hand-rolling
  // new Framer variants for this.
  //
  // whileInView + `once` means each card animates a single time as it enters,
  // so a long page does not re-run animations while scrolling, and cards below
  // the fold are not all animating at once on load.
  if (reduceMotion) {
    return (
      <div className={cn("glass-panel rounded-2xl border border-hairline", className)} {...props} />
    );
  }

  return (
    <motion.div
      initial="hidden"
      whileInView="visible"
      viewport={revealViewport}
      variants={glassAppear}
      className={cn("glass-panel rounded-2xl border border-hairline", className)}
      {...(props as React.ComponentProps<typeof motion.div>)}
    />
  );
}

export function CardHeader({ className, ...props }: HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={cn(
        "flex flex-wrap items-center justify-between gap-3 border-b border-hairline px-5 py-4",
        className
      )}
      {...props}
    />
  );
}

export function CardTitle({ className, ...props }: HTMLAttributes<HTMLHeadingElement>) {
  return <h3 className={cn("text-sm font-semibold text-content-primary", className)} {...props} />;
}

export function CardContent({ className, ...props }: HTMLAttributes<HTMLDivElement>) {
  return <div className={cn("p-5", className)} {...props} />;
}
