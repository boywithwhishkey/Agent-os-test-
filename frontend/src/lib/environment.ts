/**
 * Which deployment the user is looking at, derived from the hostname.
 *
 * staging.thynact.com was for a period served from the production deployment,
 * meaning "staging" and production were visually indistinguishable. An operator
 * cannot be expected to check an asset hash before clicking a destructive
 * action, so non-production deployments say so on screen.
 *
 * Mirrors the API-host rule in lib/api/config.ts: only the real production
 * hostname counts as production.
 */
export type DeploymentEnvironment = "production" | "staging" | "preview" | "local";

// Mirrors PRODUCTION_HOSTS in lib/api/config.ts: Cloudflare serves production
// on the custom domain and on the project's bare pages.dev alias.
const PRODUCTION_HOSTS = new Set(["app.thynact.com", "agent-os-test.pages.dev"]);

export function getDeploymentEnvironment(hostname: string): DeploymentEnvironment {
  if (PRODUCTION_HOSTS.has(hostname)) return "production";
  if (hostname === "staging.thynact.com") return "staging";
  if (hostname.endsWith(".pages.dev")) return "preview";
  if (hostname === "localhost" || hostname === "127.0.0.1" || hostname.endsWith(".local")) {
    return "local";
  }
  // Unknown host: treat as preview rather than production, so an unexpected
  // domain is labelled instead of silently passing as the real thing.
  return "preview";
}

/** Label for the environment badge, or null in production (no badge there). */
export function getEnvironmentLabel(hostname: string): string | null {
  const environment = getDeploymentEnvironment(hostname);
  if (environment === "production") return null;
  return environment.toUpperCase();
}
