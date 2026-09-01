import type { ReactNode } from "react";
import { Link } from "react-router-dom";
import { AlertTriangle, Inbox, Loader2, WifiOff, Clock, Lock, SearchX, ServerCog } from "lucide-react";
import { Button } from "./Button";
import { ApiError } from "@/lib/api/client";
import { DEFAULT_BASE_URL, getApiBaseUrl, setApiBaseUrl } from "@/lib/api/config";

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
    <div className="glass-ambient flex flex-col items-center justify-center gap-3 rounded-xl border border-dashed border-hairline px-6 py-14 text-center">
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
    <div className="glass-soft flex flex-wrap items-center justify-between gap-3 rounded-xl border border-hairline px-4 py-3.5 text-sm">
      <span className="flex items-center gap-2.5">
        <span className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-accent-gold/10 text-accent-gold">
          <Lock className="h-3.5 w-3.5" />
        </span>
        <span>
          <span className="block font-medium text-content-primary">Operator authentication required</span>
          <span className="block text-xs text-content-muted">
            This view becomes available after authentication — <span>{description}</span>
          </span>
        </span>
      </span>
      <Link
        to="/settings"
        className="focus-ring shrink-0 rounded-lg border border-hairline px-3 py-1.5 text-xs font-medium text-content-primary hover:bg-surface-hover"
      >
        Authenticate
      </Link>
    </div>
  );
}

// The server itself has no operator key configured, so NO credential the user
// could supply would work. Sending them to the Settings page — which is what
// this used to do, because 503 was folded into isUnauthorized — is actively
// misleading: the fix is on the deployment, not on them.
function ServiceUnconfiguredState({ description }: { description: string }) {
  return (
    <div className="glass-soft flex flex-wrap items-center gap-3 rounded-xl border border-accent-amber/25 px-4 py-3.5 text-sm">
      <span className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-accent-amber/10 text-accent-amber">
        <ServerCog className="h-3.5 w-3.5" />
      </span>
      <span className="min-w-0">
        <span className="block font-medium text-content-primary">
          Service temporarily unavailable
        </span>
        <span className="block text-xs text-content-muted">{description}</span>
      </span>
    </div>
  );
}

function ForbiddenState({ description }: { description: string }) {
  return (
    <div className="glass-soft flex flex-wrap items-center gap-3 rounded-xl border border-accent-red/25 px-4 py-3.5 text-sm">
      <span className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-accent-red/10 text-accent-red">
        <Lock className="h-3.5 w-3.5" />
      </span>
      <span className="min-w-0">
        <span className="block font-medium text-content-primary">Permission denied</span>
        <span className="block text-xs text-content-muted">{description}</span>
      </span>
    </div>
  );
}

export function ErrorState({ error, onRetry }: { error: unknown; onRetry?: () => void }) {
  // Three distinct states that were previously one. Order matters only in that
  // each is mutually exclusive by status code.
  if (error instanceof ApiError && error.isUnauthorized) {
    return <AuthRequiredState description={error.detail} />;
  }
  if (error instanceof ApiError && error.isForbidden) {
    return <ForbiddenState description={error.detail} />;
  }
  if (error instanceof ApiError && error.isUnavailable) {
    return <ServiceUnconfiguredState description={error.detail} />;
  }

  const { title, description, icon } = describeError(error);
  const correlationId = error instanceof ApiError ? error.correlationId : null;
  // A network failure is almost always "the app is pointed at the wrong API",
  // so name the URL it actually tried and offer a one-click way back to the
  // default. Without this the user sees "Can't reach the API" with no idea
  // which address failed or how to change it.
  // Network failures are wrapped in ApiError with isNetworkError set — they are
  // NOT plain exceptions, so testing `instanceof ApiError` alone would never
  // match and this hint would never render.
  const isNetworkError =
    error instanceof ApiError ? error.isNetworkError || error.isTimeout : true;
  const attemptedBaseUrl = isNetworkError ? getApiBaseUrl() : null;
  return (
    <div className="glass-soft flex flex-col items-center justify-center gap-3 rounded-xl border border-accent-red/20 px-6 py-14 text-center">
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
      {attemptedBaseUrl && (
        <p className="max-w-sm break-all font-mono text-[11px] text-content-muted">
          Tried: {attemptedBaseUrl}
        </p>
      )}
      <div className="flex flex-wrap items-center justify-center gap-2">
        {onRetry && (
          <Button variant="outline" size="sm" onClick={onRetry}>
            Try again
          </Button>
        )}
        {attemptedBaseUrl && attemptedBaseUrl !== DEFAULT_BASE_URL && (
          <Button
            variant="ghost"
            size="sm"
            onClick={() => {
              setApiBaseUrl(DEFAULT_BASE_URL);
              onRetry?.();
            }}
          >
            Reset API URL
          </Button>
        )}
      </div>
    </div>
  );
}
