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

const DEFAULT_BASE_URL =
  (import.meta.env.VITE_API_BASE_URL as string | undefined)?.trim() ||
  (import.meta.env.DEV ? computeDevDefault() : "https://api.thynact.com");

export function getApiBaseUrl(): string {
  try {
    return sessionStorage.getItem(BASE_URL_KEY) || DEFAULT_BASE_URL;
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
