import { cn } from "@/lib/utils";

export function Skeleton({ className }: { className?: string }) {
  return (
    <div
      className={cn(
        // A travelling highlight rather than a flat opacity pulse. The
        // `shimmer` keyframe and its --animate-shimmer token already existed in
        // index.css but nothing used them, so loading states — the most
        // frequently seen moment in the app — fell back to Tailwind's default
        // pulse. background-size must exceed the element so the -400px..400px
        // keyframe sweeps across rather than jumping.
        "animate-shimmer rounded-md bg-surface-hover",
        "bg-[linear-gradient(90deg,transparent_0%,var(--color-surface-raised)_50%,transparent_100%)]",
        "bg-[length:800px_100%] bg-no-repeat",
        className
      )}
      aria-hidden
    />
  );
}

export function SkeletonRows({ rows = 3 }: { rows?: number }) {
  return (
    <div className="space-y-2" role="status" aria-label="Loading">
      {Array.from({ length: rows }).map((_, i) => (
        <Skeleton key={i} className="h-10 w-full" />
      ))}
    </div>
  );
}

export function SkeletonCard() {
  return (
    <div className="glass-panel space-y-3 rounded-2xl border border-hairline p-5" role="status" aria-label="Loading">
      <Skeleton className="h-4 w-1/3" />
      <Skeleton className="h-8 w-1/2" />
      <Skeleton className="h-3 w-2/3" />
    </div>
  );
}
