// Runtime API configuration. The API key is kept in sessionStorage only
// (cleared when the tab closes) so it never lingers like localStorage would.
const BASE_URL_KEY = "agent-os:api-base-url";
const API_KEY_KEY = "agent-os:api-key";

function computeDevDefault(): string {
  if (typeof window === "undefined") return "http://localhost:8000";
  const { protocol, hostname } = window.location;
  // Replit maps the backend's port to the bare https domain (no port suffix);
  // outside Replit, the backend runs on port 8000 alongside the Vite dev server.
  if (hostname.endsWith(".replit.dev")) return `${protocol}//${hostname}`;
  return `${protocol}//${hostname}:8000`;
}

/**
 * Which backend a deployed frontend talks to, derived from the hostname it is
 * actually served from.
 *
 * This is deliberately NOT a single hardcoded production URL. Cloudflare Pages
 * serves the production branch, the staging branch and every feature-branch
 * preview from the same build pipeline, so a fixed `https://api.thynact.com`
 * default meant staging.thynact.com and every *.pages.dev preview pointed at
 * the PRODUCTION API — production data reachable from any preview build.
 * Deriving the host makes isolation fail-safe rather than dependent on someone
 * remembering to set VITE_API_BASE_URL on the right Pages environment.
 *
 * VITE_API_BASE_URL still overrides this when set at build time.
 */
// Cloudflare Pages serves the production deployment on BOTH the custom domain
// and the project's bare pages.dev alias (verified: both return the same asset
// hash). Preview deployments are always a SUBDOMAIN of that alias, so the bare
// host is production and anything in front of it is not.
const PRODUCTION_HOSTS = new Set(["app.thynact.com", "agent-os-test.pages.dev"]);

export function computeApiBaseUrl(hostname: string): string {
  if (PRODUCTION_HOSTS.has(hostname)) return "https://api.thynact.com";
  if (hostname === "staging.thynact.com") return "https://api-staging.thynact.com";
  // Feature-branch previews (<hash>.<project>.pages.dev) must never reach
  // production; route them at staging, which holds no production data.
  if (hostname.endsWith(".pages.dev")) return "https://api-staging.thynact.com";
  // Unknown host: fall back to staging rather than production, so a
  // misconfigured or unexpected domain cannot silently mutate production.
  return "https://api-staging.thynact.com";
}

function computeDefaultBaseUrl(): string {
  const configured = (import.meta.env.VITE_API_BASE_URL as string | undefined)?.trim();
  if (configured) return configured;
  if (import.meta.env.DEV) return computeDevDefault();
  if (typeof window === "undefined") return "https://api.thynact.com";
  return computeApiBaseUrl(window.location.hostname);
}

const DEFAULT_BASE_URL = computeDefaultBaseUrl();

/**
 * A stored override is only honoured if it could actually work from this page.
 *
 * The stored value used to win unconditionally, so a base URL left over from a
 * local dev session (http://localhost:8000) kept overriding the correct
 * production default in that browser session — every request then failed as a
 * network error and the app showed "Can't reach the API" forever, with no clue
 * that a stale setting was the cause. An http:// or loopback target is
 * unreachable from an https:// page (mixed content is blocked outright), so
 * treat it as unusable rather than obeying it.
 */
function isUsableOverride(url: string): boolean {
  if (typeof window === "undefined") return true;
  if (window.location.protocol !== "https:") return true; // local dev: anything goes
  try {
    const parsed = new URL(url);
    if (parsed.protocol !== "https:") return false;
    return !["localhost", "127.0.0.1", "::1", "0.0.0.0"].includes(parsed.hostname);
  } catch {
    return false; // unparseable — fall back to the computed default
  }
}

export function getApiBaseUrl(): string {
  try {
    const stored = sessionStorage.getItem(BASE_URL_KEY);
    if (stored && isUsableOverride(stored)) return stored;
    return DEFAULT_BASE_URL;
  } catch {
    return DEFAULT_BASE_URL;
  }
}

export function setApiBaseUrl(url: string): void {
  try {
    sessionStorage.setItem(BASE_URL_KEY, url);
  } catch {
    /* sessionStorage unavailable (private mode) — config resets on reload */
  }
}

export function getApiKey(): string {
  try {
    return sessionStorage.getItem(API_KEY_KEY) || "";
  } catch {
    return "";
  }
}

export function setApiKey(key: string): void {
  try {
    if (key) sessionStorage.setItem(API_KEY_KEY, key);
    else sessionStorage.removeItem(API_KEY_KEY);
  } catch {
    /* sessionStorage unavailable */
  }
}

export function isApiConfigured(): boolean {
  return Boolean(getApiKey());
}

export function resetApiConfig(): void {
  setApiBaseUrl(DEFAULT_BASE_URL);
  setApiKey("");
}

export { DEFAULT_BASE_URL };
