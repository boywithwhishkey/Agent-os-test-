import type { ReactNode } from "react";
import { Link } from "react-router-dom";
import { AlertTriangle, Inbox, Loader2, WifiOff, Clock, KeyRound, SearchX } from "lucide-react";
import { Button } from "./Button";
import { ApiError } from "@/lib/api/client";

export function EmptyState({
  icon,
  title,
  description,
  action,
}: {
  icon?: ReactNode;
  title: string;
  description?: string;
  action?: ReactNode;
}) {
  return (
    <div className="flex flex-col items-center justify-center gap-3 rounded-xl border border-dashed border-surface bg-surface-canvas px-6 py-14 text-center">
      <div className="flex h-11 w-11 items-center justify-center rounded-full bg-surface-hover text-content-muted">
        {icon ?? <Inbox className="h-5 w-5" />}
      </div>
      <div>
        <p className="text-sm font-medium text-content-primary">{title}</p>
        {description && <p className="mt-1 max-w-sm text-sm text-content-muted">{description}</p>}
      </div>
      {action}
    </div>
  );
}

export function LoadingState({ label = "Loading…" }: { label?: string }) {
  return (
    <div className="flex flex-col items-center justify-center gap-3 py-14 text-content-muted" role="status">
      <Loader2 className="h-5 w-5 animate-spin" />
      <p className="text-sm">{label}</p>
    </div>
  );
}

function describeError(error: unknown): { title: string; description: string; icon: ReactNode } {
  if (error instanceof ApiError) {
    if (error.isTimeout) {
      return { title: "Request timed out", description: error.detail, icon: <Clock className="h-5 w-5" /> };
    }
    if (error.isNetworkError) {
      return {
        title: "Can't reach the API",
        description: error.detail,
        icon: <WifiOff className="h-5 w-5" />,
      };
    }
    if (error.status === 404) {
      return { title: "Not found", description: error.detail, icon: <SearchX className="h-5 w-5" /> };
    }
    return {
      title: `Request failed (${error.status})`,
      description: error.detail,
      icon: <AlertTriangle className="h-5 w-5" />,
    };
  }
  return {
    title: "Something went wrong",
    description: error instanceof Error ? error.message : "Unexpected error",
    icon: <AlertTriangle className="h-5 w-5" />,
  };
}

// A missing/invalid operator API key is a setup state, not a failure of the
// app or the API — it gets a compact, neutral banner instead of the same
// alarm-red panel a genuine error gets (see CLAUDE.md's Integration Hub UX
// rules, applied app-wide here rather than only on the Integrations page).
function AuthRequiredState({ description }: { description: string }) {
  return (
    <div className="flex flex-wrap items-center justify-between gap-3 rounded-xl border border-surface bg-surface-canvas px-4 py-3.5 text-sm text-content-secondary">
      <span className="flex items-center gap-2">
        <KeyRound className="h-4 w-4 shrink-0 text-accent-amber" />
        {description}
      </span>
      <Link
        to="/settings"
        className="focus-ring shrink-0 rounded-lg border border-surface px-3 py-1.5 text-xs font-medium text-content-primary hover:bg-surface-hover"
      >
        Configure API key
      </Link>
    </div>
  );
}

export function ErrorState({ error, onRetry }: { error: unknown; onRetry?: () => void }) {
  if (error instanceof ApiError && error.isUnauthorized) {
    return <AuthRequiredState description={error.detail} />;
  }

  const { title, description, icon } = describeError(error);
  const correlationId = error instanceof ApiError ? error.correlationId : null;
  return (
    <div className="flex flex-col items-center justify-center gap-3 rounded-xl border border-accent-red/25 bg-accent-red/5 px-6 py-14 text-center">
      <div className="flex h-11 w-11 items-center justify-center rounded-full bg-accent-red/10 text-accent-red">
        {icon}
      </div>
      <div>
        <p className="text-sm font-medium text-content-primary">{title}</p>
        <p className="mt-1 max-w-sm text-sm text-content-muted">{description}</p>
        {correlationId && (
          <p className="mt-2 font-mono text-[11px] text-content-muted">
            Correlation ID: {correlationId}
          </p>
        )}
      </div>
      {onRetry && (
        <Button variant="outline" size="sm" onClick={onRetry}>
          Try again
        </Button>
      )}
    </div>
  );
}
