import { Link } from "react-router-dom";
import { KeyRound } from "lucide-react";

export function AuthRequiredBanner({ className }: { className?: string }) {
  return (
    <div
      className={`flex flex-wrap items-center justify-between gap-3 rounded-lg border border-accent-amber/25 bg-accent-amber/5 px-4 py-2.5 text-sm text-content-secondary ${className ?? ""}`}
    >
      <span className="flex items-center gap-2">
        <KeyRound className="h-4 w-4 shrink-0 text-accent-amber" />
        Operator authentication required for connector actions.
      </span>
      <Link to="/settings" className="shrink-0 font-medium text-accent-violet hover:underline">
        Configure API key
      </Link>
    </div>
  );
}
