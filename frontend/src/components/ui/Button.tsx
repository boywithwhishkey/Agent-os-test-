import { forwardRef, type ButtonHTMLAttributes } from "react";
import { Loader2 } from "lucide-react";
import { cn } from "@/lib/utils";

type Variant = "primary" | "secondary" | "ghost" | "danger" | "outline";
type Size = "sm" | "md" | "lg" | "icon";

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: Variant;
  size?: Size;
  loading?: boolean;
}

const variantStyles: Record<Variant, string> = {
  primary:
    "bg-accent-violet text-white hover:bg-accent-violet/90 shadow-sm shadow-accent-violet/20",
  secondary:
    "bg-surface-hover text-content-primary hover:bg-surface-hover/80 border border-surface",
  outline:
    "border border-surface text-content-primary hover:bg-surface-hover bg-transparent",
  ghost: "text-content-secondary hover:bg-surface-hover hover:text-content-primary",
  danger: "bg-accent-red text-white hover:bg-accent-red/90",
};

// Touch targets: 32-36px is comfortable with a mouse but below the ~44px
// guideline for fingers, so the smaller sizes grow on phones only. Desktop
// density is deliberately unchanged. (Tailwind's `pointer-coarse` variant does
// not compile in this version — verified against the built CSS — so this keys
// off viewport width instead.)
const sizeStyles: Record<Size, string> = {
  sm: "h-8 max-sm:h-10 px-3 max-sm:px-3.5 text-xs gap-1.5",
  md: "h-9 max-sm:h-11 px-4 text-sm gap-2",
  lg: "h-11 px-5 text-sm gap-2",
  icon: "h-9 w-9 max-sm:h-11 max-sm:w-11 p-0 justify-center",
};

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant = "primary", size = "md", loading, disabled, children, ...props }, ref) => {
    return (
      <button
        ref={ref}
        disabled={disabled || loading}
        className={cn(
          // transform is included in the transition so the press feedback below
          // animates instead of snapping. transform/opacity only — no layout
          // properties — so this stays cheap on every press.
          "focus-ring inline-flex items-center rounded-lg font-medium",
          "transition-[background-color,border-color,color,transform] duration-150",
          // Tactile press feedback. Neutralised under prefers-reduced-motion,
          // which the global CSS override cannot do for transforms.
          "active:scale-[0.97] motion-reduce:active:scale-100",
          "disabled:cursor-not-allowed disabled:opacity-50 disabled:active:scale-100",
          variantStyles[variant],
          sizeStyles[size],
          className
        )}
        {...props}
      >
        {loading && <Loader2 className="h-4 w-4 animate-spin" aria-hidden />}
        {children}
      </button>
    );
  }
);
Button.displayName = "Button";
